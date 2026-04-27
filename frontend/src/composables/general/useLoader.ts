import { createElement } from "../../utils/utils";

export function useLoader() {
    function show(target?: string | null, text?: string | null) {
        const loaderContainer = createElement("div", "loader-container");
        const loaderWrapper = createElement("div", "loader-wrapper");
        const loaderElement = createElement("i", "loader");
        loaderWrapper.appendChild(loaderElement);

        if (text) {
            const loaderText = createElement("span", "loader-text");
            loaderText.textContent = text;
            loaderWrapper.appendChild(loaderText);
        }

        loaderContainer.appendChild(loaderWrapper);

        let targetHtml: HTMLElement | Element[] = (() => {
            if (target && typeof target === "string") {
                return [...document.querySelectorAll(target)];
            }
            return document.body;
        })();

        if (!targetHtml) {
            targetHtml = document.body;
        }

        if (Array.isArray(targetHtml)) {
            targetHtml.forEach((target) => {
                let loaderContainerCopy = loaderContainer.cloneNode(true);
                target.appendChild(loaderContainerCopy);
            });
        } else {
            targetHtml.appendChild(loaderContainer);
        }
        return loaderContainer;
    }

    function hide() {
        document.querySelectorAll(`.loader-container`).forEach((loader) => loader.remove());
    }

    return {
        show,
        hide,
    };
}
