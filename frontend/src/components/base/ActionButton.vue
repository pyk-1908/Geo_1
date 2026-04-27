<template>
    <button class="action__button">
        <slot />
    </button>
</template>

<style scoped lang="sass">
@use '@styles/utils/_variables' as *
@use '@styles/utils/_mixins' as *

.action__button
    max-width: 120px
    border: thin solid $dark-3
    border-radius: 10px
    padding: 10px
    margin-block: 20px
    background: $white
    @include transition(border, box-shadow, translate)

    &:hover
        border-color: $primary
        @include activeShadow
        translate: 0 -2px

    :slotted(span)
        font-size: $size-14
</style>
