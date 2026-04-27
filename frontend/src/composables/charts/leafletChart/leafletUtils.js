import L from "leaflet";
import { feature as topojsonFeature } from "topojson-client";
import * as d3 from "d3";
import { WORLD_URL, GERMANY_PROVINCES_URL, nodataColor, ATTRIBUTION } from "./leafletConstants.js";
import { COUNTRY_NAME_ALIASES } from "@utils/utils";

// Module-level cache
let worldAtlasCache = null;
let germanyProvincesCache = null;

// Data loading utilities
export const loadWorldAtlasGeoJSON = async () => {
    if (worldAtlasCache) return worldAtlasCache;

    try {
        const res = await fetch(WORLD_URL);
        if (!res.ok) throw new Error(`Failed to load world atlas: ${res.status}`);
        const topojson = await res.json();
        const features = topojsonFeature(topojson, topojson.objects.countries).features;
        worldAtlasCache = features;
        return features;
    } catch (error) {
        console.error("Error loading world atlas:", error);
        throw error;
    }
};

export const loadGermanyProvincesGeoJSON = async () => {
    if (germanyProvincesCache) return germanyProvincesCache;

    const res = await fetch(GERMANY_PROVINCES_URL);
    if (!res.ok) throw new Error(`Failed to load Germany provinces: ${res.status}`);
    const data = await res.json();

    germanyProvincesCache = Array.isArray(data.features)
        ? { type: "FeatureCollection", features: data.features }
        : data;

    return germanyProvincesCache;
};

// Geometry utilities
export const extractMainlandPolygon = (feature) => {
    if (!feature || !feature.geometry) return feature;

    if (feature.geometry.type === "Polygon") {
        return feature;
    }

    if (feature.geometry.type === "MultiPolygon") {
        const polygons = feature.geometry.coordinates;
        let largestPolygon = null;
        let largestArea = 0;

        polygons.forEach((polygonCoords) => {
            const tempPolygon = {
                type: "Feature",
                geometry: {
                    type: "Polygon",
                    coordinates: polygonCoords,
                },
            };

            const tempLayer = L.geoJSON(tempPolygon);
            const bounds = tempLayer.getBounds();

            const latCenter = (bounds.getNorth() + bounds.getSouth()) / 2;
            const latScale = Math.cos((latCenter * Math.PI) / 180);
            const width = (bounds.getEast() - bounds.getWest()) * latScale;
            const height = bounds.getNorth() - bounds.getSouth();
            const approximateArea = width * height;

            if (approximateArea > largestArea) {
                largestArea = approximateArea;
                largestPolygon = polygonCoords;
            }
        });

        if (largestPolygon) {
            return {
                ...feature,
                geometry: {
                    type: "Polygon",
                    coordinates: largestPolygon,
                },
            };
        }
    }

    return feature;
};

export const extractMainlandAndTerritories = (feature) => {
    if (!feature || !feature.geometry) {
        return {
            mainlandFeature: feature,
            allTerritoriesFeature: feature,
        };
    }

    if (feature.geometry.type === "Polygon") {
        return {
            mainlandFeature: feature,
            allTerritoriesFeature: feature,
        };
    }

    if (feature.geometry.type === "MultiPolygon") {
        const polygons = feature.geometry.coordinates;
        let largestPolygon = null;
        let largestArea = 0;

        polygons.forEach((polygonCoords) => {
            const tempPolygon = {
                type: "Feature",
                geometry: {
                    type: "Polygon",
                    coordinates: polygonCoords,
                },
            };

            const tempLayer = L.geoJSON(tempPolygon);
            const bounds = tempLayer.getBounds();

            const latCenter = (bounds.getNorth() + bounds.getSouth()) / 2;
            const latScale = Math.cos((latCenter * Math.PI) / 180);
            const width = (bounds.getEast() - bounds.getWest()) * latScale;
            const height = bounds.getNorth() - bounds.getSouth();
            const approximateArea = width * height;

            if (approximateArea > largestArea) {
                largestArea = approximateArea;
                largestPolygon = polygonCoords;
            }
        });

        const mainlandFeature = largestPolygon
            ? {
                  ...feature,
                  geometry: {
                      type: "Polygon",
                      coordinates: largestPolygon,
                  },
              }
            : feature;

        return {
            mainlandFeature,
            allTerritoriesFeature: feature,
        };
    }

    return {
        mainlandFeature: feature,
        allTerritoriesFeature: feature,
    };
};

const normalizeName = (name) => {
    if (!name) return "";
    return name
        .toString()
        .trim()
        .toLowerCase()
        .replace(/[\s\/]+/g, " ")
        .replace(/\band\b/g, " ")
        .replace(/\./g, "")
        .replace(/\s+/g, " ")
        .trim();
};

export const normalizeCountryName = normalizeName;

export const resolveCountryInput = (countryInput) => {
    if (!countryInput) return { decoded: "", normalized: "" };

    let decoded;
    try {
        decoded = decodeURIComponent(countryInput.toString());
    } catch (e) {
        decoded = countryInput.toString();
    }

    const aliasResolved = COUNTRY_NAME_ALIASES.get(decoded.trim()) ?? decoded;
    const normalized = normalizeName(aliasResolved);
    return { decoded: aliasResolved, normalized };
};

const namesMatch = (name1, name2) => {
    if (name1 === name2) return true;

    const words1 = name1.split(/\s+/).filter(Boolean);
    const words2 = name2.split(/\s+/).filter(Boolean);

    if (words1.length !== words2.length) {
        return false;
    }

    for (let i = 0; i < words1.length; i++) {
        const w1 = words1[i];
        const w2 = words2[i];
        if (w1 !== w2 && !w1.startsWith(w2) && !w2.startsWith(w1)) {
            return false;
        }
    }
    return true;
};

export const fetchSingleCountry = async (countryName) => {
    if (!countryName) return null;

    const { decoded: decodedName, normalized: normalizedSearchName } =
        resolveCountryInput(countryName);
    const allFeatures = await loadWorldAtlasGeoJSON();

    let feature = allFeatures.find((feature) => {
        const featureName = feature.properties?.name;
        if (!featureName) return false;
        const normalizedFeatureName = normalizeName(featureName);
        if (normalizedFeatureName === normalizedSearchName) {
            return true;
        }
        const searchWords = normalizedSearchName.split(/\s+/).filter(Boolean);
        const featureWords = normalizedFeatureName.split(/\s+/).filter(Boolean);
        if (searchWords.length === featureWords.length) {
            return namesMatch(normalizedSearchName, normalizedFeatureName);
        }
        return false;
    });

    if (!feature && normalizedSearchName.length >= 5) {
        const searchWords = normalizedSearchName.split(/\s+/).filter(Boolean);
        feature = allFeatures.find((feature) => {
            const featureName = feature.properties?.name;
            if (!featureName) return false;
            const normalizedFeatureName = normalizeName(featureName);
            const featureWords = normalizedFeatureName.split(/\s+/).filter(Boolean);
            if (searchWords.length === featureWords.length) {
                return namesMatch(normalizedSearchName, normalizedFeatureName);
            }
            return false;
        });
    }

    if (!feature) {
        console.warn(`Country not found in world atlas: ${decodedName}`);
        return null;
    }

    return extractMainlandPolygon(feature);
};

export const fetchSingleCountryWithTerritories = async (countryName) => {
    if (!countryName) return null;

    const { decoded: decodedName, normalized: normalizedSearchName } =
        resolveCountryInput(countryName);
    const allFeatures = await loadWorldAtlasGeoJSON();

    let feature = allFeatures.find((feature) => {
        const featureName = feature.properties?.name;
        if (!featureName) return false;
        const normalizedFeatureName = normalizeName(featureName);
        if (normalizedFeatureName === normalizedSearchName) {
            return true;
        }
        const searchWords = normalizedSearchName.split(/\s+/).filter(Boolean);
        const featureWords = normalizedFeatureName.split(/\s+/).filter(Boolean);
        if (searchWords.length === featureWords.length) {
            return namesMatch(normalizedSearchName, normalizedFeatureName);
        }
        return false;
    });

    if (!feature && normalizedSearchName.length >= 5) {
        const searchWords = normalizedSearchName.split(/\s+/).filter(Boolean);
        feature = allFeatures.find((feature) => {
            const featureName = feature.properties?.name;
            if (!featureName) return false;
            const normalizedFeatureName = normalizeName(featureName);
            const featureWords = normalizedFeatureName.split(/\s+/).filter(Boolean);
            if (searchWords.length === featureWords.length) {
                return namesMatch(normalizedSearchName, normalizedFeatureName);
            }
            return false;
        });
    }

    if (!feature) {
        console.warn(`Country not found in world atlas: ${decodedName}`);
        return null;
    }

    return extractMainlandAndTerritories(feature);
};

export const fetchCountryBoundaries = async (countryNames, countriesData) => {
    const allFeatures = await loadWorldAtlasGeoJSON();
    const normalizedSearchNames = new Set(countryNames.map((name) => normalizeName(name)));

    const dataByNormalizedName = new Map();
    countriesData.forEach((country) => {
        const normalized = normalizeName(country.country_name);
        dataByNormalizedName.set(normalized, country);
    });

    return allFeatures
        .filter((feature) => {
            const featureName = feature.properties?.name;
            if (!featureName) return false;
            const normalizedFeatureName = normalizeName(featureName);
            return normalizedSearchNames.has(normalizedFeatureName);
        })
        .map((feature) => {
            const featureName = feature.properties?.name;
            const normalizedFeatureName = normalizeName(featureName);
            const countryData = dataByNormalizedName.get(normalizedFeatureName);
            return {
                ...feature,
                countryData: countryData || null,
            };
        });
};

export const isGermany = (name) => {
    if (!name) return false;
    const normalized = name.toString().trim().toLowerCase();
    return normalized === "germany" || normalized === "de" || normalized === "deutschland";
};

export const createTileLayer = (url, options = {}) => {
    return L.tileLayer(url, {
        attribution: ATTRIBUTION,
        subdomains: "abcd",
        maxZoom: 19,
        ...options,
    });
};

export const setupLabelPane = (map) => {
    map.createPane("labels");
    const labelsPane = map.getPane("labels");
    if (labelsPane) {
        labelsPane.style.zIndex = 350;
        labelsPane.style.pointerEvents = "none";
    }
};

export const createColorScale = (countriesData) => {
    const values = countriesData.map((c) => c.demand_score).filter((v) => v != null && isFinite(v));
    const domain = values.length ? d3.extent(values) : [0, 100];
    return d3.scaleSequential(d3.interpolateRdYlGn).domain([domain[0], domain[1]]);
};

export const getFeatureStyle = (feature, colorScale) => {
    const countryData = feature.countryData;
    const score = countryData?.demand_score;
    const fillColor = score != null && isFinite(score) ? colorScale(score) : nodataColor;

    return {
        fill: true,
        fillColor,
        fillOpacity: 0.2,
        weight: 0.6,
        opacity: 1,
        color: fillColor,
        dashArray: "3",
    };
};

export const createPopupContent = (feature) => {
    const countryName = feature.properties?.name;
    const countryData = feature.countryData;
    const score = countryData?.demand_score;

    if (!countryData || score == null) {
        return `<b>${countryName}</b><br>No data available`;
    }

    return `<b>${countryName}</b><br>Value: ${score}`;
};

export const isPointInPolygon = (point, polygonFeature) => {
    if (!point || !polygonFeature || !polygonFeature.geometry) return false;

    const geometry = polygonFeature.geometry;
    const lat = point.lat;
    const lng = point.lng;

    if (geometry.type === "Polygon") {
        const coordinates = geometry.coordinates[0];
        return rayCasting(lat, lng, coordinates);
    }

    if (geometry.type === "MultiPolygon") {
        for (const polygon of geometry.coordinates) {
            const outerRing = polygon[0];
            if (rayCasting(lat, lng, outerRing)) {
                let inHole = false;
                for (let i = 1; i < polygon.length; i++) {
                    if (rayCasting(lat, lng, polygon[i])) {
                        inHole = true;
                        break;
                    }
                }
                if (!inHole) return true;
            }
        }
        return false;
    }

    return false;
};

const rayCasting = (lat, lng, polygon) => {
    let inside = false;
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
        const [xiLng, xiLat] = polygon[i];
        const [xjLng, xjLat] = polygon[j];
        const intersect =
            xiLat > lat !== xjLat > lat &&
            lng < ((xjLng - xiLng) * (lat - xiLat)) / (xjLat - xiLat) + xiLng;
        if (intersect) inside = !inside;
    }
    return inside;
};
