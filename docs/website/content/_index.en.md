---
title: "VRM Add-on for Blender"
description: "VRM Add-on for Blender adds VRM import, export, and editing capabilities to Blender."
images: ["en/top.en.png"]
---

<style>
main header {
  display: none;
}

main article.prose section :where(p, img):not(:where([class~=not-prose] *)) {
  margin-top: 0;
}
</style>

![](top.en.png)

VRM Add-on for Blender adds VRM import, export, and editing capabilities to Blender. It supports Blender versions 2.93 to 4.3.

## Download

- For Blender 4.2 or later, please download from [**Blender Extensions Platform**](https://extensions.blender.org/add-ons/vrm).
- For Blender 2.93 to 4.1: **[Download Latest Version {{< release_utc >}}](https://vrm-addon-for-blender.info/releases/VRM_Addon_for_Blender-release.zip)** \
  <small>[Past Releases](https://github.com/saturday06/VRM-Addon-for-Blender/releases)</small>

## Tutorials

| [Installation]({{< ref "installation" >}})                  | [Create Simple VRM]({{< ref "create-simple-vrm-from-scratch" >}}) | [Create Humanoid VRM]({{< ref "create-humanoid-vrm-from-scratch" >}}) |
| ----------------------------------------------------------- | ----------------------------------------------------------------- | --------------------------------------------------------------------- |
| [![](installation.gif)]({{< ref "installation" >}})         | [![](simple.gif)]({{< ref "create-simple-vrm-from-scratch" >}})   | [![](humanoid.gif)]({{< ref "create-humanoid-vrm-from-scratch" >}})   |
|                                                             |                                                                   |                                                                       |
| [Create Physics Based Material]({{< ref "material-pbr" >}}) | [Create Anime Style Material]({{< ref "material-mtoon" >}})       | [Automation with Python scripts]({{< ref "scripting-api" >}})         |
| [![](material_pbr.gif)]({{< ref "material-pbr" >}})         | [![](material_mtoon.gif)]({{< ref "material-mtoon" >}})           | [![](scripting_api.gif)]({{< ref "scripting-api" >}})                 |
| [VRM Animation]({{< ref "animation" >}})                    | [Development How-To]({{< ref "development" >}})                   |                                                                       |
| [![](animation.gif)]({{< ref "animation" >}})               | [![](animation.gif)]({{< ref "development" >}})                   |                                                                       |

## Overview

This add-on adds VRM-related functions to Blender, such as importing and exporting VRM, adding VRM Humanoid and setting MToon shaders. Bug reports, feature requests, pull requests, etc. are welcome. I have taken over the development after [Version 0.79](https://github.com/iCyP/VRM_IMPORTER_for_Blender2_8/releases/tag/0.79) from the author, [@iCyP](https://github.com/iCyP).
