<script setup>
import { ref, computed, watch } from "vue";
import ActionButton from "@components/base/ActionButton.vue";
import TableIcon from "@components/icons/TableIcon.vue";
import { useOutsideClick } from "@/composables/general/useOutsideClick";

const props = defineProps({
    options: {
        type: Object,
        default: () => ({
            competitors: [],
            customers: [],
            sellers: [],
        }),
    },
});

const selected = defineModel({
    type: Object,
    default: () => ({
        competitors: [],
        customers: [],
        sellers: [],
    }),
});

const isOpen = ref(false);
const panelRef = ref(null);
const hasInitialized = ref(false);

useOutsideClick(panelRef, () => {
    if (isOpen.value) isOpen.value = false;
});

watch(
    () => props.options,
    () => {
        if (
            !hasInitialized.value &&
            props.options &&
            Array.isArray(props.options.competitors) &&
            props.options.competitors.length > 0
        ) {
            selected.value.competitors = props.options.competitors
                .map((o) => o?.competitor_id)
                .filter(Boolean);
            selected.value.customers = Array.isArray(props.options.customers)
                ? props.options.customers.map((o) => o?.customer_id).filter(Boolean)
                : [];
            selected.value.sellers = Array.isArray(props.options.sellers)
                ? props.options.sellers.map((o) => o?.seller_id).filter(Boolean)
                : [];
            hasInitialized.value = true;
        }
    },
    { deep: true, immediate: true }
);

const totalOptionsCount = computed(
    () =>
        (Array.isArray(props.options?.competitors) ? props.options.competitors.length : 0) +
        (Array.isArray(props.options?.customers) ? props.options.customers.length : 0) +
        (Array.isArray(props.options?.sellers) ? props.options.sellers.length : 0)
);

const totalSelectedCount = computed(
    () =>
        selected.value.competitors.length +
        selected.value.customers.length +
        selected.value.sellers.length
);

const allSelected = computed(() => totalSelectedCount.value === totalOptionsCount.value);

const toggleAll = () => {
    selected.value = allSelected.value
        ? { competitors: [], customers: [], sellers: [] }
        : {
              competitors: Array.isArray(props.options?.competitors)
                  ? props.options.competitors.map((o) => o?.competitor_id ?? o?.id).filter(Boolean)
                  : [],
              customers: Array.isArray(props.options?.customers)
                  ? props.options.customers.map((o) => o?.customer_id ?? o?.id).filter(Boolean)
                  : [],
              sellers: Array.isArray(props.options?.sellers)
                  ? props.options.sellers.map((o) => o?.seller_id ?? o?.id).filter(Boolean)
                  : [],
          };
};

const isChecked = (group, id) => selected.value[group].includes(id);

const toggle = (group, id) => {
    const arr = selected.value[group];
    selected.value[group] = arr.includes(id) ? arr.filter((x) => x !== id) : [...arr, id];
};

const clearAll = () => {
    selected.value = { competitors: [], customers: [], sellers: [] };
};
</script>

<template>
    <div class="map-filter">
        <Transition name="map-filter-swap" mode="out-in">
            <ActionButton v-if="!isOpen" key="btn" class="my-0" @click.stop="isOpen = true">
                <div class="map-filter__trigger">
                    <div class="chevron__container">
                        <TableIcon />
                    </div>
                    <span>Filter</span>
                    <i class="arrow map-filter__arrow"></i>
                </div>
            </ActionButton>
            <div v-else key="panel" ref="panelRef" class="map-filter__panel" @click.stop>
                <div class="map-filter__header">
                    <h2>Filter</h2>
                    <i class="arrow map-filter__arrow"></i>
                </div>
                <div class="map-filter__content">
                    <div class="map-filter__group">
                        <div class="checkbox-container">
                            <input
                                id="map-filter-all"
                                type="checkbox"
                                :checked="allSelected"
                                @change="toggleAll" />
                            <span class="custom-checkbox"></span>
                            <label for="map-filter-all">Show All</label>
                        </div>
                    </div>
                    <div v-if="props.options.competitors.length > 0" class="map-filter__group">
                        <h3>Competitors</h3>
                        <div
                            v-for="opt in props.options.competitors"
                            :key="`cmp-${opt.competitor_id ?? opt.id}`"
                            class="checkbox-container">
                            <input
                                type="checkbox"
                                :id="`cmp-${opt.competitor_id ?? opt.id}`"
                                :checked="isChecked('competitors', opt.competitor_id ?? opt.id)"
                                @change="toggle('competitors', opt.competitor_id ?? opt.id)" />
                            <span class="custom-checkbox"></span>
                            <label :for="`cmp-${opt.competitor_id ?? opt.id}`">
                                {{ opt.competitor_name ?? opt.label }}
                            </label>
                        </div>
                    </div>
                    <div v-if="props.options.customers.length > 0" class="map-filter__group">
                        <h3>Customers</h3>
                        <div
                            v-for="opt in props.options.customers"
                            :key="`cust-${opt?.customer_id ?? opt?.id}`"
                            class="checkbox-container">
                            <input
                                type="checkbox"
                                :id="`cust-${opt?.customer_id ?? opt?.id}`"
                                :checked="isChecked('customers', opt?.customer_id ?? opt?.id)"
                                @change="toggle('customers', opt?.customer_id ?? opt?.id)" />
                            <span class="custom-checkbox"></span>
                            <label :for="`cust-${opt?.customer_id ?? opt?.id}`">
                                {{ opt?.customer_name ?? opt?.label }}
                            </label>
                        </div>
                    </div>
                    <div v-if="props.options.sellers.length > 0" class="map-filter__group">
                        <h3>Company</h3>
                        <div
                            v-for="opt in props.options.sellers"
                            :key="`seller-${opt?.seller_id ?? opt?.id}`"
                            class="checkbox-container">
                            <input
                                type="checkbox"
                                :id="`seller-${opt?.seller_id ?? opt?.id}`"
                                :checked="isChecked('sellers', opt?.seller_id ?? opt?.id)"
                                @change="toggle('sellers', opt?.seller_id ?? opt?.id)" />
                            <span class="custom-checkbox"></span>
                            <label :for="`seller-${opt?.seller_id ?? opt?.id}`">
                                {{ opt?.seller_name ?? opt?.label }}
                            </label>
                        </div>
                    </div>
                </div>
                <button
                    class="map-filter__clear"
                    :disabled="totalSelectedCount === 0"
                    @click="clearAll">
                    Clear
                </button>
            </div>
        </Transition>
    </div>
</template>

<style lang="sass">
@use '@styles/components/map-filter.sass'
</style>
