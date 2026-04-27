export function createElement(type: string, classNames?: string | string[] | null) {
    const el = document.createElement(type);

    if (!classNames) return el;

    if (typeof classNames === "string") {
        if (classNames.trim()) {
            el.classList.add(classNames);
        }
    } else if (Array.isArray(classNames)) {
        const validClassNames = classNames.filter((cls) => cls && typeof cls === "string" && cls.trim());
        if (validClassNames.length > 0) {
            el.classList.add(...validClassNames);
        }
    }

    return el;
}

export const numberSeparator = (price: number) => {
    if (typeof price !== "number") {
        price = Number(price);
    }
    if (isNaN(price)) {
        return 0;
    }

    const roundedPrice = Math.floor(price);
    return roundedPrice.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
};

export const COUNTRY_NAME_ALIASES = new Map<string, string>([
    ["North Macedonia", "Macedonia"],
    ["Bosnia/Herzegovina", "Bosnia and Herz."],
    ["Czech Republic", "Czechia"],
]);

export function normalizeCountryName(name?: string | null): string | null {
    if (typeof name !== "string") return null;
    const trimmed = name.trim();
    return COUNTRY_NAME_ALIASES.get(trimmed) ?? trimmed;
}

