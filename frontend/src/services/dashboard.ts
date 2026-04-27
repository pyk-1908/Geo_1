import { get } from "../utils/requests";

export async function getCustomerCountryMap(
    countryIds: string | number,
    productIds: string,
) {
    const params = new URLSearchParams({
        country_id: String(countryIds),
        product_id: productIds,
    });
    return await get(`/buyer/buyer_map/?${params.toString()}`);
}
