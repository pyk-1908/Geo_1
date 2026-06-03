import L from "leaflet";
import { COLOR_BY_TYPE } from "./leafletConstants.js";

// Salesforce notes are external data, so escape before injecting into popup HTML.
const escapeHtml = (value) =>
    String(value ?? "").replace(
        /[&<>"']/g,
        (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[ch],
    );

const formatNoteDate = (value) => {
    if (!value) return "";
    const date = new Date(value);
    return isNaN(date.getTime()) ? "" : date.toLocaleDateString();
};

const renderNotesHtml = (notes) => {
    if (!notes || notes.length === 0) {
        return `<em style="color:#6b7280;">No Salesforce notes</em>`;
    }
    return notes
        .map((note) => {
            const date = formatNoteDate(note.created_date);
            return `<div style="margin-bottom:6px;padding-bottom:6px;border-bottom:1px solid #eee;">
                <div style="font-weight:600;">${escapeHtml(note.title) || "(untitled)"}</div>
                <div style="white-space:pre-wrap;">${escapeHtml(note.body)}</div>
                ${date ? `<div style="color:#6b7280;font-size:11px;">${date}</div>` : ""}
            </div>`;
        })
        .join("");
};

export const normalizeLocations = (input, type) => {
    const out = [];
    if (!input) return out;
    const arr = Array.isArray(input) ? input : [input];
    for (const item of arr) {
        if (item && Array.isArray(item.locations)) {
            for (const loc of item.locations) {
                out.push({
                    ...loc,
                    ...item,
                    type,
                    icon_name: item.icon_name ?? loc.icon_name,
                    _entity_name:
                        item.customer_name || item.competitor_name || item.seller_name || null,
                });
            }
        } else {
            out.push({ ...item, type });
        }
    }
    return out;
};

export const getCoordinates = (location) => {
    const lng =
        location.lng ??
        location.lon ??
        location.long ??
        location.longitude ??
        location.lng_coordinate;
    const lat = location.lat ?? location.latitude ?? location.lat_coordinate;
    return { lng, lat };
};

// Inject the marker stylesheet once (hover/transition can't be done with inline styles).
let markerStylesInjected = false;
const ensureMarkerStyles = () => {
    if (markerStylesInjected || typeof document === "undefined") return;
    markerStylesInjected = true;
    const style = document.createElement("style");
    style.id = "si-marker-styles";
    style.textContent = `
        .si-marker { width: 16px; height: 16px; }
        .si-marker__dot {
            width: 16px; height: 16px; border-radius: 50%;
            border: 2px solid #ffffff; box-sizing: border-box;
            box-shadow: 0 1px 4px rgba(16,24,40,.35);
            transition: transform .15s ease, box-shadow .15s ease;
        }
        .si-marker:hover { z-index: 1000 !important; }
        .si-marker:hover .si-marker__dot {
            transform: scale(1.35);
            box-shadow: 0 3px 10px rgba(16,24,40,.45);
        }
        .si-marker__label {
            position: absolute; left: 50%; bottom: calc(100% + 6px);
            transform: translateX(-50%);
            background: #ffffff; color: #1f2937;
            font-size: 11px; font-weight: 600; line-height: 1;
            padding: 4px 7px; border-radius: 7px; white-space: nowrap;
            pointer-events: none; border: 1px solid #ECEBEA;
            box-shadow: 0 2px 6px rgba(16,24,40,.18);
        }
        .si-marker__label::after {
            content: ""; position: absolute; top: 100%; left: 50%;
            transform: translateX(-50%);
            border: 4px solid transparent; border-top-color: #ffffff;
        }
    `;
    document.head.appendChild(style);
};

export const createMarkerIcon = (location) => {
    ensureMarkerStyles();
    const color = COLOR_BY_TYPE[location.type] || "#7C3AED";
    const label = location.city_name
        ? `<div class="si-marker__label">${escapeHtml(location.city_name)}</div>`
        : "";

    return L.divIcon({
        className: "custom-marker si-marker",
        html: `<div class="si-marker__dot" style="background:${color};"></div>${label}`,
        iconSize: [16, 16],
        iconAnchor: [8, 8],
    });
};

export const createMarkerWithPopup = (location, isPopup, onMarkerClick, isLCC = false, loadNotes = null) => {
    const { lng, lat } = getCoordinates(location);
    if (lng == null || lat == null || !isFinite(+lng) || !isFinite(+lat)) {
        return null;
    }

    const marker = L.marker([+lat, +lng], {
        icon: createMarkerIcon(location),
    });

    const isCompetitor =
        location.type === "competitor" && location.competitor_id && location.competitor_name;
    const isCustomer = location.type === "customer";

    // Buyers (normalized to type "customer") may carry a Salesforce Account Id;
    // if so, fetch and show that account's notes inside the popup.
    const accountId = location.salesforce_account_id;
    const showNotes = isCustomer && !!accountId && !isPopup && typeof loadNotes === "function";

    const hasMarkerClickHandler = onMarkerClick && typeof onMarkerClick === "function";
    const shouldUseStaticStyle = isPopup || !hasMarkerClickHandler || isLCC;
    const competitorNameHtml = isCompetitor
        ? shouldUseStaticStyle
            ? `<span class="popup__competitor popup__competitor--static">${location.competitor_name}</span>`
            : `<span class="popup__competitor popup__competitor--link competitor-link">${location.competitor_name}</span>`
        : location._entity_name || "";

    const closestList =
        isCustomer && Array.isArray(location.closest_to_customer)
            ? [...location.closest_to_customer].filter((c) => c && c.competitor_name)
            : [];

    let popupContent = closestList.length
        ? `
            <div class="popup popup--customer">
                <div class="popup__header">
                    Closest to
                    <span class="popup__customer-name">
                        ${location.customer_name || "Customer"}
                    </span>
                </div>
                <ul class="popup__list">
                    ${closestList
                        .sort((a, b) => {
                            const da = isFinite(+a.distance_abs) ? +a.distance_abs : Infinity;
                            const db = isFinite(+b.distance_abs) ? +b.distance_abs : Infinity;
                            return da - db;
                        })
                        .map((c) => {
                            const distance =
                                c.distance_abs != null && isFinite(+c.distance_abs)
                                    ? `${Math.round(+c.distance_abs)} km`
                                    : "—";
                            return `<li class="popup__list-item">${c.competitor_name} - ${distance}</li>`;
                        })
                        .join("")}
                </ul>
            </div>
        `
        : `
            <div class="popup popup--default">
                <strong>${location.city_name || "Unknown"}</strong><br>
                ${competitorNameHtml ? `${competitorNameHtml}<br>` : ""}
                ${location.state_name ? `${location.state_name}` : ""}
            </div>
        `;

    if (showNotes) {
        popupContent += `
            <div class="popup__notes" style="margin-top:8px;padding-top:8px;border-top:1px solid #ddd;max-width:260px;">
                <div style="font-weight:600;margin-bottom:4px;">Salesforce notes</div>
                <div class="popup__notes-body" style="max-height:160px;overflow:auto;">Loading…</div>
            </div>`;
    }

    const popup = L.popup({
        autoPan: true,
        autoPanPadding: [50, 50],
        keepInView: true,
    }).setContent(popupContent);
    marker.bindPopup(popup);

    if (showNotes) {
        marker.on("popupopen", () => {
            // Defer so the popup DOM is attached before we query it. Leaflet resets the
            // popup content to the original HTML on every open, so we must re-render into
            // the fresh body each time; we cache the fetched DATA so we only hit the API once.
            setTimeout(async () => {
                // Render into the live popup body. We must NOT call popup.update() —
                // Leaflet rebuilds the popup HTML from the original string on update,
                // which would wipe the notes back to "Loading...". Re-query each time
                // so we always write into the current node.
                const renderInto = (html) => {
                    const el = marker.getPopup()?.getElement()?.querySelector(".popup__notes-body");
                    if (el) el.innerHTML = html;
                };

                if (marker._sfNotes !== undefined) {
                    renderInto(renderNotesHtml(marker._sfNotes));
                    return;
                }
                try {
                    const resp = await loadNotes(accountId);
                    if (resp && resp.unauthorized) {
                        renderInto(`<em style="color:#b91c1c;">Session expired — refresh and log in again.</em>`);
                    } else if (resp && resp.success === false) {
                        renderInto(`<em style="color:#b91c1c;">Couldn't load notes.</em>`);
                    } else {
                        const notes = Array.isArray(resp && resp.notes) ? resp.notes : [];
                        marker._sfNotes = notes;
                        renderInto(renderNotesHtml(notes));
                    }
                } catch (error) {
                    renderInto(`<em style="color:#b91c1c;">Couldn't load notes.</em>`);
                }
            }, 0);
        });
    }

    if (isCompetitor && onMarkerClick && !isPopup) {
        marker.on("popupopen", () => {
            setTimeout(() => {
                try {
                    const popup = marker.getPopup();
                    if (!popup) return;

                    const popupElement = popup.getElement();
                    if (!popupElement) return;

                    const competitorLink = popupElement.querySelector(".competitor-link");
                    if (competitorLink && competitorLink.nodeType === 1) {
                        const handleCompetitorClick = (e) => {
                            e.stopPropagation();
                            e.preventDefault();
                            if (onMarkerClick) {
                                const { lng, lat } = getCoordinates(location);
                                onMarkerClick({
                                    competitor_id: location.competitor_id,
                                    competitor_name: location.competitor_name,
                                    lat: lat,
                                    lng: lng,
                                    city_name: location.city_name,
                                    ...location,
                                });
                            }
                        };
                        competitorLink.addEventListener("click", handleCompetitorClick);
                        competitorLink._clickHandler = handleCompetitorClick;
                    }
                } catch (error) {
                    console.warn("Error setting up competitor link click handler:", error);
                }
            }, 0);
        });

        marker.on("popupclose", () => {
            const popup = marker.getPopup();
            if (!popup) return;

            const popupElement = popup.getElement();
            if (!popupElement) return;

            const competitorLink = popupElement.querySelector(".competitor-link");
            if (competitorLink && competitorLink._clickHandler) {
                competitorLink.removeEventListener("click", competitorLink._clickHandler);
                competitorLink._clickHandler = null;
            }
        });
    }

    return marker;
};

export const createMarkerClusterGroup = () => {
    if (!L.markerClusterGroup || typeof L.markerClusterGroup !== "function") {
        return null;
    }
    return L.markerClusterGroup({
        maxClusterRadius: 50,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true,
    });
};
