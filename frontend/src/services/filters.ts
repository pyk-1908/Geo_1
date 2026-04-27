import { get } from "@utils/requests.ts";
import type { ProductCluster, ProductGroup, Product, CustomerCountry } from "@lib/filters";

export async function getListClusterBuyerMap(): Promise<ProductCluster[]> {
    return await get("/lists/buyermap/cluster/");
}

export async function getListGroupBuyerMap(clusterIds: string): Promise<ProductGroup[]> {
    return await get(`/lists/buyermap/group/?cluster_id=${clusterIds}`);
}

export async function getListProductBuyerMap(groupIds: string): Promise<Product[]> {
    return await get(`/lists/buyermap/product/?group_id=${groupIds}`);
}

export async function getListCountryBuyerMap(productIds: string): Promise<CustomerCountry[]> {
    return await get(`/lists/buyermap/country/?product_id=${productIds}`);
}
