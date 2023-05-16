---
title: "VRM Add-on for Blender"
description: "VRM Add-on for Blender adds VRM import, export, and editing capabilities to Blender."
images: ["en/images/top.png"]
---

![](images/top.png)

VRM Add-on for Blender adds VRM import, export, and editing capabilities to Blender. It supports Blender version 2.83 or later.

**[Download Latest Version {{< release_utc >}}](https://vrm-addon-for-blender.info/releases/VRM_Addon_for_Blender-release.zip)**<small> / [Past Releases](https://github.com/saturday06/VRM-Addon-for-Blender/releases)</small>

## Tutorials

| [Installation]({{< ref "installation" >}}) | [Create Simple VRM]({{< ref "create-simple-vrm-from-scratch" >}}) | [Create Humanoid VRM]({{< ref "create-humanoid-vrm-from-scratch" >}}) |
| --- | --- | --- |
| [![](../../images/installation.gif)]({{< ref "installation" >}}) | [![](../../images/simple.gif)]({{< ref "create-simple-vrm-from-scratch" >}}) | [![](../../images/humanoid.gif)]({{< ref "create-humanoid-vrm-from-scratch" >}}) |

| [Create Physics Based Material]({{< ref "material-pbr" >}}) | [Create Anime Style Material]({{< ref "material-mtoon" >}}) | |
| --- | --- | --- |
| [![](../../images/material_pbr.gif)]({{< ref "material-pbr" >}}) | [![](../../images/material_mtoon.gif)]({{< ref "material-mtoon" >}}) | ![](../../images/transparent.gif) |

## Import

- Support VRM 0.0, 1.0
- If the "Extract texture images into the folder" option is enabled, the add-on makes a texture folder for each import (max:100,000 character name).

## Edit

- Add VRM Extension Panel
- Add a VRM like shader as Node Group (MToon_unversioned, TransparentZwrite)(Please use these node groups and direct link it to TEX_IMAGE, RGBA, VALUE, and Material output Nodes for export).
- Add a humanoid armature for VRM (T-Pose, Required Bones, and appending custom properties to need export VRM (reference to VRM extensions textblock, and bone tagging))

## Export

- Support VRM 0.0, 1.0
