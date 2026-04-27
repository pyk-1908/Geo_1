<script setup>
import { ref } from "vue";
import { useOutsideClick } from "@composables/general/useOutsideClick";

const emit = defineEmits(["item-clicked"]);

const dropdownRef = ref(null);
const isOpened = ref(false);

useOutsideClick(dropdownRef, () => {
    isOpened.value = false;
});

const handleListClick = (event) => {
    emit("item-clicked", event);
};

defineExpose({
    isOpened,
});
</script>

<template>
    <div
        class="dropdown"
        :class="{ 'dropdown--dropped': isOpened }"
        @click.stop
        ref="dropdownRef">
        <div class="dropdown__summary" @click="isOpened = !isOpened">
            <slot></slot>
            <i class="arrow"></i>
        </div>
        <div class="dropdown__list" @click="handleListClick">
            <slot name="list"></slot>
        </div>
    </div>
</template>

<style lang="sass">
@forward '@styles/components/dropdown.sass'
</style>
