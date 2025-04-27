import { defineConfig } from "vitepress";

// https://vitepress.dev/reference/site-config
export default defineConfig({
  srcExclude: ["./website/**/*.md"],
  sitemap: {
    hostname: "https://vrm-addon-for-blender.info",
  },
  themeConfig: {
    socialLinks: [
      {
        icon: "github",
        link: "https://github.com/saturday06/VRM-Addon-for-Blender",
      },
      {
        icon: "x",
        link: "https://x.com/saturday06",
      },
    ],
    editLink: {
      pattern:
        "https://github.com/saturday06/VRM-Addon-for-Blender/edit/main/docs/:path",
    },
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
          {
            text: "ダウンロード",
            link:
              "https://vrm-addon-for-blender.info/releases/VRM_Addon_for_Blender-release.zip",
          },
          {
            text: "バグを報告",
            link: "https://github.com/saturday06/VRM-Addon-for-Blender/issues",
          },
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
          {
            text: "Download",
            link:
              "https://vrm-addon-for-blender.info/releases/VRM_Addon_for_Blender-release.zip",
          },
          {
            text: "Report Bugs",
            link: "https://github.com/saturday06/VRM-Addon-for-Blender/issues",
          },
        ],
      },
    },
  },
  head: [
    ["link", {
      rel: "apple-touch-icon",
      sizes: "57x57",
      href: "/apple-icon-57x57.png",
    }],
    ["link", {
      rel: "apple-touch-icon",
      sizes: "60x60",
      href: "/apple-icon-60x60.png",
    }],
    ["link", {
      rel: "apple-touch-icon",
      sizes: "72x72",
      href: "/apple-icon-72x72.png",
    }],
    ["link", {
      rel: "apple-touch-icon",
      sizes: "76x76",
      href: "/apple-icon-76x76.png",
    }],
    ["link", {
      rel: "apple-touch-icon",
      sizes: "114x114",
      href: "/apple-icon-114x114.png",
    }],
    ["link", {
      rel: "apple-touch-icon",
      sizes: "120x120",
      href: "/apple-icon-120x120.png",
    }],
    ["link", {
      rel: "apple-touch-icon",
      sizes: "144x144",
      href: "/apple-icon-144x144.png",
    }],
    ["link", {
      rel: "apple-touch-icon",
      sizes: "152x152",
      href: "/apple-icon-152x152.png",
    }],
    ["link", {
      rel: "apple-touch-icon",
      sizes: "180x180",
      href: "/apple-icon-180x180.png",
    }],
    ["link", {
      rel: "icon",
      type: "image/png",
      sizes: "192x192",
      href: "/android-icon-192x192.png",
    }],
    ["link", {
      rel: "icon",
      type: "image/png",
      sizes: "32x32",
      href: "/favicon-32x32.png",
    }],
    ["link", {
      rel: "icon",
      type: "image/png",
      sizes: "96x96",
      href: "/favicon-96x96.png",
    }],
    ["link", {
      rel: "icon",
      type: "image/png",
      sizes: "16x16",
      href: "/favicon-16x16.png",
    }],
  ],
});
