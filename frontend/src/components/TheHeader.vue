<script setup>
import logo from "../assets/logo.svg";
import UserIcon from "@components/icons/UserIcon.vue";
import LogoutIcon from "@components/icons/LogoutIcon.vue";
import Dropdown from "@components/base/Dropdown.vue";
import { useAuthStore } from "@stores/auth";
import { useRouter } from "vue-router";

const router = useRouter();
const auth = useAuthStore();

const handleLogout = () => {
    auth.logout().then(() => {
        router.push({ name: "login" });
    });
};
</script>

<template>
    <header class="header">
        <div class="header__content">
            <RouterLink to="/" class="header__logo">
                <img :src="logo" alt="Zopa AI" height="22" />
            </RouterLink>
            <div class="header__links" :class="{ inactive: !auth.isLogged }">
                <RouterLink
                    to="/customer/map"
                    class="link"
                    :class="{ 'router-link-active': $route.path.startsWith('/customer') }">
                    Customer Map
                </RouterLink>
            </div>
            <Dropdown v-if="auth.isLogged">
                <UserIcon />
                <template v-slot:list>
                    <button @click="handleLogout()">
                        <LogoutIcon />
                        Log out
                    </button>
                </template>
            </Dropdown>
            <RouterLink v-else to="/login" class="link button--secondary button--login">
                <UserIcon />
                Log in
            </RouterLink>
        </div>
    </header>
</template>

<style lang="sass" scoped>
@forward '@styles/components/header.sass'
</style>
