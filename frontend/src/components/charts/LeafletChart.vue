<script setup>
import { ref, onMounted, onUnmounted, watch, computed, toRef } from "vue";
import { useLeafletChart } from "@composables/charts/leafletChart/useLeafletChart";
import { normalizeCountryName } from "@composables/charts/leafletChart/leafletUtils";
import { getAccountNotes } from "@services/salesforce";
import TableTooltipRight from "@components/icons/TableTooltipRight.vue";
import ChevronRight from "@components/icons/ChevronRight.vue";
import MapFilter from "@components/MapFilter.vue";
import { useDebounceFn } from "@vueuse/core";

const props = defineProps({
    countriesData: {
        type: Array,
        default: () => [],
    },
    countryData: {
        type: Object,
        default: null,
    },
    isSingleCountry: {
        type: Boolean,
        default: false,
    },
    singleCountry: {
        type: String,
        default: null,
    },
    hasPrev: {
        type: Boolean,
        default: false,
    },
    hasNext: {
        type: Boolean,
        default: false,
    },
    isPopup: {
        type: Boolean,
        default: false,
    },
    provinceName: {
        type: String,
        default: null,
    },
    isLCC: {
        type: Boolean,
        default: false,
    },
    showCountryOutlines: {
        type: Boolean,
        default: true,
    },
});

const selectedFilters = ref({ competitors: [], customers: [], sellers: [] });
const filtersInitialized = ref(false);

const emit = defineEmits(["countryNavigate"]);

const toArray = (value) => {
    if (!value) return [];
    return Array.isArray(value) ? value.filter(Boolean) : [value];
};

const normalizeCustomers = (value) => {
    return toArray(value).map((item) => ({
        ...item,
        customer_id:
            item?.customer_id ??
            item?.buyer_id ??
            item?.id ??
            item?.customerId ??
            item?.buyerId ??
            null,
        customer_name: item?.customer_name ?? item?.buyer_name ?? item?.name ?? item?.label ?? null,
    }));
};

const normalizedCountryEntities = computed(() => {
    const base = props.countryData?.country?.[0] || props.countryData || {};
    return {
        base,
        competitors: toArray(base.competitors),
        customers: normalizeCustomers(
            base.customer ?? base.customers ?? base.buyers ?? base.buyer ?? null
        ),
        sellers: toArray(base.seller),
    };
});

const isCountryDataFresh = computed(() => {
    if (!props.singleCountry || !props.countryData) return false;
    const dataName =
        props.countryData?.country_name || props.countryData?.country?.[0]?.country_name;
    if (!dataName) return false;
    return normalizeCountryName(dataName) === normalizeCountryName(props.singleCountry);
});

const countryCode = computed(() => {
    if (!isCountryDataFresh.value) return null;
    return props.countryData?.country_code || props.countryData?.country?.[0]?.country_code || null;
});

const countryNameDisplay = computed(() => {
    return (
        props.singleCountry ||
        props.countryData?.country_name ||
        props.countryData?.country?.[0]?.country_name ||
        ""
    );
});

const flagSrc = computed(() => {
    return countryCode.value ? `/assets/flags/${countryCode.value}.svg` : null;
});

const mapFilterOptions = computed(() => {
    if (!isCountryDataFresh.value) {
        return { competitors: [], customers: [], sellers: [] };
    }
    return {
        competitors: normalizedCountryEntities.value.competitors,
        customers: normalizedCountryEntities.value.customers,
        sellers: normalizedCountryEntities.value.sellers,
    };
});

const filteredCountryData = computed(() => {
    if (!isCountryDataFresh.value) {
        return null;
    }
    const { base } = normalizedCountryEntities.value;
    const { competitors, customers, sellers } = mapFilterOptions.value;
    const sel = selectedFilters.value || { competitors: [], customers: [], sellers: [] };

    const filterByIds = (arr, ids, idKey) => {
        if (!Array.isArray(arr)) return [];
        if (!ids || ids.length === 0) return [];
        return arr.filter((item) => ids.includes(item?.[idKey]));
    };

    const filteredCompetitors = filterByIds(competitors, sel.competitors, "competitor_id");
    const filteredCustomers = filterByIds(customers, sel.customers, "customer_id");
    const filteredSellers = filterByIds(sellers, sel.sellers, "seller_id");

    return {
        ...base,
        competitors: filteredCompetitors,
        customer: filteredCustomers,
        customers: filteredCustomers,
        seller: filteredSellers.length ? filteredSellers : null,
    };
});

const handleCountryNavigate = (direction, event) => {
    event?.preventDefault();
    event?.stopPropagation();
    emit("countryNavigate", direction);
};

const mapContainer = ref(null);
const { initMap, setCountriesData, setSingleCountry, setSingleProvince, destroyMap } =
    useLeafletChart({
        isPopup: props.isPopup,
        isLCC: () => props.isLCC,
        showCountryOutlines: () => props.showCountryOutlines,
        loadNotes: getAccountNotes,
    });

const initializeFilters = () => {
    if (filtersInitialized.value) return;
    if (!isCountryDataFresh.value) return;
    const opts = mapFilterOptions.value;
    selectedFilters.value = {
        competitors: (opts.competitors || []).map((o) => o?.competitor_id).filter(Boolean),
        customers: (opts.customers || []).map((o) => o?.customer_id).filter(Boolean),
        sellers: (opts.sellers || []).map((o) => o?.seller_id).filter(Boolean),
    };
    filtersInitialized.value = true;
};

const updateSingleCountry = async () => {
    if (!props.singleCountry || !mapContainer.value) return;
    initializeFilters();
    await setSingleCountry(props.singleCountry, filteredCountryData.value);
};

const updateSingleProvince = async () => {
    if (!props.singleCountry || !props.provinceName || !mapContainer.value) return;
    initializeFilters();
    await setSingleProvince(props.singleCountry, props.provinceName, filteredCountryData.value);
};

const debouncedUpdateCountry = useDebounceFn(updateSingleCountry, 50);
const debouncedUpdateProvince = useDebounceFn(updateSingleProvince, 50);

watch(
    () => props.countriesData,
    (newVal) => {
        if (newVal && newVal.length > 0) {
            setCountriesData(newVal);
        }
    },
    { immediate: true }
);

watch(
    () => [props.singleCountry, props.countryData, props.provinceName, props.isLCC],
    ([newCountry], [oldCountry] = []) => {
        if (newCountry !== oldCountry) {
            filtersInitialized.value = false;
        }
        if (props.provinceName) {
            debouncedUpdateProvince();
        } else {
            debouncedUpdateCountry();
        }
    },
    { immediate: true, deep: true }
);

watch(
    () => mapFilterOptions.value,
    (newOptions, oldOptions) => {
        const hasNewData =
            newOptions.competitors.length > 0 ||
            newOptions.customers.length > 0 ||
            newOptions.sellers.length > 0;

        const hadOldData =
            oldOptions &&
            (oldOptions.competitors.length > 0 ||
                oldOptions.customers.length > 0 ||
                oldOptions.sellers.length > 0);

        if (hasNewData || hadOldData) {
            filtersInitialized.value = false;
            initializeFilters();
            if (props.provinceName) {
                debouncedUpdateProvince();
            } else {
                debouncedUpdateCountry();
            }
        }
    },
    { deep: true }
);

watch(
    () => selectedFilters.value,
    () => {
        if (props.provinceName) {
            debouncedUpdateProvince();
        } else {
            debouncedUpdateCountry();
        }
    },
    { deep: true }
);

onMounted(() => {
    initMap(mapContainer.value);
    if (props.singleCountry) {
        if (props.provinceName) {
            debouncedUpdateProvince();
        } else {
            debouncedUpdateCountry();
        }
    } else if (props.countriesData && props.countriesData.length > 0) {
        setCountriesData(props.countriesData);
    }
});

onUnmounted(() => {
    destroyMap();
});
</script>

<template>
    <template v-if="!isSingleCountry">
        <div ref="mapContainer" class="map-container"></div>
    </template>
    <template v-else>
        <div class="position-relative">
            <div ref="mapContainer" class="map-container"></div>
            <div
                v-if="isSingleCountry && !isPopup && mapFilterOptions.competitors"
                class="leaflet-filter">
                <MapFilter v-if="!isLCC" v-model="selectedFilters" :options="mapFilterOptions" />
            </div>
            <div v-if="flagSrc" class="leaflet-flag">
                <img :src="flagSrc" :alt="countryNameDisplay" />
                <span>{{ countryNameDisplay }}</span>
            </div>
            <div
                v-if="!isLCC"
                :class="[
                    'chevron__container',
                    'chevron__container--back',
                    { 'opacity-50': !hasPrev },
                ]"
                @click="handleCountryNavigate('prev', $event)">
                <ChevronRight />
            </div>
            <div
                v-if="!isLCC"
                :class="['chevron__container', { 'opacity-50': !hasNext }]"
                @click="handleCountryNavigate('next', $event)">
                <ChevronRight />
            </div>
        </div>
    </template>
</template>

<style scoped lang="sass">
.map-container
    width: 100%
    height: 500px
    border-radius: 8px
    overflow: hidden

.position-relative
    position: relative

.leaflet-filter
    position: absolute
    top: 10px
    left: 10px
    z-index: 1000

.leaflet-flag
    position: absolute
    top: 14px
    right: 14px
    display: flex
    align-items: center
    gap: 5px
    z-index: 99

    img
        width: auto
        max-height: 45px
        border-radius: 3px

    span
        font-size: 1rem
        color: #2a2a2a

.chevron__container
    position: absolute
    top: 50%
    right: 10px
    translate: 0 -50%
    z-index: 1000

    &--back
        right: auto
        left: 10px

        :deep(svg)
            rotate: 180deg

.opacity-50
    opacity: 0.5
    pointer-events: none
</style>
