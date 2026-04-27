import { defineStore } from "pinia";
import { ref } from "vue";
import { loginUser, checkMe, logoutUser } from "@services/auth";

export const useAuthStore = defineStore("auth", () => {
    // Import router lazily to avoid calling useRouter() outside a component context
    const getRouter = () => import("@/router/index.js").then((m) => m.default);
    const isLogged = ref<boolean>(false);
    const username = ref<string | null>(localStorage.getItem("username"));

    const login = async (usernameVal: string, password: string) => {
        try {
            const loginResponse = await loginUser(usernameVal, password);

            if (!loginResponse.success) {
                throw new Error(loginResponse.error?.message || loginResponse.error || "Login failed");
            }

            localStorage.setItem("username", loginResponse.data?.username || "");
            username.value = loginResponse.data?.username || null;
            isLogged.value = true;

            return { success: true };
        } catch (error) {
            isLogged.value = false;
            return { success: false, error };
        }
    };

    const logout = async () => {
        try {
            await logoutUser();
        } catch {
            // ignore
        } finally {
            isLogged.value = false;
            username.value = null;
            localStorage.removeItem("username");
            const router = await getRouter();
            router.push({ name: "login" });
        }
    };

    const restoreSession = async () => {
        try {
            const response = await checkMe();
            isLogged.value = !!response?.authenticated;
        } catch {
            isLogged.value = false;
        }
    };

    return {
        isLogged,
        username,
        login,
        logout,
        restoreSession,
    };
});
