import { defineStore } from "pinia";
import { ref } from "vue";

export const useToastStore = defineStore("toast", () => {
    const message = ref<string>("");
    const visible = ref<boolean>(false);
    const status = ref<"success" | "fail">("success");
    let timeout: ReturnType<typeof setTimeout> | null = null;

    function show(newMessage: string, newStatus: "success" | "fail" = "success", duration = 3000) {
        status.value = newStatus;
        message.value = newMessage;
        visible.value = true;

        if (timeout) {
            clearTimeout(timeout);
        }

        timeout = setTimeout(() => {
            visible.value = false;
            message.value = "";
            timeout = null;
        }, duration);
    }

    return {
        message,
        visible,
        show,
        status,
    };
});
