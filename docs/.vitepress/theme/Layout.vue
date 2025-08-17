<!--
eslint-disable vue/multi-word-component-names // Cannot be multi-word as it's a fixed name in VitePress

Code derived from VitePress documentation
https://github.com/vuejs/vitepress/blob/v1.6.3/docs/en/guide/i18n.md?plain=1#L90-L107
-->
<script setup lang="ts">

import DefaultTheme from 'vitepress/theme'
import { useData, inBrowser } from 'vitepress'
import { watchEffect } from 'vue'
import { setAutoRedirectionTargetLocaleToStorage } from "./localization.ts";

// https://github.com/vuejs/vitepress/blob/v1.6.4/docs/en/reference/runtime-api.md?plain=1#L40
const { localeIndex } = useData();
watchEffect(() => {
  if (inBrowser) {
    setAutoRedirectionTargetLocaleToStorage(localStorage, localeIndex.value);
  }
})

</script>

<template>
  <DefaultTheme.Layout />
</template>
