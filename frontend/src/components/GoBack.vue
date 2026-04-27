<script setup>
import ActionButton from "./base/ActionButton.vue";
import ChevronRight from "./icons/ChevronRight.vue";
import { useRouter } from "vue-router";

const router = useRouter();

function goBack() {
    router.back();
}
</script>

<template>
    <div class="go-back">
        <ActionButton @click="goBack">
            <div class="flex-start-gap-10">
                <div class="chevron__container">
                    <ChevronRight class="chevron--back" />
                </div>
                <span>Go Back</span>
            </div>
        </ActionButton>
    </div>
</template>

<style scoped lang="sass">
@use '@styles/utils/_variables' as *

.go-back
    padding-inline: 5vw

.chevron--back
    transform: rotate(180deg)
</style>
