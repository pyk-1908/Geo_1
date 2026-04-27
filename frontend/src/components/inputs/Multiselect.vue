<script setup>
import { ref, computed } from "vue";
import { useOutsideClick } from "@composables/general/useOutsideClick";
import DeleteButton from "@components/base/DeleteButton.vue";
import SearchDropdown from "./SearchDropdown.vue";

const props = defineProps({
    displayOption: { type: String },
    options: { type: Array, required: true },
    isDisabled: { type: Boolean, default: false },
    disableHoverEffect: { type: Boolean, default: false },
    hidePlaceholderWhenSelected: { type: Boolean, default: false },
    maxVisibleSelections: { type: Number, default: 1 },
});

const isOpen = ref(false);
const selectedOptions = defineModel();

const visibleSelectedOptions = computed(() =>
    selectedOptions.value?.slice(0, props.maxVisibleSelections) ?? []
);

const hiddenSelectionsCount = computed(() =>
    Math.max(0, (selectedOptions.value?.length ?? 0) - visibleSelectedOptions.value.length)
);

const toggleDropdown = () => {
    if (!props.options.length || props.isDisabled) {
        isOpen.value = false;
        return;
    }
    isOpen.value = !isOpen.value;
};

const toggleOption = (option) => {
    if (!selectedOptions.value) return;
    const index = selectedOptions.value.indexOf(option);
    if (index === -1) {
        selectedOptions.value.push(option);
    } else {
        selectedOptions.value.splice(index, 1);
    }
};

const multiselectRef = ref(null);
useOutsideClick(multiselectRef, () => {
    isOpen.value = false;
});
</script>

<template>
    <div
        ref="multiselectRef"
        class="select"
        :class="{
            selected: selectedOptions?.length,
            selecting: isOpen,
            disabled: !options.length || isDisabled,
            'select--hoverless': disableHoverEffect,
        }">
        <div class="select__summary" @click="toggleDropdown">
            <span
                v-if="!hidePlaceholderWhenSelected || !selectedOptions?.length"
                class="select__placeholder">
                <slot />
            </span>
            <div class="select__selected" v-if="selectedOptions?.length">
                <TransitionGroup name="fade">
                    <span v-for="(option, index) in visibleSelectedOptions" :key="index">
                        {{ displayOption && option ? option[displayOption] : option }}
                        <DeleteButton @click="selectedOptions?.splice(index, 1)" />
                    </span>
                </TransitionGroup>
                <Transition name="fade">
                    <span v-if="hiddenSelectionsCount">+{{ hiddenSelectionsCount }}</span>
                </Transition>
            </div>
            <i class="arrow arrow--select"></i>
        </div>
        <SearchDropdown
            :options="options"
            :displayOption="displayOption"
            @toggle-option="toggleOption($event)"
            @clear-all="selectedOptions = []"
            :selected="selectedOptions ?? []" />
    </div>
</template>

<style scoped lang="sass">
@forward '@styles/components/select.sass'
</style>
