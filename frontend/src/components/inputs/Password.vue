<script setup>
import LockIcon from "@components/icons/LockIcon.vue";
import PasswordVisible from "@components/icons/PasswordVisible.vue";
import PasswordHidden from "@components/icons/PasswordHidden.vue";
import { useAttrs, ref } from "vue";

defineOptions({
    inheritAttrs: false,
});

const model = defineModel();
const emit = defineEmits(["blur"]);
const onBlur = () => emit("blur");
const attrs = useAttrs();

const props = defineProps({
    error: {
        type: String,
        default: "",
    },
});

const isVisible = ref(false);
const toggleVisibility = () => {
    isVisible.value = !isVisible.value;
};
</script>

<template>
    <div class="input__container">
        <div class="input__field" :class="{ 'is-invalid': error, filled: model && model.length }">
            <LockIcon />
            <label :for="attrs.id">
                <slot>Your password</slot>
            </label>
            <input
                v-bind="attrs"
                :type="isVisible ? 'text' : 'password'"
                v-model="model"
                @blur="onBlur" />
            <div class="input__wall">
                <PasswordVisible v-if="isVisible" @click="toggleVisibility" />
                <PasswordHidden v-else @click="toggleVisibility" />
            </div>
        </div>
        <div class="error__container">
            <Transition>
                <p v-if="error" class="error__text">{{ error }}</p>
            </Transition>
        </div>
    </div>
</template>
