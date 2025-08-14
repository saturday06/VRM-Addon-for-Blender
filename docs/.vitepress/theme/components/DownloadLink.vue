<script setup lang="ts">
const latestVersionName = (import.meta.env.VITE_VRM_ADDON_FOR_BLENDER_LATEST_VERSION_NAME) || "Version Dev";
const latestVersionDateStr = (import.meta.env.VITE_VRM_ADDON_FOR_BLENDER_LATEST_PUBLISH_DATE) || "1000-01-01";
const latestVersionDate = new Date(latestVersionDateStr);
const latestVersionLocaleDateString = latestVersionDate.toLocaleDateString(
  "en-US",
  {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "Etc/UTC",
  },
);
</script>

<template>
  <a href="https://vrm-addon-for-blender.info/releases/VRM_Addon_for_Blender-release.zip">
    Download Latest Version
    ({{ latestVersionName }})
    {{ latestVersionLocaleDateString }}
    UTC
  </a>
</template>
