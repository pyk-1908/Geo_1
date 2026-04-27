import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";

export default defineConfig({
    resolve: {
        alias: {
            vue: "vue/dist/vue.esm-bundler.js",
            "@": path.resolve(__dirname, "src"),
            "@src": path.resolve(__dirname, "src"),
            "@pages": path.resolve(__dirname, "src/pages"),
            "@composables": path.resolve(__dirname, "src/composables"),
            "@components": path.resolve(__dirname, "src/components"),
            "@services": path.resolve(__dirname, "src/services"),
            "@types": path.resolve(__dirname, "src/types"),
            "@lib": path.resolve(__dirname, "src/types"),
            "@stores": path.resolve(__dirname, "src/stores"),
            "@utils": path.resolve(__dirname, "src/utils"),
            "@assets": path.resolve(__dirname, "src/assets"),
            "@styles": path.resolve(__dirname, "src/styles"),
        },
    },
    plugins: [
        vue({
            template: {
                transformAssetUrls: {
                    base: null,
                    includeAbsolutePath: false,
                },
            },
        }),
    ],
    server: {
        proxy: {
            "/api": {
                target: "http://localhost:8000",
                changeOrigin: true,
            },
        },
    },
    css: {
        preprocessorOptions: {
            sass: {
                loadPaths: [path.resolve(__dirname, "src/styles")],
            },
        },
    },
});
