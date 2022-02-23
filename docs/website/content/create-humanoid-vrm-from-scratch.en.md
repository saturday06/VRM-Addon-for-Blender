---
title: "Create Humanoid VRM"
description: "VRM Add-on for Blender: Create Humanoid VRM"
---

We will create a simple Humanoid VRM model.

![](../../images/humanoid.gif)

After starting Blender, place the mouse cursor on the 3D Viewport and press the `n` key.

![](../images/humanoid1.png)

This will open a Sidebar from the right side. Select the `VRM` tab and click the `Create VRM Model` button.

![](../images/humanoid2.png)

Then an armature suitable for VRM output will be created automatically. An armature represents the bone structure of a 3D model.
This add-on uses armature to represent the skeletal structure of the human figure in VRM.

![](../images/humanoid3.png)

We will use the default Cube as a torso. Select `Cube` from the `Scene Collection` in the upper right corner, select `Scale:` from `Item` in the sidebar, and set all values to `0.2` to make it small enough to be used as a torso.

![](../images/humanoid4.png)

We associate the torso with the bones of the armature. Select the tab with the square icon in the lower right corner, go to `Relations`, and set `Parent` to `Armature`, `Parent Type` to `Bone`, and `Parent Bone` to `spine`. The torso will move to the spine of the 3D model.

![](../images/humanoid5.png)

The next step is to create the head, press `Shift + A` in the 3D viewport to bring up an additional menu, select `Mesh` -> `UV Sphere`.

![](../images/humanoid6.png)

A `Sphere` will be added.

![](../images/humanoid7.png)

It is too big so we will shrink it. Select the `Sphere` or from the `Scene Collection` in the upper right corner, then select `Scale:` from the `Item` in the sidebar and set all values to `0.25`.

![](../images/humanoid8.png)

Associate this sphere with the armature's bone. Select the tab with the square icon in the lower right corner, go to `Relations`, set `Parent` to `Armature`, set `Parent Type` to `Bone`, and set `Parent Bone` to `head`. The sphere will move to the head of the 3D model.

![](../images/humanoid9.png)

Next, we will add the limbs: in the 3D viewport, press `Shift + A` to bring up the Add menu, and select `Mesh` -> `Ico Sphere`.

![](../images/humanoid10.png)

The `Icosphere` will be added, and at the same time, you will see `> Add Ico Sphere` in the lower-left corner of the 3D viewport. Click on this message.

![](../images/humanoid11.png)

You can then set up the new Ico Sphere to be added. We feel that the radius is too large so we will change the radius value to `0.1 m`.

![](../images/humanoid12.png)

Associate the Ico sphere with the armature bones of the limbs. Select the tab with the square icon in the lower right corner, go to `Relations`, set `Parent` to `Armature`, set `Parent Type` to `Bone`, and set `Parent Bone` to `upper_arm.L`. The sphere will move to the left upper arm of the 3D model.

![](../images/humanoid13.png)

Add the Ico sphere as before, and now associate it with the `hand.L` bone. The Ico sphere will move to the left hand.

![](../images/humanoid14.png)

Similarly, we will associate it with the `upper_arm.R` bone.

![](../images/humanoid15.png)

Associate with the `hand.R` bone.

![](../images/humanoid16.png)

Associate with the `upper_leg.L` bone.

![](../images/humanoid17.png)

Associate with the `lower_leg.L` bone.

![](../images/humanoid18.png)

Associate with the `upper_leg.R` bone.

![](../images/humanoid19.png)

Finally, associate it with the `lower_leg.R` bone.

![](../images/humanoid20.png)

Save this model as a VRM. Select `File` → `Export` → `VRM` from the menu.

![](../images/simple2.png)

Enter the file name and destination when the File View window appears and press `Export VRM`.

![](../images/simple3.png)

If successful, the VRM file will be saved to the specified location.

![](../../images/humanoid.gif)

You can check the operation on this page.

- https://hub.vroid.com/en/characters/4668234592601830916/models/6637924170056429746

## Links

- [Top]({{< ref "/" >}})
- [Create Simple VRM]({{< ref "create-simple-vrm-from-scratch" >}})
