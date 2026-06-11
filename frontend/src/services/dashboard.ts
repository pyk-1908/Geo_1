import { get } from "../utils/requests";
import { dummyMapMarks } from "@/data/dummyMapMarks";

export async function getCustomerCountryMap(
    countryIds: string | number,
    productIds: string,
) {
    const params = new URLSearchParams({
        country_id: String(countryIds),
        product_id: productIds,
    });
    const data = await get(`/buyer/buyer_map/?${params.toString()}`);

    if (
        import.meta.env.DEV &&
        (!data || data.success === false || !data.country || data.country.length === 0)
    ) {
        return dummyMapMarks;
    }

    return data;
}
