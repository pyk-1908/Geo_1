import type { MapCountryResponse } from "@types/competitor";

export const dummyMapMarks: MapCountryResponse = {
    country: [
        {
            country_name: "Germany",
            country_id: 1,
            country_code: "de",
            buyers: [
                {
                    buyer_name: "Acme Electronics GmbH",
                    buyer_id: 101,
                    salesforce_account_id: "0015g00000X1YZaAAN",
                    growth_score: 78,
                    num_plants_abs: 4,
                    locations: [
                        {
                            city_name: "Berlin",
                            city_id: 1001,
                            state_name: "Berlin",
                            lat: 52.520008,
                            lng: 13.404954,
                        },
                        {
                            city_name: "Dresden",
                            city_id: 1002,
                            state_name: "Saxony",
                            lat: 51.050407,
                            lng: 13.737262,
                        },
                    ],
                },
                {
                    buyer_name: "NordTech Solutions",
                    buyer_id: 102,
                    salesforce_account_id: "0015g00000X1YZbAAN",
                    growth_score: 54,
                    num_plants_abs: 2,
                    locations: [
                        {
                            city_name: "Hamburg",
                            city_id: 1003,
                            state_name: "Hamburg",
                            lat: 53.551086,
                            lng: 9.993682,
                        },
                    ],
                },
                {
                    buyer_name: "Bayern Parts AG",
                    buyer_id: 103,
                    salesforce_account_id: "0015g00000X1YZcAAN",
                    growth_score: 92,
                    num_plants_abs: 6,
                    locations: [
                        {
                            city_name: "Munich",
                            city_id: 1004,
                            state_name: "Bavaria",
                            lat: 48.135125,
                            lng: 11.581981,
                        },
                        {
                            city_name: "Nuremberg",
                            city_id: 1005,
                            state_name: "Bavaria",
                            lat: 49.452030,
                            lng: 11.076750,
                        },
                    ],
                },
            ],
            seller: {
                seller_name: "Demo Supply AG",
                seller_id: 900,
                locations: [
                    {
                        city_name: "Frankfurt",
                        city_id: 2001,
                        state_name: "Hesse",
                        lat: 50.110924,
                        lng: 8.682127,
                    },
                ],
            },
        },
    ],
};
