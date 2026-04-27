<script setup>
import { ref, computed, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import Popover from "@components/base/Popover.vue";
import GoBack from "@components/GoBack.vue";
import LeafletChart from "@components/charts/LeafletChart.vue";
import TableProgressBar from "@components/table/TableProgressBar.vue";
import { numberSeparator } from "@utils/utils.ts";
import { useLoader } from "@composables/general/useLoader";
import { useFiltersStore } from "@stores/filters";
import { getCustomerCountryMap } from "@services/dashboard";

const filters = useFiltersStore();
const route = useRoute();
const router = useRouter();
const countryData = ref(null);
const infotextsData = ref(null);
const prevCountryIndex = ref(null);
const nextCountryIndex = ref(null);
const loader = useLoader();

const handleFilterCountry = (mode) => {
    if (!mode || !filters.c_map_countries || !filters.c_map_countries_selected) return;

    if (mode === "prev") {
        if (prevCountryIndex.value === null) return;
        const prevCountry = filters.c_map_countries[prevCountryIndex.value];
        if (prevCountry) return filters.setMapCountriesSelected(prevCountry);
    } else if (mode === "next") {
        if (nextCountryIndex.value === null) return;
        const nextCountry = filters.c_map_countries[nextCountryIndex.value];
        if (nextCountry) return filters.setMapCountriesSelected(nextCountry);
    }
};

const updateRouteParams = (country) => {
    if (!country || !route) return;
    const next = {
        name: route.name,
        params: { ...route.params },
        query: { ...route.query },
    };
    const countryId = country.country_id?.toString();
    const countryName = country.country_name.toString();
    if (countryId) next.params.countryId = countryId;
    if (countryName) next.params.countryName = countryName;
    router.replace(next);
};

const selectedCountryKey = computed(() =>
    filters.c_map_countries_selected
        ? String(filters.c_map_countries_selected.country_id ?? "")
        : ""
);

const tableHeaders = computed(() => [
    {
        title: "Customer",
        key: "competitor",
        infotext: infotextsData.value?.customer ?? "Name of the competitor",
    },
    {
        title: "Growth",
        key: "growth",
        infotext: infotextsData.value?.growth ?? "Year-over-year growth rate of the competitor",
    },
    {
        title: "# of Plants",
        key: "num_plants",
        infotext: infotextsData.value?.num_of_plants ?? "Number of production plants",
    },
]);

watch(
    selectedCountryKey,
    async (newKey, oldKey) => {
        if (newKey === oldKey && newKey !== "" && newKey !== "all") return;
        const country = filters.c_map_countries_selected;
        const products = filters.c_map_products_selected;
        if (!country || !products?.length || !filters.c_map_countries) return;
        updateRouteParams(country);
        const currentCountryId = country.country_id;
        if (!currentCountryId) return;
        loader.show(".main-content");
        const productIds = products.map((el) => el.product_id).join(",");
        try {
            loader.show(".main-content");
            const data = await getCustomerCountryMap(currentCountryId, productIds);
            if (data && data.country) countryData.value = data.country?.[0];
            if (data && data.infotext) infotextsData.value = data.infotext;
            const currentCountryTarget = filters.c_map_countries.find(
                (c) => c.country_id == currentCountryId
            );
            const currentCountryIndex = filters.c_map_countries.indexOf(currentCountryTarget);
            const prevCountry = filters.c_map_countries[currentCountryIndex - 1];
            const nextCountry = filters.c_map_countries[currentCountryIndex + 1];
            prevCountryIndex.value = prevCountry ? currentCountryIndex - 1 : null;
            nextCountryIndex.value = nextCountry ? currentCountryIndex + 1 : null;
        } catch (error) {
            console.error(error);
            loader.hide();
        }
        loader.hide();
    },
    { deep: true, immediate: true }
);
</script>

<template>
    <div class="page-wrap">
        <div class="page-content">
            <GoBack />
            <section class="section">
                <div class="section-title">
                    <h1>Customer Map</h1>
                    <Popover :is-left="true">
                        {{ infotextsData?.map }}
                    </Popover>
                </div>
                <div class="d-flex gap-3 main-content">
                    <div class="chart-container">
                        <LeafletChart
                            :single-country="countryData?.country_name || filters.c_map_countries_selected?.country_name || 'Germany'"
                            :is-single-country="true"
                            :country-data="countryData?.country?.[0] || countryData || null"
                            :has-prev="prevCountryIndex !== null"
                            :has-next="nextCountryIndex !== null"
                            @country-navigate="handleFilterCountry"/>
                        <div class="legend">
                            <div class="legend__holder">
                                <div class="legend__item blue"></div>
                                <span>Customer Plant</span>
                            </div>
                            <div class="legend__holder">
                                <div class="legend__item green"></div>
                                <span>Company Plant</span>
                            </div>
                        </div>
                    </div>
                    <div class="table__container--scrollable">
                        <div class="table__overflow--competitor">
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th v-for="header in tableHeaders" :key="header.key">
                                            <div class="flex-start-gap-10">
                                                <span>{{ header.title }}</span>
                                                <div class="header-row">
                                                    <Popover :main-axis="6" :cross-axis="5">
                                                        {{ header.infotext }}
                                                    </Popover>
                                                    <div class="sort-icon">
                                                        <div class="arrow-up"></div>
                                                        <div class="arrow-down"></div>
                                                    </div>
                                                </div>
                                            </div>
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr
                                        v-if="countryData?.buyers"
                                        v-for="(buyer, i) in countryData?.buyers"
                                        :key="i"
                                        :class="{ highlighted: i === 3 }">
                                        <td>
                                            <span class="active" :title="buyer.buyer_name">
                                                {{ buyer.buyer_name }}
                                            </span>
                                        </td>
                                        <td>
                                            <TableProgressBar
                                                :value="buyer.growth_score"
                                                :is-with-arrow="false" />
                                        </td>
                                        <td>
                                            <span>
                                                {{ numberSeparator(buyer.num_plants_abs) }}
                                            </span>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    </div>
</template>

<style scoped lang="sass">
@use '@styles/utils/_variables' as *
@use '@styles/utils/_mixins' as *
@forward '@styles/components/table/scrollable-table.sass'

.page-wrap
    padding-inline: 5vw
    padding-block: 20px

.page-content
    max-width: 1400px
    margin-inline: auto

:deep(.go-back)
    padding-inline: 0

.d-flex
    display: flex

.gap-3
    gap: 1rem

.table__container--scrollable
    flex-shrink: 0
    width: 50%

.table__container--scrollable .table__overflow--competitor table
    td:first-child
        position: static
    th:first-child
        left: unset

h2
    font-size: $size-16
    font-weight: 400
    color: $gray

.section
    margin: 0 0 50px 0

.main-content
    min-height: 50vh

:deep(.table .info-container svg)
    width: 15px
    height: 15px

.chart-container
    flex: 1
    min-width: 0
    display: flex
    flex-direction: column

.legend
    display: flex
    align-items: center
    justify-content: center
    gap: 35px
    margin-top: 10px

    span
        font-size: $size-12
        color: $dark

    &__holder
        display: flex
        align-items: center
        gap: 15px

    &__item
        width: 25px
        height: 15px
        border-radius: 10px

        &.green
            background: $primary-1
            border: thin solid $primary-2

        &.purple
            border: thin solid $purple-bar
            background: $purple-bar-gradient

        &.blue
            border: thin solid $blue-border
            background: $blue

.v-enter-active,
.v-leave-active
    transition: opacity 0.3s ease-in-out

.v-enter-from,
.v-leave-to
    opacity: 0
</style>
