import L from "leaflet";
import { loadGermanyProvincesGeoJSON } from "./leafletUtils.js";
import { PROVINCE_HOVER_SELECTED_STYLE } from "./leafletConstants.js";

const normalizeProvinceName = (name) => {
    if (!name) return "";
    return name.toString().trim().toLowerCase().replace(/\s+/g, " ");
};

export const renderProvinceLayer = async (
    map,
    provinceName,
    onProvinceClick,
    isInteractive = true
) => {
    if (!map || !provinceName) return null;

    const provinces = await loadGermanyProvincesGeoJSON();

    if (!map || !map._container || !map._container.parentNode) {
        return null;
    }

    const allProvinces = Array.isArray(provinces.features) ? provinces.features : provinces;
    const normalizedTargetProvince = normalizeProvinceName(provinceName);

    const selectedProvince = allProvinces.find((feature) => {
        const props = feature.properties || {};
        const featureName = props.name || props.NAME || props.Name || props.gen || props.GEN || "";
        return normalizeProvinceName(featureName) === normalizedTargetProvince;
    });

    if (!selectedProvince) {
        console.warn(`Province not found: ${provinceName}`);
        return null;
    }

    const provinceBaseStyle = {
        fill: true,
        fillColor: "#dfe3e8",
        fillOpacity: 0.1,
        weight: 1,
        opacity: 0.5,
        color: "#b9c2cc",
    };

    const provinceSelectedStyle = PROVINCE_HOVER_SELECTED_STYLE;

    if (!map || !map._container || !map._container.parentNode) {
        return null;
    }

    const geoJsonLayer = L.geoJSON(allProvinces, {
        style: (feature) => {
            const props = feature.properties || {};
            const featureName =
                props.name || props.NAME || props.Name || props.gen || props.GEN || "";
            const isSelected = normalizeProvinceName(featureName) === normalizedTargetProvince;
            return isSelected ? provinceSelectedStyle : provinceBaseStyle;
        },
        onEachFeature: (feature, layer) => {
            layer.options.interactive = isInteractive;

            if (isInteractive && onProvinceClick) {
                layer.on({
                    mouseover: () => {
                        layer.setStyle(PROVINCE_HOVER_SELECTED_STYLE);
                        if (layer.bringToFront) layer.bringToFront();
                    },
                    mouseout: () => {
                        layer.setStyle(provinceBaseStyle);
                    },
                    click: (e) => {
                        L.DomEvent.stopPropagation(e);
                        L.DomEvent.preventDefault(e);
                        if (feature.properties) {
                            const provinceName =
                                feature.properties.name ||
                                feature.properties.NAME ||
                                feature.properties.Name ||
                                feature.properties.gen ||
                                feature.properties.GEN;
                            if (provinceName) {
                                onProvinceClick({
                                    provinceName: provinceName,
                                    properties: feature.properties,
                                });
                            }
                        }
                    },
                });
            }
        },
    });

    if (!map || !map._container || !map._container.parentNode) {
        return null;
    }

    geoJsonLayer.addTo(map);

    return { geoJsonLayer, selectedProvince };
};

export const renderGermanyProvinces = async (map, onProvinceClick) => {
    if (!map) return null;

    const provinces = await loadGermanyProvincesGeoJSON();

    if (!map || !map._container || !map._container.parentNode) {
        return null;
    }

    const tempLayer = L.geoJSON(provinces);
    const bounds = tempLayer.getBounds();

    const provinceBaseStyle = {
        fill: true,
        fillColor: "#dfe3e8",
        fillOpacity: 0.2,
        weight: 1,
        opacity: 1,
        color: "#b9c2cc",
    };

    const provinceHoverStyle = PROVINCE_HOVER_SELECTED_STYLE;

    if (!map || !map._container || !map._container.parentNode) {
        return null;
    }

    const geoJsonLayer = L.geoJSON(provinces, {
        style: provinceBaseStyle,
        onEachFeature: (feature, layer) => {
            layer.options.interactive = true;

            layer.on({
                mouseover: () => {
                    layer.setStyle(provinceHoverStyle);
                    if (layer.bringToFront) layer.bringToFront();
                },
                mouseout: () => {
                    layer.setStyle(provinceBaseStyle);
                },
                click: (e) => {
                    L.DomEvent.stopPropagation(e);
                    L.DomEvent.preventDefault(e);
                    if (onProvinceClick && feature.properties) {
                        const provinceName =
                            feature.properties.name ||
                            feature.properties.NAME ||
                            feature.properties.Name ||
                            feature.properties.gen ||
                            feature.properties.GEN;
                        if (provinceName) {
                            onProvinceClick({
                                provinceName: provinceName,
                                properties: feature.properties,
                            });
                        }
                    }
                },
            });
        },
    });

    if (!map || !map._container || !map._container.parentNode) {
        return null;
    }

    geoJsonLayer.addTo(map);

    return { geoJsonLayer, bounds };
};
