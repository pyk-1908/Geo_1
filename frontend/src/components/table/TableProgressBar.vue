<script setup>
import ProgressBar from "@components/base/ProgressBar.vue";
import PointingArrow from "@components/icons/PointingArrow.vue";
import { computed } from "vue";

const props = defineProps({
    value: {
        type: Number,
        required: true,
        default: 0,
    },
    invert_colors: {
        type: Boolean,
        default: false,
    },
    isWithArrow: {
        type: Boolean,
        default: false,
    },
    greenBorder: {
        type: Boolean,
        default: false,
    },
});

const rotate = computed(() => {
    const numberValue = Number(props.value);
    if (numberValue >= 67) {
        return "";
    } else if (numberValue >= 34) {
        return "img-rotate-45";
    } else {
        return "img-rotate-90";
    }
});
</script>

<template>
    <div class="d-flex align-items-center gap-2 justify-content-center" v-if="value">
        <ProgressBar
            :value="value"
            :show-labels="false"
            :is-table="true"
            :isColorInverted="invert_colors" />
        <template v-if="!isWithArrow">
            <div
                :class="['progress__indicator', { 'progress__indicator--green': greenBorder }]">
                <span>{{ value }}</span>
            </div>
        </template>
        <template v-else>
            <div class="progress__indicator progress__indicator--arrow">
                <span>{{ value }}</span>
                <PointingArrow :class="rotate" />
            </div>
        </template>
    </div>
    <div v-else>
        <span class="text--sml">-</span>
    </div>
</template>

<style scoped>
.progress__indicator {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    font-weight: 500;
    min-width: 28px;
}
.img-rotate-45 {
    transform: rotate(45deg);
}
.img-rotate-90 {
    transform: rotate(90deg);
}
</style>
