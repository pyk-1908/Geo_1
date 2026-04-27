import { onMounted, onBeforeUnmount, Ref } from "vue";

type ClickOutsideHandler = (event: MouseEvent) => void;

export function useOutsideClick(
    elementRef: Ref<HTMLElement | null>,
    handler: ClickOutsideHandler
): void {
    const listener = (event: MouseEvent) => {
        const el = elementRef.value;
        if (!el) return;

        if (!el.contains(event.target as Node)) {
            handler(event);
        }
    };

    onMounted(() => {
        document.body.addEventListener("click", listener);
    });

    onBeforeUnmount(() => {
        document.body.removeEventListener("click", listener);
    });
}
