<script setup>
import UserIcon from "@components/icons/UserIcon.vue";
import { useAttrs } from "vue";

defineOptions({
    inheritAttrs: false,
});

const attrs = useAttrs();
const props = defineProps({
    error: {
        type: String,
        default: "",
    },
});

const model = defineModel();
const emit = defineEmits(["blur"]);
const onBlur = () => emit("blur");
</script>

<template>
    <div class="input__container">
        <div class="input__field" :class="{ 'is-invalid': error, filled: model && model.length }">
            <UserIcon />
            <label :for="attrs.id">
                <slot>Username</slot>
            </label>
            <input v-bind="attrs" v-model="model" @blur="onBlur" />
        </div>
        <div class="error__container">
            <Transition>
                <p v-if="error" class="error__text">{{ error }}</p>
            </Transition>
        </div>
    </div>
</template>
