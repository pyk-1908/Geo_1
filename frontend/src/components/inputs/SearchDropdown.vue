<script setup>
import { ref, computed } from "vue";

const props = defineProps({
    options: Array,
    selected: [Array, Object],
    displayOption: String,
    multiselect: {
        type: Boolean,
        default: true,
    },
});

const emit = defineEmits(["toggle-option", "clear-all"]);
const searchQuery = ref("");

const filteredOptions = computed(() => {
    if (!Array.isArray(props.options)) return [];
    if (!searchQuery.value) return props.options;
    return props.options.filter((option) => {
        if (!option) return false;
        const value = props.displayOption ? option[props.displayOption] : option;
        if (value == null) return false;
        return String(value).toLowerCase().includes(searchQuery.value.toLowerCase());
    });
});

const toggle = (option) => emit("toggle-option", option);

const toggleAll = () => {
    if (!Array.isArray(props.options)) return;
    props.options.forEach((option) => {
        if (option && !props.selected.includes(option)) {
            toggle(option);
        }
    });
};

const clearAll = () => emit("clear-all");
</script>

<template>
    <TransitionGroup tag="ul" class="search__dropdown">
        <li class="search__dropdown__sticky" key="search-input">
            <input
                type="text"
                class="select__search"
                v-model="searchQuery"
                placeholder="Search..." />
        </li>
        <li v-if="multiselect" class="search__dropdown__option dropdown__option--actions">
            <label
                class="dropdown__option--select-all"
                @click.stop="toggleAll"
                :class="{ selected: props.selected.length == filteredOptions.length }">
                <span>Select All</span>
                <input
                    v-if="multiselect"
                    type="checkbox"
                    :checked="props.selected.length == filteredOptions.length" />
            </label>
            <Transition name="fade">
                <button v-if="props.selected.length" class="button button--clear" @click="clearAll">
                    Clear All
                </button>
            </Transition>
        </li>
        <li
            v-for="(option, index) in filteredOptions"
            :key="option + '--' + index"
            class="search__dropdown__option"
            :class="{
                selected: multiselect ? props.selected.includes(option) : selected == option,
            }"
            @click.stop="toggle(option)">
            <input v-if="multiselect" type="checkbox" :checked="props.selected.includes(option)" />
            <input
                v-else
                type="radio"
                :name="displayOption"
                :checked="props.selected?.[displayOption] == option?.[displayOption]" />
            <span>{{ displayOption && option ? option[displayOption] : option }}</span>
        </li>
    </TransitionGroup>
</template>

<style scoped lang="sass">
@forward '@styles/components/select.sass'

.search__dropdown__sticky
    position: sticky
    top: 0
    z-index: 1
</style>
