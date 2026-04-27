export type Product = {
    product_id: number;
    product_name: string;
};
export type Customer = {
    buyer_id: number;
    buyer_name: string;
};
export type ProductCluster = {
    product_cluster_id: number;
    product_cluster_name: string;
};
export type ProductGroup = {
    product_group_id: number;
    product_group_name: string;
};
export type GroupRawData = {
    product_group_id: number;
    product_group_name: string;
    product: Product[];
};
export type ClusterRawData = {
    product_cluster_id: number;
    product_cluster_name: string;
    product_group: GroupRawData[];
};
export type CustomerClusterGroupProduct = {
    buyer_id: number;
    buyer_name: string;
    product_cluster: ClusterRawData[];
};

export type CustomerCountry = {
    country_name: string;
    country_id: number;
    country_code: string;
};

export type CustomerCountryListResponse = CustomerCountry[];
export type CustomerClusterListResponse = ProductCluster[];
export type CustomerGroupListResponse = ProductGroup[];
export type CustomerProductListResponse = Product[];

export type CustomerPlant = {
    customer_plant_name: string;
    customer_plant_id: number;
};

export type CustomerPlantListResponse = CustomerPlant[];
