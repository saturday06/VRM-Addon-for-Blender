<script setup lang="ts">
const latestVersionName = (import.meta.env.VITE_VRM_ADDON_FOR_BLENDER_LATEST_VERSION_NAME) || "Version Dev";
const latestVersionDateStr = (import.meta.env.VITE_VRM_ADDON_FOR_BLENDER_LATEST_PUBLISH_DATE) || "1000-01-01";
const latestVersionDate = new Date(latestVersionDateStr);
const latestVersionLocaleDateString = latestVersionDate.toLocaleDateString(
  "ja-JP",
  {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "Asia/Tokyo",
  },
);
</script>

<template>
  <a href="https://vrm-addon-for-blender.info/releases/VRM_Addon_for_Blender-release.zip">
    最新版のダウンロード
    ({{ latestVersionName }})
    {{ latestVersionLocaleDateString }}
  </a>
</template>
