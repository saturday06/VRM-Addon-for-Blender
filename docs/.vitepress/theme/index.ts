// VitePressのドキュメント由来のコードです
// https://github.com/vuejs/vitepress/blob/v1.6.3/docs/en/guide/custom-theme.md?plain=1#L52-L64

import DefaultTheme from "vitepress/theme";
import { EnhanceAppContext, inBrowser } from "vitepress";
import Layout from "./Layout.vue";
import { redirectToLocaleUrlIfNeeded } from "./localization.ts";
import "./custom.css";
import DownloadLink from "./components/DownloadLink.vue";
import DownloadLinkJa from "./components/DownloadLinkJa.vue";

export default {
  ...DefaultTheme,
  Layout,
  enhanceApp(enhanceAppContext: EnhanceAppContext) {
    enhanceAppContext.app.component("DownloadLink", DownloadLink);
    enhanceAppContext.app.component("DownloadLinkJa", DownloadLinkJa);
    enhanceAppContext.router.onAfterRouteChange = (_) => {
      if (inBrowser) {
        redirectToLocaleUrlIfNeeded(localStorage);
      }
    };
  },
};
