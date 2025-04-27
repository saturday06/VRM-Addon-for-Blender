<script setup lang="ts">
const latestVersionName = (import.meta.env.VITE_VRM_ADDON_FOR_BLENDER_LATEST_VERSION_NAME) || "Version Dev";
const latestVersionDateStr = (import.meta.env.VITE_VRM_ADDON_FOR_BLENDER_LATEST_PUBLISH_DATE) || "1000-01-01";
const latestVersionJstUnixDate = Date.parse(latestVersionDateStr) + 9 * 60 * 60 * 1000; // JSTはUTC+9時間
const latestVersionJstDate = new Date(latestVersionJstUnixDate);
</script>

<template>
  <a href="https://vrm-addon-for-blender.info/releases/VRM_Addon_for_Blender-release.zip">
    最新版のダウンロード
    ({{ latestVersionName }})
    {{ latestVersionJstDate.getFullYear() }}年{{ latestVersionJstDate.getMonth() + 1 }}月{{ latestVersionJstDate.getDate() }}日
  </a>
</template>
