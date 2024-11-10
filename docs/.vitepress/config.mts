import { defineConfig } from "vitepress";

// https://vitepress.dev/reference/site-config
export default defineConfig({
    title: "VRM Format / VRM Add-on for Blender",
    description:
        "VRM format adds VRM import, export, and editing capabilities to Blender. It supports Blender versions 2.93 to 4.2.",
    themeConfig: {
        // https://vitepress.dev/reference/default-theme-config
        nav: [
            { text: "Home", link: "/" },
            { text: "Examples", link: "/markdown-examples" },
        ],

        sidebar: [
            {
                text: "Examples",
                items: [
                    { text: "Markdown Examples", link: "/markdown-examples" },
                    { text: "Runtime API Examples", link: "/api-examples" },
                ],
            },
        ],

        socialLinks: [
            {
                icon: "github",
                link: "https://github.com/saturday06/VRM-Addon-for-Blender",
            },
        ],
    },
});
