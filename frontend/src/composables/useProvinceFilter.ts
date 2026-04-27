import { ref, watch, type Ref } from "vue";
import type {
    LocationCoordinates,
    CompetitorWithLocations,
    CountryDataItem,
    MapCountryResponse,
    GeoJSONFeatureCollection,
    GeoJSONFeature,
} from "@/types/competitor";

// Cache for province GeoJSON feature
let provinceFeatureCache: { name: string; feature: GeoJSONFeature } | null = null;

const GERMANY_PROVINCES_URL =
    "https://raw.githubusercontent.com/wbkd/germany-iconfont/master/geojson/bundeslaender.geo.json";

const normalizeProvinceName = (name: string | undefined | null): string => {
    if (!name) return "";
    return name.toString().trim().toLowerCase().replace(/\s+/g, " ");
};

const rayCasting = (lat: number, lng: number, polygon: number[][]): boolean => {
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

const isPointInPolygon = (
    point: { lat: number; lng: number },
    polygonFeature: GeoJSONFeature
): boolean => {
    if (!point || !polygonFeature || !polygonFeature.geometry) return false;

    const geometry = polygonFeature.geometry;
    const { lat, lng } = point;

    if (geometry.type === "Polygon") {
        const coordinates = (geometry.coordinates as number[][][])[0];
        return rayCasting(lat, lng, coordinates);
    }

    if (geometry.type === "MultiPolygon") {
        for (const polygon of geometry.coordinates as number[][][][]) {
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

const getProvinceFeature = async (provinceName: string): Promise<GeoJSONFeature | null> => {
    if (provinceFeatureCache && provinceFeatureCache.name === provinceName) {
        return provinceFeatureCache.feature;
    }

    try {
        const res = await fetch(GERMANY_PROVINCES_URL);
        const data = (await res.json()) as GeoJSONFeatureCollection;
        const provinces = Array.isArray(data.features) ? data.features : [];

        const normalizedTargetProvince = normalizeProvinceName(provinceName);

        const provinceFeature = provinces.find((feature: GeoJSONFeature) => {
            const props = feature?.properties || {};
            const featureName =
                props.name || props.NAME || props.Name || props.gen || props.GEN || "";
            return normalizeProvinceName(featureName) === normalizedTargetProvince;
        });

        if (!provinceFeature) return null;

        provinceFeatureCache = { name: provinceName, feature: provinceFeature };
        return provinceFeature;
    } catch (error) {
        console.warn("Error loading province feature:", error);
        return null;
    }
};

const checkLocationInProvince = async (
    lat: number | null | undefined,
    lng: number | null | undefined,
    provinceName: string
): Promise<boolean> => {
    if (lat == null || lng == null || !isFinite(+lat) || !isFinite(+lng)) return false;

    const provinceFeature = await getProvinceFeature(provinceName);
    if (!provinceFeature) return false;

    return isPointInPolygon({ lat: +lat, lng: +lng }, provinceFeature);
};

const getLocationCoordinates = (
    location: LocationCoordinates
): { lat: number | null | undefined; lng: number | null | undefined } => {
    return {
        lat: location.lat ?? location.latitude ?? location.lat_coordinate,
        lng:
            location.lng ??
            location.lon ??
            location.long ??
            location.longitude ??
            location.lng_coordinate,
    };
};

export function useProvinceFilter(
    provinceName: Ref<string | null>,
    countryData: Ref<MapCountryResponse | null>
) {
    const filteredCountryData = ref<CountryDataItem | null>(null);
    const isLoadingProvinceData = ref(false);

    const toArray = <T>(value: T | T[] | null | undefined): T[] => {
        if (!value) return [];
        return Array.isArray(value) ? value.filter(Boolean) : [value];
    };

    const extractLocations = (entity: Record<string, unknown>): LocationCoordinates[] => {
        if (!entity) return [];
        if (Array.isArray(entity.locations)) return entity.locations as LocationCoordinates[];
        return [entity as LocationCoordinates];
    };

    const filterCompetitorsByProvince = async (
        competitors: CompetitorWithLocations[],
        provinceName: string
    ): Promise<CompetitorWithLocations[]> => {
        if (!competitors || !Array.isArray(competitors) || !provinceName) return [];

        const filteredCompetitors: CompetitorWithLocations[] = [];

        for (const competitor of competitors) {
            if (!competitor.locations || !Array.isArray(competitor.locations)) continue;

            let hasLocationInProvince = false;
            for (const location of competitor.locations) {
                const { lat, lng } = getLocationCoordinates(location);

                if (await checkLocationInProvince(lat, lng, provinceName)) {
                    hasLocationInProvince = true;
                    break;
                }
            }

            if (hasLocationInProvince) {
                filteredCompetitors.push(competitor);
            }
        }

        return filteredCompetitors;
    };

    const filterCustomersByProvince = async (
        customers: Array<Record<string, unknown>>,
        provinceName: string
    ): Promise<Array<Record<string, unknown>>> => {
        if (!customers || !Array.isArray(customers) || !provinceName) return [];

        const filteredCustomers: Array<Record<string, unknown>> = [];

        for (const customer of customers) {
            const locations = extractLocations(customer);
            for (const location of locations) {
                const { lat, lng } = getLocationCoordinates(location);
                if (await checkLocationInProvince(lat, lng, provinceName)) {
                    filteredCustomers.push(customer);
                    break;
                }
            }
        }

        return filteredCustomers;
    };

    watch(
        [countryData, provinceName],
        async () => {
            if (!countryData.value || !provinceName.value) {
                filteredCountryData.value = null;
                return;
            }

            isLoadingProvinceData.value = true;
            try {
                const base = (countryData.value.country?.[0] || countryData.value || {}) as Record<string, unknown>;
                const { buyers: _buyers, buyer: _buyer, ...baseWithoutCustomers } = base;
                const allCompetitors = toArray(base.competitors as CompetitorWithLocations[]);
                const allBuyers = toArray((base.buyers ?? base.buyer ?? []) as Array<Record<string, unknown>>);

                const [provinceCompetitors, provinceCustomers] = await Promise.all([
                    allCompetitors.length
                        ? filterCompetitorsByProvince(allCompetitors, provinceName.value)
                        : Promise.resolve([]),
                    allBuyers.length
                        ? filterCustomersByProvince(allBuyers, provinceName.value)
                        : Promise.resolve([]),
                ]);

                filteredCountryData.value = {
                    ...baseWithoutCustomers,
                    competitors: provinceCompetitors,
                    buyers: provinceCustomers,
                    seller: base.seller || null,
                };
            } finally {
                isLoadingProvinceData.value = false;
            }
        },
        { immediate: true, deep: true }
    );

    return {
        filteredCountryData,
        isLoadingProvinceData,
    };
}
