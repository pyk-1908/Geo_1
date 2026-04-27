import { useAuthStore } from "../stores/auth";

function getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem("access_token");
    return {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
}

export async function get(address: string, timeout: number = 15000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
        console.error("Fetch request timed out:", address);
        controller.abort();
    }, timeout);

    try {
        const response = await fetch("/api" + address, {
            method: "GET",
            headers: getAuthHeaders(),
            signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (response.status === 401 || response.status === 429) {
            try {
                const authStore = useAuthStore();
                authStore.isLogged = false;
                localStorage.removeItem("username");
                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");
            } catch {}
            return { success: false, unauthorized: true };
        }

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return await response.json();
    } catch (error: any) {
        console.error("Fetch error:", error.message);
        return { message: error.message, success: false };
    }
}

export async function post(
    address: string,
    body: object,
    method: "POST" | "PUT" | "PATCH" = "POST",
    timeout: number = 10000
) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
        console.error("Fetch request timed out:", address);
        controller.abort();
    }, timeout);

    try {
        const response = await fetch("/api" + address, {
            method,
            headers: getAuthHeaders(),
            body: JSON.stringify(body),
            signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (response.status === 401 || response.status === 429) {
            try {
                const authStore = useAuthStore();
                authStore.isLogged = false;
                localStorage.removeItem("username");
                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");
            } catch {}
            return { success: false, unauthorized: true };
        }

        const contentType = response.headers.get("content-type");
        let data;
        if (contentType && contentType.includes("application/json")) {
            data = await response.json();
        } else {
            return {
                success: false,
                message: `Unexpected response format. Status: ${response.status}`,
            };
        }

        if (!response.ok) {
            return { ...data, success: false };
        }

        return data;
    } catch (error: any) {
        console.error("Fetch error:", error.message);
        return { message: error.message, success: false };
    }
}
