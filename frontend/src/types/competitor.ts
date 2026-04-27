// Types for province filtering (used by useProvinceFilter)
export type LocationCoordinates = {
    lat?: number | null;
    lng?: number | null;
    latitude?: number | null;
    longitude?: number | null;
    lon?: number | null;
    long?: number | null;
    lat_coordinate?: number | null;
    lng_coordinate?: number | null;
};

export type CompetitorWithLocations = {
    competitor_id?: number;
    competitor_name?: string;
    locations?: LocationCoordinates[];
    [key: string]: unknown;
};

export type CountryDataItem = {
    competitors?: CompetitorWithLocations[];
    customer?: unknown[];
    seller?: unknown | null;
    [key: string]: unknown;
};

export type MapCountryResponse = {
    country?: CountryDataItem[];
} & CountryDataItem;

export type GeoJSONFeature = {
    type: "Feature";
    properties?: {
        name?: string;
        NAME?: string;
        Name?: string;
        gen?: string;
        GEN?: string;
        [key: string]: unknown;
    };
    geometry?: {
        type: string;
        coordinates: unknown;
        [key: string]: unknown;
    };
    [key: string]: unknown;
};

export type GeoJSONFeatureCollection = {
    type?: "FeatureCollection";
    features?: GeoJSONFeature[];
    [key: string]: unknown;
};
