---
title: "Create Anime Style Material"
description: "Set up an anime-style material with MToon shaders."
images: ["images/material_mtoon.gif"]
---

Set an anime-style material to VRM.

![](../../images/material_mtoon.gif)

Please refer to the VRM documentation for detailed configuration items

https://vrm.dev/en/univrm/shaders/shader_mtoon

After starting Blender, delete the cube that is displayed from the beginning. First, select the cube by left-clicking on it.

![](../images/material_pbr1.png)

When selected, the cube will turn orange around it. In this state, press the `x` key on your keyboard.

![](../images/material_pbr2.png)

Press the `Enter` key on the keyboard to confirm the deletion.

![](../images/material_pbr3.png)

If successful, the cube will be deleted.
Next, add a sphere.
With the cursor in the 3D viewport, hold down the `Shift` key on your keyboard and press the `a` key.
The Add Object menu will appear, select `Mesh` → `UV Sphere`.

![](../images/material_mtoon1.png)

Success is indicated when a sphere consisting of a square surface is displayed.

![](../images/material_mtoon2.png)

Next, smooth the surface of this sphere to make it more spherical. Click on the `Object` menu at the top of the screen and select `Shade Smooth` from there.

![](../images/material_mtoon3.png)

It is successful when the corners are removed and the sphere looks like a smooth sphere.

![](../images/material_mtoon4.png)

Next, we can check the color of the material.

With the cursor in the 3D viewport, press the `z` key on the keyboard to bring up the preview display selection menu.
Then move the mouse down and select `Rendered`.

![](../images/material_mtoon5.png)

If successful, the direction of the unlit areas will change. However, there is little change in the display, but note that the coloring is not reflected in the display if the default setting is used.

Next, set the view transformation settings. Select the tab with the "<img src="../../images/scene_property_tab_icon.png">" icon in the lower right corner, then go to `Color Management` and set `View Transform` to `Standard`.

![](../images/material_mtoon6.png)

The sphere will be slightly brighter. If the default is left unchanged, the color displayed will be darker than the specified color.

Next, configure the material settings. Select the tab with the "<img src="../../images/material_property_tab_icon.png">" icon in the lower right corner and press the `New` button.

![](../images/material_mtoon7.png)

A material named `Material.001` will be added. Then scroll down the view and under `VRM Material` check the `Enable VRM MToon Material` checkbox.

![](../images/material_mtoon8.png)

The display color of the sphere turns white and the VRM anime-style material setting item appears.

![](../images/material_mtoon9.png)

As a sample setup, set the following

- Set the `Lit Color, Alpha` to light blue
- Set the `Shade Color` to blue
- Set the `Shading Toony` to 1
- Set the `Shading Shift` to 0

![](../images/material_mtoon10.png)

Scroll the display and set the `Outline` item to `World Coordinates`.

![](../images/material_mtoon11.png)

When the outline settings appear, set the following as a sample setting.

- Set the `Outlien Width` to 0.03
- Set the `Outline Color` to white
- Set the `Outline LightingMix` to 0

![](../images/material_mtoon12.png)

Save this model as a VRM. Select `File` → `Export` → `VRM (.vrm)` from the menu.

![](../images/material_mtoon13.png)

Enter the filename and destination when the File View window appears and press `Export VRM`.

![](../images/material_pbr14.png)

If successful, the VRM file will be saved to the specified location.

![](../../images/material_mtoon.gif)

You can check the operation on this page.

- https://hub.vroid.com/en/characters/2368193253669776229/models/7692418309335351071

## Links

- [Top]({{< ref "/" >}})
- [Create Physics Based Material]({{< ref "material-pbr" >}})
