<script setup>
import { ref, computed, onBeforeUnmount, watch } from "vue";
import { useFloating, offset, shift, flip } from "@floating-ui/vue";
import InfoHoverVisible from "@components/icons/InfoHoverVisible.vue";
import InfoHoverHidden from "@components/icons/InfoHoverHidden.vue";
import ArrowTop from "@components/icons/ArrowTop.vue";

const show = ref(false);
const referenceEl = ref(null);
const floatingEl = ref(null);
const isHoveringReference = ref(false);
const isHoveringPopover = ref(false);
const hideTimeout = ref(null);

const props = defineProps({
    mainAxis: {
        type: Number,
        default: 10,
    },
    crossAxis: {
        type: Number,
        default: 0,
    },
    isSmall: {
        type: Boolean,
        default: false,
    },
    isLarge: {
        type: Boolean,
        default: false,
    },
    isLeft: {
        type: Boolean,
        default: false,
    },
    isOutOfBounds: {
        type: Boolean,
        default: false,
    },
    clickable: {
        type: Boolean,
        default: false,
    },
});

const emit = defineEmits(['click']);

const { floatingStyles } = useFloating(referenceEl, floatingEl, {
    placement: "bottom-end",
    middleware: [
        offset({
            mainAxis: props.mainAxis,
            crossAxis: props.crossAxis,
        }),
        flip(),
        shift({ padding: 8 }),
    ],
});

const teleportTarget = computed(() => {
    show.value;
    const dialog = document.querySelector("dialog[open]");
    if (dialog) {
        const dialogContent = dialog.querySelector(".dialog__content");
        return dialogContent || dialog;
    }
    return "body";
});

const clearHideTimeout = () => {
    if (hideTimeout.value) {
        clearTimeout(hideTimeout.value);
        hideTimeout.value = null;
    }
};

const showPopover = () => {
    clearHideTimeout();
    show.value = true;
};

const hidePopover = () => {
    clearHideTimeout();
    hideTimeout.value = setTimeout(() => {
        if (!isHoveringReference.value && !isHoveringPopover.value) {
            show.value = false;
        }
    }, 40);
};

const handleReferenceEnter = () => {
    isHoveringReference.value = true;
    showPopover();
};

const handleReferenceLeave = () => {
    isHoveringReference.value = false;
    hidePopover();
};

const handlePopoverEnter = () => {
    isHoveringPopover.value = true;
    showPopover();
};

const handlePopoverLeave = () => {
    isHoveringPopover.value = false;
    hidePopover();
};

const handleClick = (event) => {
    if (props.clickable) {
        event.stopPropagation();
        emit('click', event);
    }
};

const handleGlobalMouseMove = (event) => {
    if (!show.value) return;

    const refRect = referenceEl.value?.getBoundingClientRect();
    const floatRect = floatingEl.value?.getBoundingClientRect();

    if (!refRect || !floatRect) return;

    const { clientX, clientY } = event;

    const isOutsideRef =
        clientX < refRect.left ||
        clientX > refRect.right ||
        clientY < refRect.top ||
        clientY > refRect.bottom;

    const isOutsideFloat =
        clientX < floatRect.left ||
        clientX > floatRect.right ||
        clientY < floatRect.top ||
        clientY > floatRect.bottom;

    if (isOutsideRef && isOutsideFloat) {
        isHoveringReference.value = false;
        isHoveringPopover.value = false;
        hidePopover();
    }
};

watch(show, (newVal) => {
    if (newVal) {
        document.addEventListener("mousemove", handleGlobalMouseMove);
    } else {
        document.removeEventListener("mousemove", handleGlobalMouseMove);
    }
});

onBeforeUnmount(() => {
    clearHideTimeout();
    document.removeEventListener("mousemove", handleGlobalMouseMove);
});
</script>

<template>
    <div
        ref="referenceEl"
        class="info-container"
        :class="{
            'info-container--sm': isSmall,
            'info-container--lg': isLarge,
            'info-container--clickable': clickable,
        }"
        @mouseenter="handleReferenceEnter"
        @mouseleave="handleReferenceLeave"
        @click="handleClick">
        <InfoHoverVisible v-if="!show" />
        <InfoHoverHidden v-else />
        <Teleport :to="teleportTarget">
            <Transition name="popover">
                <div
                    v-if="show"
                    ref="floatingEl"
                    class="popover-element"
                    :class="{ 'out-of-bounds': isOutOfBounds }"
                    :style="floatingStyles"
                    @mouseenter="handlePopoverEnter"
                    @mouseleave="handlePopoverLeave"
                    @click.stop>
                    <ArrowTop class="arrow-top" :class="{ left: isLeft }" />
                    <span lang="de">
                        <slot />
                    </span>
                </div>
            </Transition>
        </Teleport>
    </div>
</template>

<style scoped>
.info-container {
    display: inline-block;
    position: relative;
    cursor: pointer;
}
.info-container--sm svg { width: 15px; height: 15px; }
.info-container--lg svg { width: 18px; height: 18px; }
.popover-element {
    position: relative;
    background: rgba(0, 0, 0, 0.8);
    border: thin solid #000;
    color: #fff;
    border-radius: 5px;
    padding: 10px;
    font-size: 14px;
    max-width: 200px;
    z-index: 102;
    pointer-events: auto;
}
.popover-element.out-of-bounds { max-width: 300px; }
.arrow-top {
    position: absolute;
    top: -8px;
    right: 7px;
}
.arrow-top.left { right: auto; left: 7px; }
</style>
