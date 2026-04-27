import "@styles/base/base.sass";
import "@styles/app.sass";
import { createApp } from "vue";
import App from "./App.vue";
import router from "./router/index.js";
import { createPinia } from "pinia";
import { useAuthStore } from "@stores/auth";

// Chunk-load recovery – MUST be before createApp()
let hasReloaded = false;
if (sessionStorage.getItem("chunk_reload")) {
    sessionStorage.removeItem("chunk_reload");
    hasReloaded = true;
}

window.addEventListener("unhandledrejection", (e) => {
    const msg = e?.reason?.message || "";
    if (msg.includes("dynamically imported module") && !hasReloaded) {
        hasReloaded = true;
        sessionStorage.setItem("chunk_reload", "1");
        window.location.reload();
    }
});

const pinia = createPinia();
const app = createApp(App);
app.use(pinia);

const authStore = useAuthStore(pinia);

authStore.restoreSession().finally(() => {
    app.use(router).mount("#app");
});
