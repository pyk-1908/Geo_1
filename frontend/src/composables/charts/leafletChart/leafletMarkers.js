import L from "leaflet";
import { COLOR_BY_TYPE } from "./leafletConstants.js";

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

export const createMarkerIcon = (location) => {
    const color = COLOR_BY_TYPE[location.type] || "#7C3AED";
    const iconSize = 20;
    const iconHeight = 10;

    return L.divIcon({
        className: "custom-marker",
        html: `<div style="
            width: ${iconSize}px;
            height: ${iconHeight}px;
            background: ${color};
            border: 1px solid #E3E2E0;
            border-radius: 10px;
            position: relative;
        ">
            <span style="
                position: absolute;
                top: -10%;
                left: 50%;
                transform: translate(-50%, -100%);
                font-size: 10px;
                font-weight: 400;
                color: #2a2a2a;
                white-space: nowrap;
                pointer-events: none;
            ">${location.city_name || ""}</span>
        </div>`,
        iconSize: [iconSize, iconHeight],
        iconAnchor: [iconSize / 2, iconHeight / 2],
    });
};

export const createMarkerWithPopup = (location, isPopup, onMarkerClick, isLCC = false) => {
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

    const popupContent = closestList.length
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

    const popup = L.popup({
        autoPan: true,
        autoPanPadding: [50, 50],
        keepInView: true,
    }).setContent(popupContent);
    marker.bindPopup(popup);

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
