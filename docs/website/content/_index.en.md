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

**[Download Latest Version {{< release_utc >}}](https://vrm-addon-for-blender.info/releases/VRM_Addon_for_Blender-release.zip)**<small> / [Past Releases](https://github.com/saturday06/VRM-Addon-for-Blender/releases)</small>

VRM Add-on for Blender adds VRM import, export, and editing capabilities to Blender. It supports Blender versions 2.93 to 4.0.

## Tutorials

| [Installation]({{< ref "installation" >}}) | [Create Simple VRM]({{< ref "create-simple-vrm-from-scratch" >}}) | [Create Humanoid VRM]({{< ref "create-humanoid-vrm-from-scratch" >}}) |
| --- | --- | --- |
| [![](installation.png)]({{< ref "installation" >}}) | [![](simple.gif)]({{< ref "create-simple-vrm-from-scratch" >}}) | [![](humanoid.gif)]({{< ref "create-humanoid-vrm-from-scratch" >}}) |
| | | |
| [Create Physics Based Material]({{< ref "material-pbr" >}}) | [Create Anime Style Material]({{< ref "material-mtoon" >}}) | [Automation with Python scripts]({{< ref "scripting-api" >}}) |
| [![](material_pbr.gif)]({{< ref "material-pbr" >}}) | [![](material_mtoon.gif)]({{< ref "material-mtoon" >}}) | [![](scripting_api.png)]({{< ref "scripting-api" >}}) |
| [VRM Animation]({{< ref "animation" >}}) | | |
| [![](animation.gif)]({{< ref "animation" >}}) | | |

## Overview

This add-on adds VRM-related functions to Blender, such as importing and exporting VRM, adding VRM Humanoid and setting MToon shaders. Bug reports, feature requests, pull requests, etc. are welcome. I have taken over the development after [Version 0.79](https://github.com/iCyP/VRM_IMPORTER_for_Blender2_8/releases/tag/0.79) from the author, [@iCyP](https://github.com/iCyP).

## Import

- Support VRM 0.0, 1.0

## Edit

- Add VRM Extension Panel
- Add a VRM like shader as Node Group (MToon_unversioned)(Please use these node groups and direct link it to TEX_IMAGE, RGBA, VALUE, and Material output Nodes for export).
- Add a humanoid armature for VRM (T-Pose, Required Bones, and appending custom properties to need export VRM (reference to VRM extensions textblock, and bone tagging))

## Export

- Support VRM 0.0, 1.0
