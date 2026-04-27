<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@stores/auth";
import { useToastStore } from "@stores/toast";
import { useLoader } from "@composables/general/useLoader";
import { useVuelidate } from "@vuelidate/core";
import { required } from "@vuelidate/validators";
import PasswordInput from "@components/inputs/Password.vue";
import TextInput from "@components/inputs/Text.vue";

const authStore = useAuthStore();
const toast = useToastStore();
const router = useRouter();
const loader = useLoader();
const username = ref("");
const password = ref("");

const rules = {
    username: { required },
    password: { required },
};

const v$ = useVuelidate(rules, { username, password });

const handleSubmit = async (e) => {
    e.preventDefault();

    const result = await v$.value.$validate();
    if (!result) {
        toast.show("Please fill in all required fields", "fail");
        return;
    }

    loader.show();
    try {
        const loginResponse = await authStore.login(username.value, password.value);
        if (loginResponse.error) {
            toast.show(loginResponse.error.message || loginResponse.error, "fail");
            return;
        }
        if (loginResponse.success) {
            toast.show("You have been successfully logged in", "success");
            await router.push({ name: "customer.map" });
        }
    } catch (error) {
        toast.show(error.message, "fail");
    } finally {
        loader.hide();
    }
};
</script>

<template>
    <section class="auth-page">
        <div class="auth-page__inner">
            <h1 class="text--center">Log into your account</h1>
            <form @submit="handleSubmit">
                <TextInput
                    v-model="username"
                    type="text"
                    required
                    id="username"
                    name="username"
                    @blur="v$.username.$touch()"
                    :error="v$.username.$error ? 'The field is required' : ''">
                    Username
                </TextInput>
                <PasswordInput
                    v-model="password"
                    id="password"
                    name="password"
                    @blur="v$.password.$touch()"
                    :error="v$.password.$error ? 'Password is required' : ''" />
                <div
                    class="button__container"
                    :class="{
                        'mt-0': v$.password.$error,
                        'button__container--disabled': v$.$invalid,
                    }">
                    <button
                        type="submit"
                        :class="v$.$invalid ? 'button--disabled' : 'button--primary'"
                        :disabled="v$.$invalid">
                        Log in
                    </button>
                </div>
            </form>
        </div>
    </section>
</template>

<style lang="sass" scoped>
@forward '@styles/pages/auth'
</style>
