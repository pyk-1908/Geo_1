<script setup>
import { computed } from "vue";

const props = defineProps({
    value: {
        type: Number,
        required: true,
        default: 0,
    },
    showLabels: {
        type: Boolean,
        default: true,
    },
    isTable: {
        type: Boolean,
        default: false,
    },
    isRisk: {
        type: Boolean,
        default: false,
    },
    isDisruption: {
        type: Boolean,
        default: false,
    },
    isInverted: {
        type: Boolean,
        default: false,
    },
    isColorInverted: {
        type: Boolean,
        default: false,
    },
});

const progressClass = computed(() => {
    const invertColors = props.isColorInverted ? !props.isInverted : props.isInverted;

    if (props.isRisk || props.isDisruption) {
        if (props.value < 35) return invertColors ? "red" : "green";
        if (props.value < 70) return "yellow";
        return invertColors ? "green" : "red";
    } else {
        if (props.value >= 67) return invertColors ? "red" : "green";
        if (props.value >= 34) return "yellow";
        return invertColors ? "green" : "red";
    }
});

const linePosition = computed(() => {
    return Math.min(Math.max(props.value, 0), 100);
});
</script>

<template>
    <div
        :class="[
            'progress__container',
            {
                'progress__container--table': isTable,
                'progress__container--inverted': isInverted,
            },
        ]">
        <progress
            :class="['progress__bar', progressClass, { 'progress__bar--table': isTable }]"
            :value="value"
            max="100"></progress>
        <span
            :class="['progress__line', progressClass, { 'progress__line--table': isTable }]"
            :style="{
                left: isInverted ? '' : `${Math.max(linePosition, 0.4)}%`,
                right: isInverted ? `${Math.max(linePosition, 0.4)}%` : '',
            }"></span>
        <div v-if="showLabels" class="progress__labels">
            <div class="progress__label">
                <span>{{ isInverted ? "100" : "0" }}</span>
                <span>{{ isInverted ? "Strong" : "Weak" }}</span>
            </div>
            <div class="progress__label">
                <span>{{ isInverted ? "Weak" : "Strong" }}</span>
                <span>{{ isInverted ? "0" : "100" }}</span>
            </div>
        </div>
    </div>
</template>

<style scoped>
.progress__container {
    position: relative;
    display: flex;
    align-items: center;
    gap: 4px;
}
.progress__bar {
    width: 80px;
    height: 8px;
    border-radius: 4px;
    appearance: none;
    -webkit-appearance: none;
}
.progress__bar.green::-webkit-progress-value { background: #00C898; }
.progress__bar.yellow::-webkit-progress-value { background: #F5A623; }
.progress__bar.red::-webkit-progress-value { background: #E53935; }
.progress__bar::-webkit-progress-bar { background: #eee; border-radius: 4px; }
</style>
