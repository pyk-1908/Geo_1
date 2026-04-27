export async function loginUser(
    username: string,
    password: string
): Promise<{
    data?: { username: string };
    error?: any;
    success: boolean;
}> {
    try {
        const response = await fetch("/api/token/pair", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data?.detail || data?.message || "Login failed");
        }

        localStorage.setItem("access_token", data.access);
        localStorage.setItem("refresh_token", data.refresh);

        return { data: { username }, success: true };
    } catch (error) {
        return { error, success: false };
    }
}

export async function logoutUser() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    return { success: true };
}

export async function checkMe(): Promise<{ authenticated: boolean }> {
    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) return { authenticated: false };

    try {
        const response = await fetch("/api/token/refresh", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh: refreshToken }),
        });

        if (!response.ok) {
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
            return { authenticated: false };
        }

        const data = await response.json();
        if (data.access) {
            localStorage.setItem("access_token", data.access);
        }
        return { authenticated: true };
    } catch {
        return { authenticated: false };
    }
}
