<script setup lang="ts">
// VitePressのドキュメント由来のコードです
// https://github.com/vuejs/vitepress/blob/v1.6.3/docs/en/guide/i18n.md?plain=1#L90-L107

import DefaultTheme from 'vitepress/theme'
import { useData, inBrowser } from 'vitepress'
import { watchEffect } from 'vue'
import { registerAutoRedirectionTargetLocale } from "./localization.ts";

const { lang } = useData()
watchEffect(() => {
  if (inBrowser) {
    registerAutoRedirectionTargetLocale(localStorage, lang.value);
  }
})

</script>

<template>
  <DefaultTheme.Layout />
</template>
