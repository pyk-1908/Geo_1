<script setup>
import { useId } from "vue";

const props = defineProps({
    isCountryMap: {
        type: Boolean,
        default: false,
    },
    isMarketAttractiveness: {
        type: Boolean,
        default: false,
    },
});

const uniqueId = useId();
</script>

<template>
    <svg
        width="13"
        height="15"
        viewBox="0 0 13 15"
        xmlns="http://www.w3.org/2000/svg"
        class="plants-tooltip__arrow"
        :class="{
            'is-country-map': isCountryMap,
            'is-market-attractiveness': isMarketAttractiveness,
        }"
    >
        <defs>
            <mask :id="uniqueId">
                <rect width="100%" height="100%" fill="white" />
                <rect x="0" y="0" width="4" height="6" fill="black" />
                <rect x="0" y="9" width="4" height="6" fill="black" />
            </mask>
        </defs>

        <path
            d="M0.505859 3.55273
       C0.632378 1.71202 2.68188 0.617255 4.2959 1.5957
       L10.5088 5.36133
       C12.1141 6.33451 12.1141 8.66451 10.5088 9.6377
       L4.2959 13.4043
       C2.62985 14.414 0.5 13.2138 0.5 11.2656
       V3.7334
       L0.505859 3.55273Z"
            fill="#fff"
        />

        <path
            d="M0.505859 3.55273
       C0.632378 1.71202 2.68188 0.617255 4.2959 1.5957
       L10.5088 5.36133
       C12.1141 6.33451 12.1141 8.66451 10.5088 9.6377
       L4.2959 13.4043"
            fill="none"
            stroke="#E3E2E0"
            stroke-linejoin="round"
            stroke-linecap="butt"
            :mask="`url(#${uniqueId})`"
        />
    </svg>
</template>

<style scoped>
.plants-tooltip__arrow {
    position: absolute;
    right: -9px;
    top: 50%;
    transform: translateY(-50%);
    z-index: 0;
}
.plants-tooltip__arrow.is-country-map {
    left: 50%;
    top: -10px;
    transform: translateX(-50%) rotate(-90deg);
}
.plants-tooltip__arrow.is-market-attractiveness {
    left: 50%;
    top: 21px;
    transform: translateX(-50%) rotate(-270deg);
}
</style>
