---
title: "VRM Add-on for Blender"
description: "VRM Add-on for Blender adds VRM import, export, and editing capabilities to Blender."
images: ["en/images/top.png"]
---

<img src="images/top.png">

**Update 3/13/2022: There is currently a crash when exporting VRM in Blender 3.1.0; <a href="https://developer.blender.org/T96294">this will be fixed in Blender 3.1.1</a>, so please use Blender 3.0.1 or lower versions until then.**

VRM Add-on for Blender adds VRM import, export, and editing capabilities to Blender. It supports Blender version 2.82 or later.

**[Download Latest Version {{< release_utc >}}](https://github.com/saturday06/VRM_Addon_for_Blender/archive/release.zip)**<small> / [Past Releases](https://github.com/saturday06/VRM_Addon_for_Blender/releases)</small>

## Tutorials

| [Installation]({{< ref "installation" >}}) | [Create Simple VRM]({{< ref "create-simple-vrm-from-scratch" >}}) | [Create Humanoid VRM]({{< ref "create-humanoid-vrm-from-scratch" >}}) |
| --- | --- | --- |
| [![](images/installation.png)]({{< ref "installation" >}}) | [![](../../images/simple.gif)]({{< ref "create-simple-vrm-from-scratch" >}}) | [![](../../images/humanoid.gif)]({{< ref "create-humanoid-vrm-from-scratch" >}}) |

## Import

- Support VRM 0.0
- If the "Extract texture images into the folder" option is enabled, the add-on makes a texture folder for each import (max:100,000 character name).

## Edit

- Add VRM Extension Panel
  ![UI Panel](../ja/images/ui_panel.png)
- Add a VRM like shader as Node Group (GLTF, MToon_unversioned, TransparentZwrite)(Please use these node groups and direct link it to TEX_IMAGE, RGBA, VALUE, and Material output Nodes for export).
- Add a humanoid armature for VRM (T-Pose, Required Bones, and appending custom properties to need export VRM (reference to VRM extensions textblock, and bone tagging))

## Export

- Support VRM 0.0

## Tutorials for the legacy version 1.x, 0.x

### Export (Japanese)

https://qiita.com/iCyP/items/61af0ea93c604e37bed6

### In-out-modify video tutorial (Japanese)

https://www.nicovideo.jp/watch/sm36033523
