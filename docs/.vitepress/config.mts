import { defineConfig } from "vitepress";

// https://vitepress.dev/reference/site-config
export default defineConfig({
  srcExclude: ["./website/**/*.md"],
  themeConfig: {
    socialLinks: [
      {
        icon: "github",
        link: "https://github.com/saturday06/VRM-Addon-for-Blender",
      },
    ],
  },
  locales: {
    ja: {
      lang: "ja",
      label: "日本語",
      title: "VRM Format / VRM Add-on for Blender",
      description:
        "VRMファイルのインポート・エクスポート・編集機能をBlenderに追加するアドオンです。" +
        "Blender 2.93 から 4.4 をサポートしています。",
      themeConfig: {
        nav: [
          { text: "Home", link: "/ja" },
          { text: "Examples", link: "/ja/markdown-examples" },
        ],
      },
    },
    en: {
      lang: "en",
      label: "English",
      title: "VRM Format / VRM Add-on for Blender",
      description:
        "VRM format adds VRM import, export, and editing capabilities to Blender." +
        " It supports Blender versions 2.93 to 4.4.",
      themeConfig: {
        nav: [
          { text: "Home", link: "/en" },
          { text: "Examples", link: "/en/markdown-examples" },
        ],
      },
    },
  },
});
