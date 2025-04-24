// VitePressのドキュメント由来のコードです
// https://github.com/vuejs/vitepress/blob/v1.6.3/docs/en/guide/custom-theme.md?plain=1#L52-L64

import DefaultTheme from "vitepress/theme";
import { EnhanceAppContext, inBrowser } from "vitepress";
import Layout from "./Layout.vue";
import { redirectToLocaleUrlIfNeeded } from "./localization.ts";
import "./custom.css";

export default {
  ...DefaultTheme,
  Layout,
  enhanceApp(enhanceAppContext: EnhanceAppContext) {
    if (!inBrowser) {
      return;
    }
    enhanceAppContext.router.onAfterRouteChange = (_) => {
      redirectToLocaleUrlIfNeeded();
    };
  },
};
