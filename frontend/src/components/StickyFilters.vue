<script setup>
import { ref, nextTick, watch } from "vue";
import { useRoute } from "vue-router";
import { useFiltersStore } from "@stores/filters";
import { useCustomerMapFilters } from "@composables/useCustomerMapFilters";
import Multiselect from "@components/inputs/Multiselect.vue";
import TheSelect from "@components/inputs/TheSelect.vue";

const route = useRoute();
const filters = useFiltersStore();
const customerMapFilters = useCustomerMapFilters();
const isMinimized = ref(false);

const isCustomerMap = () =>
    route.name === "customer.map";

const handleMinimize = async () => {
    await nextTick();
    isMinimized.value = true;
};

const handleExpand = async () => {
    await nextTick();
    isMinimized.value = false;
};

watch(
    () => route.name,
    async () => {
        if (isCustomerMap()) {
            await customerMapFilters.init();
        } else {
            customerMapFilters.resetInit();
        }
    },
    { immediate: true }
);
</script>

<template>
    <div
        v-if="isCustomerMap()"
        class="sticky-filters"
        :class="{ 'sticky-filters--minimized': isMinimized }">
        <div class="sticky-filters__inner" v-show="!isMinimized">
            <div class="sticky-filters__content">
                <Multiselect
                    v-model="filters.c_map_clusters_selected"
                    :options="filters.c_map_clusters ?? []"
                    displayOption="product_cluster_name"
                    class="filter--cluster">
                    Product Cluster
                </Multiselect>
                <Multiselect
                    v-model="filters.c_map_groups_selected"
                    :options="filters.c_map_groups ?? []"
                    displayOption="product_group_name"
                    class="filter--group">
                    Product Group
                </Multiselect>
                <Multiselect
                    v-model="filters.c_map_products_selected"
                    :options="filters.c_map_products ?? []"
                    displayOption="product_name"
                    class="filter--product">
                    Product
                </Multiselect>
                <TheSelect
                    v-model="filters.c_map_countries_selected"
                    :options="filters.c_map_countries ?? []"
                    displayOption="country_name"
                    class="filter--country">
                    Country
                </TheSelect>
            </div>
        </div>
        <button
            v-show="!isMinimized"
            type="button"
            class="button--minimize"
            @mousedown.prevent="handleMinimize">
            Minimize
        </button>
        <button
            v-show="isMinimized"
            type="button"
            class="button button--expand"
            @mousedown.prevent="handleExpand">
            Filters
        </button>
    </div>
</template>

<style lang="sass">
@forward '@styles/components/sticky-filters.sass'
</style>
