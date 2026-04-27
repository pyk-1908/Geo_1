<script setup>
import { ref } from "vue";
import { useOutsideClick } from "@composables/general/useOutsideClick";
import DeleteButton from "@components/base/DeleteButton.vue";
import SearchDropdown from "./SearchDropdown.vue";

const props = defineProps({
    displayOption: { type: String },
    options: { type: Array, required: true },
    disableHoverEffect: { type: Boolean, default: false },
    clearable: { type: Boolean, default: false },
    hidePlaceholderWhenSelected: { type: Boolean, default: false },
});

const isOpen = ref(false);
const selectedOption = defineModel();

const toggleDropdown = () => {
    isOpen.value = !isOpen.value;
};

const handleSelectOption = (option) => {
    selectedOption.value = option;
    isOpen.value = false;
};

const theSelectRef = ref(null);
useOutsideClick(theSelectRef, () => {
    isOpen.value = false;
});
</script>

<template>
    <div
        ref="theSelectRef"
        class="select"
        :class="{
            selected: selectedOption,
            selecting: isOpen,
            'select--hoverless': disableHoverEffect,
        }">
        <div class="select__summary" @click="toggleDropdown">
            <span
                v-if="!hidePlaceholderWhenSelected || !selectedOption"
                class="select__placeholder">
                <slot />
            </span>
            <div v-if="selectedOption" class="select__selected">
                <Transition name="fade">
                    <span>
                        {{ selectedOption && displayOption ? selectedOption[displayOption] : selectedOption }}
                        <DeleteButton
                            v-if="clearable && selectedOption"
                            @click.stop="selectedOption = null" />
                    </span>
                </Transition>
            </div>
            <i class="arrow arrow--select"></i>
        </div>
        <SearchDropdown
            :options="options"
            :displayOption="displayOption"
            :selected="selectedOption"
            :multiselect="false"
            @toggle-option="handleSelectOption" />
    </div>
</template>

<style scoped lang="sass">
@forward '@styles/components/select.sass'
</style>
