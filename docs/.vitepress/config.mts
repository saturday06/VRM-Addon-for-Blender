import {
  Awaitable,
  defineConfig,
  HeadConfig,
  TransformContext,
} from "vitepress";

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "VRM Format / VRM Add-on for Blender",
  locales: {
    en: {
      lang: "en",
      label: "English",
      description:
        "VRM format adds VRM import, export, and editing capabilities to Blender." +
        " It supports Blender versions 2.93 to 4.5.",
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
        sidebar: [
          {
            text: "Top",
            items: [
              {
                items: [
                  { text: "Top Page", link: "/en/" },
                ],
              },
            ],
          },
          {
            text: "Tutorials",
            items: [
              {
                items: [
                  { text: "Installation", link: "/en/installation/" },
                  {
                    text: "Create Simple VRM",
                    link: "/en/create-simple-vrm-from-scratch/",
                  },
                  {
                    text: "Create Humanoid VRM",
                    link: "/en/create-humanoid-vrm-from-scratch/",
                  },
                  {
                    text: "Create Physics Based Material",
                    link: "/en/material-pbr/",
                  },
                  {
                    text: "Create Anime Style Material",
                    link: "/en/material-mtoon/",
                  },
                  { text: "VRM Animation", link: "/en/animation/" },
                  {
                    text: "Automation with Python scripts",
                    link: "/en/scripting-api/",
                  },
                  { text: "Development How-To", link: "/en/development/" },
                ],
              },
            ],
          },
        ],
      },
    },
    ja: {
      lang: "ja",
      label: "日本語",
      description:
        "VRMファイルのインポート・エクスポート・編集機能をBlenderに追加するアドオンです。" +
        "Blender 2.93 から 4.5 をサポートしています。",
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
        sidebar: [
          {
            text: "トップ",
            items: [
              {
                items: [
                  { text: "トップページ", link: "/ja/" },
                ],
              },
            ],
          },
          {
            text: "チュートリアル",
            items: [
              {
                items: [
                  { text: "アドオンのインストール", link: "/ja/installation/" },
                  {
                    text: "シンプルなVRMモデルを作る",
                    link: "/ja/create-simple-vrm-from-scratch/",
                  },
                  {
                    text: "人型のVRMモデルを作る",
                    link: "/ja/create-humanoid-vrm-from-scratch/",
                  },
                  {
                    text: "物理ベースのマテリアル設定",
                    link: "/ja/material-pbr/",
                  },
                  {
                    text: "アニメ風のマテリアル設定",
                    link: "/ja/material-mtoon/",
                  },
                  { text: "VRMアニメーション", link: "/ja/animation/" },
                  {
                    text: "Pythonスクリプトによる自動化",
                    link: "/ja/scripting-api/",
                  },
                  { text: "改造するには", link: "/ja/development/" },
                ],
              },
            ],
          },
        ],
      },
    },
  },
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
  head: [
    [
      "script",
      {
        async: "",
        src: "https://www.googletagmanager.com/gtag/js?id=G-L4E126M2JR",
      },
    ],
    [
      "script",
      {},
      `
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());

        gtag('config', 'G-L4E126M2JR');
      `,
    ],
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

  transformHead(context: TransformContext): Awaitable<HeadConfig[]> {
    // Generate og:image path from article path
    // There is no good way to do this, and an issue has been raised
    // https://github.com/vuejs/vitepress/issues/3161
    const pathComponents = context.pageData.relativePath.split("/");
    const _filePath = pathComponents.pop();
    const parentPath = pathComponents.pop();
    let ogImagePath;
    if (parentPath) {
      for (const asset of context.assets) {
        const assetName = asset.split("/").pop();
        if (!assetName) {
          continue;
        }
        if (
          assetName.startsWith(parentPath.replaceAll("-", "_") + ".") &&
          assetName.endsWith(".gif")
        ) {
          ogImagePath = asset;
          break;
        }
      }
    }
    if (!ogImagePath) {
      ogImagePath = "/logo.png";
    }

    return [
      ["meta", { property: "og:image", content: ogImagePath }],
    ];
  },
});
