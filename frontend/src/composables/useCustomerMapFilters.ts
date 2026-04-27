import { useFiltersStore } from "@stores/filters";
import { computed, watch } from "vue";
import {
    getListClusterBuyerMap,
    getListCountryBuyerMap,
    getListGroupBuyerMap,
    getListProductBuyerMap,
} from "@services/filters";

export function useCustomerMapFilters() {
    const filters = useFiltersStore();
    let isInitializing = false;
    let initialized = false;

    const selectedClusterKey = computed(() =>
        filters.c_map_clusters_selected?.map((c) => Number(c.product_cluster_id)).sort().join(",")
    );
    const selectedGroupKey = computed(() =>
        filters.c_map_groups_selected?.map((g) => Number(g.product_group_id)).sort().join(",")
    );
    const selectedProductKey = computed(() =>
        filters.c_map_products_selected?.map((p) => Number(p.product_id)).sort().join(",")
    );

    const resetMapFiltersState = () => {
        filters.c_map_clusters = null;
        filters.c_map_clusters_selected = null;
        filters.c_map_groups = null;
        filters.c_map_groups_selected = null;
        filters.c_map_products = null;
        filters.c_map_products_selected = null;
        filters.c_map_countries = null;
        filters.c_map_countries_selected = null;
    };

    const init = async (force = false) => {
        if (isInitializing) return;
        if (initialized && !force) return;
        isInitializing = true;
        resetMapFiltersState();
        try {
            const clusters = await getListClusterBuyerMap();
            if (clusters?.length) {
                filters.setMapClusters(clusters);
                filters.setMapClustersSelected([clusters[0]]);
            }
            initialized = true;
        } finally {
            isInitializing = false;
        }
    };

    const resetInit = () => {
        initialized = false;
    };

    watch(
        selectedClusterKey,
        async (newKey, oldKey) => {
            if (newKey === oldKey && newKey !== "" && newKey !== "all") return;
            if (!selectedClusterKey.value) {
                filters.c_map_groups = null;
                filters.c_map_groups_selected = null;
                return;
            }
            const groups = await getListGroupBuyerMap(selectedClusterKey.value);
            if (!groups?.length) return;
            filters.setMapGroups(groups);
            filters.setMapGroupsSelected([groups[0]]);
        },
        { deep: true }
    );

    watch(
        selectedGroupKey,
        async (newKey, oldKey) => {
            if (newKey === oldKey && newKey !== "" && newKey !== "all") return;
            if (!selectedGroupKey.value) {
                filters.c_map_products = null;
                filters.c_map_products_selected = null;
                return;
            }
            const products = await getListProductBuyerMap(selectedGroupKey.value);
            if (!products?.length) return;
            filters.setMapProducts(products);
            filters.setMapProductsSelected([products[0]]);
        },
        { deep: true }
    );

    watch(
        selectedProductKey,
        async (newKey, oldKey) => {
            if (newKey === oldKey && newKey !== "" && newKey !== "all") return;
            if (!selectedProductKey.value) {
                filters.c_map_countries = null;
                filters.c_map_countries_selected = null;
                return;
            }
            const countries = await getListCountryBuyerMap(selectedProductKey.value);
            if (!countries?.length) return;
            filters.setMapCountries(countries);
            const germany = countries.find((c) => c.country_name?.toLowerCase() === "germany");
            filters.setMapCountriesSelected(germany ?? countries[0]);
        },
        { deep: true }
    );

    return { init, resetInit };
}
