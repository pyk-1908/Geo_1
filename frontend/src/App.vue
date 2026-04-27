<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import TheHeader from "@components/TheHeader.vue";
import StickyFilters from "@components/StickyFilters.vue";
import Toast from "@components/base/Toast.vue";

const route = useRoute();
const isAuthPage = computed(() => route.meta.type === "auth");
</script>

<template>
    <TheHeader v-if="!isAuthPage" />
    <main>
        <RouterView v-slot="{ Component }">
            <transition name="fade">
                <component :is="Component" />
            </transition>
        </RouterView>
        <StickyFilters v-if="!isAuthPage" />
    </main>
    <Toast />
</template>
