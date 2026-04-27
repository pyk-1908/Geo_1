import { defineStore } from "pinia";
import { ref } from "vue";
import type { Customer, Product, ProductCluster, ProductGroup } from "@lib/filters";
import {
    ClusterRawData,
    CustomerClusterGroupProduct,
    CustomerCountry,
    CustomerCountryListResponse,
    CustomerPlant,
    CustomerPlantListResponse,
    GroupRawData,
} from "@lib/filters";

export const useFiltersStore = defineStore("filters", () => {
    const stickyFilled = ref<boolean>(false);
    const products = ref<Product[]>([]);
    const customer = ref<Customer | null>(null);
    const productsGroup = ref<ProductGroup[]>([]);
    const productsCluster = ref<ProductCluster[]>([]);
    const customerOptions = ref<Customer[]>([]);
    const productOptions = ref<Product[]>([]);
    const productGroupOptions = ref<ProductGroup[]>([]);
    const productClusterOptions = ref<ProductCluster[]>([]);
    const rawData = ref<CustomerClusterGroupProduct[]>([]);
    const clustersRawData = ref<ClusterRawData[]>([]);
    const currentCustomerIndex = ref<null | number>(null);
    const selectedClustersIndexes = ref<number[]>([]);
    const selectedProductGroupsRaw = ref<GroupRawData[]>([]);
    // for tender scenario
    const countryOptions = ref<CustomerCountryListResponse>([] as CustomerCountryListResponse);
    const plantOptions = ref<CustomerPlantListResponse>([] as CustomerPlantListResponse);
    const selectedCountry = ref<CustomerCountry | null>(null);
    const selectedPlant = ref<CustomerPlant | null>(null);
    // for customer map / buyer map
    const c_map_clusters = ref<ProductCluster[] | null>(null);
    const c_map_clusters_selected = ref<ProductCluster[] | null>(null);
    const c_map_groups = ref<ProductGroup[] | null>(null);
    const c_map_groups_selected = ref<ProductGroup[] | null>(null);
    const c_map_products = ref<Product[] | null>(null);
    const c_map_products_selected = ref<Product[] | null>(null);
    const c_map_countries = ref<CustomerCountryListResponse | null>(null);
    const c_map_countries_selected = ref<CustomerCountry | null>(null);

    const loadingCount = ref(0);
    const isReady = ref(false);
    let readyTimeout: ReturnType<typeof setTimeout> | null = null;

    function startFilterLoad() {
        loadingCount.value++;
        if (readyTimeout) clearTimeout(readyTimeout);
        isReady.value = false;
    }

    function endFilterLoad() {
        loadingCount.value = Math.max(0, loadingCount.value - 1);
        if (loadingCount.value === 0) {
            if (readyTimeout) clearTimeout(readyTimeout);
            readyTimeout = setTimeout(() => {
                isReady.value = true;
            }, 200);
        }
    }

    function assignRawData(passRawData: CustomerClusterGroupProduct[]) {
        rawData.value = [...passRawData];
    }

    function assignCustomersList(customersList: Customer[]) {
        customerOptions.value = [...customersList];
    }

    function setCustomer(customerIndex: number | null) {
        customer.value =
            customerIndex || customerIndex == 0 ? customerOptions.value[customerIndex] : null;
    }

    function setCountryOptions(data: CustomerCountryListResponse) {
        countryOptions.value = data;
    }

    function setPlantOptions(data: CustomerPlantListResponse) {
        plantOptions.value = data;
    }

    function setCountry(data: CustomerCountry) {
        selectedCountry.value = data;
    }

    function setPlant(data: CustomerPlant) {
        selectedPlant.value = data;
    }

    function setMapClusters(data: ProductCluster[] | null) {
        c_map_clusters.value = data;
    }

    function setMapClustersSelected(data: ProductCluster[] | null) {
        c_map_clusters_selected.value = data;
    }

    function setMapGroups(data: ProductGroup[] | null) {
        c_map_groups.value = data;
    }

    function setMapGroupsSelected(data: ProductGroup[] | null) {
        c_map_groups_selected.value = data;
    }

    function setMapProducts(data: Product[] | null) {
        c_map_products.value = data;
    }

    function setMapProductsSelected(data: Product[] | null) {
        c_map_products_selected.value = data;
    }

    function setMapCountries(data: CustomerCountryListResponse | null) {
        c_map_countries.value = data;
    }

    function setMapCountriesSelected(data: CustomerCountry | null) {
        c_map_countries_selected.value = data;
    }

    const clearFilters = () => {
        startFilterLoad();

        stickyFilled.value = false;

        customer.value = null;
        products.value = [];
        productsGroup.value = [];
        productsCluster.value = [];

        customerOptions.value = [];
        productOptions.value = [];
        productGroupOptions.value = [];
        productClusterOptions.value = [];

        rawData.value = [];
        clustersRawData.value = [];
        selectedProductGroupsRaw.value = [];
        selectedClustersIndexes.value = [];

        countryOptions.value = [];
        plantOptions.value = [];
        selectedCountry.value = null;
        selectedPlant.value = null;

        currentCustomerIndex.value = null;

        c_map_clusters.value = null;
        c_map_clusters_selected.value = null;
        c_map_groups.value = null;
        c_map_groups_selected.value = null;
        c_map_products.value = null;
        c_map_products_selected.value = null;
        c_map_countries.value = null;
        c_map_countries_selected.value = null;

        endFilterLoad();
    };

    return {
        stickyFilled,
        customer,
        products,
        productsGroup,
        productsCluster,
        customerOptions,
        productOptions,
        productGroupOptions,
        productClusterOptions,
        rawData,
        clustersRawData,
        currentCustomerIndex,
        selectedClustersIndexes,
        selectedProductGroupsRaw,
        selectedCountry,
        selectedPlant,
        countryOptions,
        plantOptions,
        setCountry,
        setPlant,
        assignCustomersList,
        assignRawData,
        setCustomer,
        setCountryOptions,
        setPlantOptions,
        startFilterLoad,
        endFilterLoad,
        isReady,
        loadingCount,
        clearFilters,
        c_map_clusters,
        c_map_clusters_selected,
        setMapClusters,
        setMapClustersSelected,
        c_map_groups,
        c_map_groups_selected,
        setMapGroups,
        setMapGroupsSelected,
        c_map_products,
        c_map_products_selected,
        setMapProducts,
        setMapProductsSelected,
        c_map_countries,
        c_map_countries_selected,
        setMapCountries,
        setMapCountriesSelected,
    };
});
