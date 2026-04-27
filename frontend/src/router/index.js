import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@stores/auth";

const routes = [
    {
        path: "/login",
        name: "login",
        component: () => import("@pages/auth/Login.vue"),
        meta: {
            title: "Login",
            type: "auth",
        },
    },
    {
        path: "/customer/:customerId?/map/:countryName?/:countryId?",
        name: "customer.map",
        component: () => import("@pages/CustomerCountryMap.vue"),
        meta: {
            title: "Customer Map",
            breadcrumbs: () => [
                { label: "Customer Map", to: "" },
            ],
        },
    },
{
        path: "/",
        redirect: "/customer/map",
    },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

// Auth middleware
router.beforeEach((to, from, next) => {
    const authStore = useAuthStore();
    const authPages = ["login"];
    const isAuthenticated = authStore.isLogged;

    window.scroll({ top: 0 });
    document.title = "SalesIQ | " + (to.meta.title || "Customer Map");

    if (!isAuthenticated && !authPages.includes(to.name)) {
        next({ name: "login" });
    } else if (isAuthenticated && to.name === "login") {
        next({ name: "customer.map" });
    } else {
        next();
    }
});

export default router;
