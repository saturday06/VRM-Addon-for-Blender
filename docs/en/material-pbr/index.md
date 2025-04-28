---
title: "Create Physics Based Material"
description: "Set up physics-based materials using Principled BSDF shaders."
---

Set up realistic physics-based materials for VRM.

![](/assets/images/material_pbr.gif)

In VRM Add-on for Blender, realistic physics-based material settings are handled
exactly the same way as in Blender's glTF 2.0 add-on. Please refer to the
appropriate documentation for more information.

https://docs.blender.org/manual/en/2.93/addons/import_export/scene_gltf2.html#exported-materials

After starting Blender, delete the cube that is displayed from the beginning.
First, select the cube by left-clicking on it.

![](1.png)

When selected, the cube will turn orange around it. In this state, press the `x`
key on your keyboard.

![](2.png)

Press the `Enter` key on the keyboard to confirm the deletion.

![](3.png)

If successful, the cube will be deleted. Next, add a sphere consisting of
triangles. With the cursor in the 3D viewport, hold down the `Shift` key on your
keyboard and press the `a` key. The Add Object menu will appear, select `Mesh` →
`Ico Sphere`.

![](4.png)

If successful, a sphere consisting of triangles is added.

![](5.png)

Next, we can check the color of the material.

With the cursor in the 3D viewport, press the `z` key on the keyboard to bring
up the preview display selection menu. Then move the mouse down and select
`Material Preview`.

![](6.png)

If successful, the grayish color of the display will increase. However, there is
little change, but note that the coloring is not reflected in the display if the
default is used.

![](7.png)

In this state, set the material settings. Select the tab with the
"![](/assets/images/material_property_tab_icon.png)" icon in the lower right
corner and press the `New` button.

![](8.png)

A material named `Material.001` will be added. Also make sure that the `Surface`
setting is set to `Principled BSDF`.

![](9.png)

By setting the `Principled BSDF`, you can configure realistic physics-based
texture settings, which can then be exported directly to VRM.

![](10.png)

Then select `Base Color` and enter blue when the color selection pop-up appears.

![](11.png)

Then set the value of `Metallic` to `0.5`.

![](12.png)

Save this model as a VRM. Select `File` → `Export` → `VRM (.vrm)` from the menu.

![](13.png)

Enter the filename and destination when the File View window appears and press
`Export VRM`.

![](14.png)

If successful, the VRM file will be saved to the specified location.

![](/assets/images/material_pbr.gif)

You can check the operation on this page.

- https://hub.vroid.com/en/characters/3819557420301868457/models/3988362170085862123

## Links

- [Top](../)
- [Create Anime Style Material](../material-mtoon/)
