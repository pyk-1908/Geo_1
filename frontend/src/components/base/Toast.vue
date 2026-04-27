<script setup lang="ts">
import { useToastStore } from "@stores/toast";

const toast = useToastStore();
</script>

<template>
    <transition name="fade" v-if="toast.visible">
        <div class="custom-toast" :class="toast.status">
            {{ toast.message }}
        </div>
    </transition>
</template>

<style scoped lang="sass">
@use '@styles/utils/_variables' as *

.custom-toast
    position: fixed
    top: 90px
    right: 5vw
    color: $white
    border-radius: 4px
    background: $primary
    padding: 5px 10px
    white-space: pre-line

    &.fail
        background: $red
</style>
