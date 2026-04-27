import L from "leaflet";
import "leaflet.markercluster";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import { MAP_CENTER, MAP_ZOOM } from "./leafletConstants.js";
import {
    createTileLayer,
    setupLabelPane,
    fetchSingleCountryWithTerritories,
    fetchCountryBoundaries,
    isGermany,
    createColorScale,
    getFeatureStyle,
    createPopupContent,
    isPointInPolygon,
    normalizeCountryName,
} from "./leafletUtils.js";
import {
    normalizeLocations,
    getCoordinates,
    createMarkerWithPopup,
    createMarkerClusterGroup,
} from "./leafletMarkers.js";
import { renderProvinceLayer, renderGermanyProvinces } from "./leafletProvinces.js";

// Composable
export const useLeafletChart = (options = {}) => {
    // State
    let map = null;
    let mapContainer = null;
    let countriesData = null;
    let geoJsonLayer = null;
    let layerControl = null;
    let competitorClusterGroup = null;
    let sellerClusterGroup = null;
    let customerClusterGroup = null;
    let popupTimeout = null;
    const {
        onCountryClick,
        onCountryHover,
        onMarkerClick,
        onProvinceClick,
        isPopup = false,
        isLCC = false,
        showCountryOutlines = true,
    } = options;

    const getIsLCC = typeof isLCC === "function" ? isLCC : () => isLCC;
    const getShowCountryOutlines =
        typeof showCountryOutlines === "function"
            ? showCountryOutlines
            : () => showCountryOutlines;

    const toArray = (value) => {
        if (!value) return [];
        return Array.isArray(value) ? value.filter(Boolean) : [value];
    };

    const getCustomers = (data) => {
        const source = data?.customer ?? data?.customers ?? data?.buyers ?? data?.buyer ?? null;
        return toArray(source).map((item) => ({
            ...item,
            customer_id:
                item?.customer_id ??
                item?.buyer_id ??
                item?.id ??
                item?.customerId ??
                item?.buyerId ??
                null,
            customer_name:
                item?.customer_name ?? item?.buyer_name ?? item?.name ?? item?.label ?? null,
        }));
    };

    const buildLocations = (data) => ({
        competitors: toArray(data?.competitors),
        customers: getCustomers(data),
        seller: data?.seller ?? null,
    });

    const initMap = (container) => {
        if (!container) return;
        mapContainer = container;

        map = L.map(container, {
            zoomControl: false,
        }).setView(MAP_CENTER, MAP_ZOOM);

        setupLabelPane(map);

        const originalOnPanTransitionEnd = map._onPanTransitionEnd;
        if (originalOnPanTransitionEnd) {
            map._onPanTransitionEnd = function () {
                if (this._mapPane && this._mapPane.classList) {
                    originalOnPanTransitionEnd.call(this);
                }
            };
        }

        createTileLayer(
            "https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_nolabels/{z}/{x}/{y}.png"
        ).addTo(map);

        createTileLayer(
            "https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_only_labels/{z}/{x}/{y}.png",
            { pane: "labels" }
        ).addTo(map);
    };

    const renderCountryOutlines = async () => {
        if (!map || !countriesData?.length) return;

        if (geoJsonLayer) {
            map.removeLayer(geoJsonLayer);
            geoJsonLayer = null;
        }

        const countryNames = countriesData.map((country) => country.country_name);
        const featuresToRender = await fetchCountryBoundaries(countryNames, countriesData);

        if (featuresToRender.length === 0 || !map) return;

        const colorScale = createColorScale(countriesData);

        geoJsonLayer = L.geoJSON(featuresToRender, {
            style: (feature) => getFeatureStyle(feature, colorScale),
            onEachFeature: (feature, layer) => {
                const handleCountryClick = () => {
                    if (onCountryClick && feature.countryData) {
                        onCountryClick(feature.countryData);
                    }
                };

                const clearPopupTimeout = () => {
                    if (popupTimeout) {
                        clearTimeout(popupTimeout);
                        popupTimeout = null;
                    }
                };

                const resetStyle = (targetLayer) => {
                    targetLayer.setStyle({
                        weight: 0.6,
                        opacity: 1,
                        fillOpacity: 0.1,
                    });
                };

                const scheduleClose = (targetLayer) => {
                    clearPopupTimeout();
                    popupTimeout = setTimeout(() => {
                        const popupElement = document.querySelector(".leaflet-popup");
                        if (popupElement && !popupElement.matches(":hover")) {
                            resetStyle(targetLayer);
                            map.closePopup();
                        }
                    }, 150);
                };

                layer.on({
                    mouseover: (e) => {
                        clearPopupTimeout();
                        map.closePopup();

                        const layer = e.target;
                        layer.setStyle({
                            weight: 2,
                            opacity: 1,
                            fillOpacity: 0.9,
                        });
                        layer.bringToFront();

                        if (onCountryHover && feature.countryData) {
                            onCountryHover(feature.countryData);
                        }

                        L.popup()
                            .setLatLng(e.latlng)
                            .setContent(createPopupContent(feature))
                            .openOn(map);

                        setTimeout(() => {
                            const popupElement = document.querySelector(".leaflet-popup");
                            if (popupElement) {
                                popupElement.addEventListener("mouseenter", clearPopupTimeout);
                                popupElement.addEventListener("mouseleave", () =>
                                    scheduleClose(layer)
                                );
                            }
                        }, 50);
                    },
                    mouseout: (e) => {
                        resetStyle(e.target);
                        scheduleClose(e.target);

                        if (onCountryHover && feature.countryData) {
                            onCountryHover(null);
                        }
                    },
                    click: handleCountryClick,
                });
            },
        }).addTo(map);
    };

    const createClusterGroupForType = (validLocations) => {
        if (!validLocations || validLocations.length === 0) return null;

        const clusterGroup = createMarkerClusterGroup();
        if (!clusterGroup) return null;

        validLocations.forEach((location) => {
            const marker = createMarkerWithPopup(location, isPopup, onMarkerClick, getIsLCC());
            if (marker) {
                clusterGroup.addLayer(marker);
            }
        });
        return clusterGroup;
    };

    const clearAllMarkerGroups = () => {
        if (competitorClusterGroup) {
            map.removeLayer(competitorClusterGroup);
            competitorClusterGroup = null;
        }
        if (sellerClusterGroup) {
            map.removeLayer(sellerClusterGroup);
            sellerClusterGroup = null;
        }
        if (customerClusterGroup) {
            map.removeLayer(customerClusterGroup);
            customerClusterGroup = null;
        }
    };

    const fitMapToMarkerGroups = () => {
        if (!map) return;

        const groups = [competitorClusterGroup, sellerClusterGroup, customerClusterGroup].filter(
            Boolean
        );

        if (!groups.length) {
            return;
        }

        const markerBounds = L.featureGroup(groups).getBounds();

        if (!markerBounds.isValid()) {
            return;
        }

        map.fitBounds(markerBounds.pad(0.2), {
            padding: [40, 40],
            maxZoom: 6,
            animate: false,
        });
    };

    const clearAllGeoJsonLayers = () => {
        if (!map) return;

        if (geoJsonLayer) {
            try {
                if (geoJsonLayer.eachLayer) {
                    geoJsonLayer.eachLayer((layer) => {
                        try {
                            map.removeLayer(layer);
                        } catch (e) {
                            // Layer might already be removed
                        }
                    });
                }
                map.removeLayer(geoJsonLayer);
            } catch (e) {
                console.warn("Error removing geoJsonLayer:", e);
            }
            geoJsonLayer = null;
        }

        map.eachLayer((layer) => {
            if (
                !layer._url &&
                !layer._childClusters &&
                layer !== competitorClusterGroup &&
                layer !== sellerClusterGroup &&
                layer !== customerClusterGroup
            ) {
                try {
                    map.removeLayer(layer);
                } catch (e) {
                    // Ignore errors
                }
            }
        });
    };

    const renderMarkers = (locations, bounds = null, provinceFeature = null) => {
        if (!map || !locations) return;

        clearAllMarkerGroups();

        if (layerControl) {
            map.removeControl(layerControl);
            layerControl = null;
        }

        const hasStructured =
            locations && (locations.customers || locations.competitors || locations.seller);

        const typeConfig = [
            {
                key: "competitors",
                type: "competitor",
                clusterRef: "competitorClusterGroup",
                label: "Competitors",
            },
            {
                key: "customers",
                type: "customer",
                clusterRef: "customerClusterGroup",
                label: "Customers",
            },
            {
                key: "seller",
                type: "seller",
                clusterRef: "sellerClusterGroup",
                label: "Sellers",
            },
        ];

        typeConfig.forEach(({ key, type, clusterRef }) => {
            const normalized = hasStructured
                ? normalizeLocations(locations[key], type)
                : Array.isArray(locations)
                  ? locations
                  : [];

            const valid = normalized.filter((loc) => {
                const { lng, lat } = getCoordinates(loc);
                if (lng == null || lat == null || !isFinite(+lng) || !isFinite(+lat)) {
                    return false;
                }
                if (provinceFeature) {
                    return isPointInPolygon({ lat: +lat, lng: +lng }, provinceFeature);
                }
                if (bounds) {
                    const point = L.latLng(+lat, +lng);
                    return bounds.contains(point);
                }
                return true;
            });

            const clusterGroup = createClusterGroupForType(valid);
            if (clusterGroup) {
                if (clusterRef === "competitorClusterGroup") {
                    competitorClusterGroup = clusterGroup;
                } else if (clusterRef === "customerClusterGroup") {
                    customerClusterGroup = clusterGroup;
                } else if (clusterRef === "sellerClusterGroup") {
                    sellerClusterGroup = clusterGroup;
                }
                if (map && map._container && map._container.parentNode) {
                    clusterGroup.addTo(map);
                }
            }
        });
    };

    const setCountriesData = async (data) => {
        countriesData = data;

        clearAllGeoJsonLayers();

        if (getShowCountryOutlines()) {
            await renderCountryOutlines();
        }

        const locations = {
            competitors: [],
            customers: data.flatMap((country) => getCustomers(country)),
            seller: data.map((country) => country?.seller).filter(Boolean),
        };

        renderMarkers(locations);
        fitMapToMarkerGroups();
    };

    const renderGermanyCountryBorder = async () => {
        if (!map || !map._container || !map._container.parentNode) return null;

        const countryResult = await fetchSingleCountryWithTerritories("Germany");
        if (!countryResult || !countryResult.allTerritoriesFeature) {
            if (!countryResult) {
                console.warn(`Failed to fetch Germany country border`);
            }
            return null;
        }

        if (!map || !map._container || !map._container.parentNode) return null;

        return L.geoJSON([countryResult.allTerritoriesFeature], {
            style: {
                fill: true,
                fillColor: "#cfd5db",
                fillOpacity: 0.2,
                weight: 1.5,
                opacity: 1,
                color: "#000000",
                dashArray: "3",
            },
        });
    };

    const setSingleProvince = async (countryName, provinceName, countryData = null) => {
        if (!map || !isGermany(countryName)) return;

        clearAllGeoJsonLayers();
        clearAllMarkerGroups();

        if (layerControl) {
            map.removeControl(layerControl);
            layerControl = null;
        }

        map.setMaxBounds(null);
        map.setMinZoom(0);

        const countryBorderLayer = await renderGermanyCountryBorder();
        if (!countryBorderLayer) return;

        const result = await renderProvinceLayer(map, provinceName, null, false);
        if (!result || !map) return;

        if (!map._container || !map._container.parentNode) return;

        map.removeLayer(result.geoJsonLayer);

        geoJsonLayer = L.layerGroup([countryBorderLayer, result.geoJsonLayer]);
        geoJsonLayer.addTo(map);

        const selectedProvince = result.selectedProvince;

        const bounds = L.geoJSON(selectedProvince).getBounds();
        const paddedBounds = bounds.pad(0.2);
        map.setMaxBounds(paddedBounds);

        map.fitBounds(bounds, {
            padding: [50, 50],
            maxZoom: 10,
            animate: false,
        });

        const calculatedZoom = map.getZoom();
        map.setZoom(Math.max(calculatedZoom - 0.5, 5), { animate: false });
        map.setMinZoom(Math.max(0, map.getZoom()));

        if (countryData) {
            const dataCountryName =
                countryData.country_name || countryData.country?.[0]?.country_name;
            const normalizedDataName = normalizeCountryName(dataCountryName);
            const normalizedTargetName = normalizeCountryName(countryName);

            if (
                normalizedDataName &&
                normalizedTargetName &&
                normalizedDataName !== normalizedTargetName
            ) {
                return;
            }

            const locations = buildLocations(countryData);
            renderMarkers(locations, null, selectedProvince);
        }
    };

    const setSingleCountry = async (countryName, countryData = null) => {
        if (!map) return;

        clearAllGeoJsonLayers();
        clearAllMarkerGroups();

        if (layerControl) {
            map.removeControl(layerControl);
            layerControl = null;
        }

        map.setMaxBounds(null);
        map.setMinZoom(0);

        const germanyMode = isGermany(countryName);

        let bounds = null;

        if (germanyMode) {
            const countryBorderLayer = await renderGermanyCountryBorder();
            if (!countryBorderLayer) return;

            const provincesResult = await renderGermanyProvinces(map, onProvinceClick);
            if (!provincesResult || !map || !map._container || !map._container.parentNode) return;

            map.removeLayer(provincesResult.geoJsonLayer);

            geoJsonLayer = L.layerGroup([countryBorderLayer, provincesResult.geoJsonLayer]);
            geoJsonLayer.addTo(map);

            bounds = provincesResult.bounds;
        } else {
            const result = await fetchSingleCountryWithTerritories(countryName);
            if (
                !result ||
                !result.mainlandFeature ||
                !result.allTerritoriesFeature ||
                !map ||
                !map._container ||
                !map._container.parentNode
            ) {
                if (!result) {
                    console.warn(`Country not found: ${countryName}`);
                }
                return;
            }

            const { mainlandFeature, allTerritoriesFeature } = result;

            const tempLayer = L.geoJSON(mainlandFeature);
            bounds = tempLayer.getBounds();

            const enrichedFeature = {
                ...allTerritoriesFeature,
                countryData: countryData,
            };

            if (geoJsonLayer) {
                try {
                    map.removeLayer(geoJsonLayer);
                } catch (e) {
                    // Ignore if already removed
                }
                geoJsonLayer = null;
            }

            if (!map || !map._container || !map._container.parentNode) return;

            geoJsonLayer = L.geoJSON([enrichedFeature], {
                style: {
                    fill: true,
                    fillColor: "#cfd5db",
                    fillOpacity: 0.2,
                    weight: 1.5,
                    opacity: 1,
                    color: "#000000",
                    dashArray: "3",
                },
            }).addTo(map);
        }

        if (!bounds || !map) return;

        if (!map._container || !map._container.parentNode) return;

        let allLayersBounds = bounds;
        if (geoJsonLayer) {
            try {
                allLayersBounds = geoJsonLayer.getBounds();
            } catch (e) {
                allLayersBounds = bounds;
            }
        }

        const paddedBounds = allLayersBounds.pad(0.5);
        map.setMaxBounds(paddedBounds);

        const boundsSize = bounds.getNorthEast().distanceTo(bounds.getSouthWest());
        const padding =
            boundsSize > 2000000 ? [80, 80] : boundsSize > 1000000 ? [60, 60] : [50, 50];

        map.fitBounds(bounds, {
            padding,
            maxZoom: 10,
            animate: false,
        });

        const calculatedZoom = map.getZoom();
        const adjustedZoom =
            boundsSize > 2000000 ? Math.max(calculatedZoom - 0.5, 3) : calculatedZoom;

        map.setZoom(adjustedZoom, { animate: false });

        const currentZoom = map.getZoom();
        map.setMinZoom(Math.max(0, currentZoom - 1));

        if (countryData) {
            const dataCountryName =
                countryData.country_name || countryData.country?.[0]?.country_name;
            const normalizedDataName = normalizeCountryName(dataCountryName);
            const normalizedTargetName = normalizeCountryName(countryName);

            if (
                normalizedDataName &&
                normalizedTargetName &&
                normalizedDataName !== normalizedTargetName
            ) {
                return;
            }

            const locations = buildLocations(countryData);
            renderMarkers(locations);
        }
    };

    const destroyMap = () => {
        if (popupTimeout) {
            clearTimeout(popupTimeout);
            popupTimeout = null;
        }

        if (layerControl) {
            map?.removeControl(layerControl);
            layerControl = null;
        }

        clearAllMarkerGroups();

        if (geoJsonLayer) {
            map?.removeLayer(geoJsonLayer);
            geoJsonLayer = null;
        }

        if (map) {
            try {
                if (map._panAnim) {
                    map._panAnim.stop();
                }

                map.stop();

                if (map._mapPane && map._mapPane.classList) {
                    try {
                        map._mapPane.classList.remove("leaflet-pan-anim");
                    } catch (e) {
                        // Ignore if already removed
                    }
                }

                map.off();
                map.closePopup();
                map.setMaxBounds(null);
                map.setMinZoom(0);
                map.remove();
            } catch (e) {
                console.warn("Error destroying map:", e);
            }
            map = null;
        }

        mapContainer = null;
        countriesData = null;
    };

    return {
        initMap,
        setCountriesData,
        setSingleCountry,
        setSingleProvince,
        destroyMap,
    };
};
