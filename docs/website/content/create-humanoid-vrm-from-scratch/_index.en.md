---
title: "Create Humanoid VRM"
description: "We will create a simple Humanoid VRM model."
images: ["images/humanoid.gif"]
---

We will create a simple Humanoid VRM model.

![](humanoid.gif)

After starting Blender, place the mouse cursor on the 3D Viewport and press the `n` key.

![](1.en.png)

This will open a Sidebar from the right side. Select the `VRM` tab and click the `Create VRM Model` button.

![](2.en.png)

Then an armature suitable for VRM output will be created automatically. An armature represents the bone structure of a 3D model.
This add-on uses armature to represent the skeletal structure of the human figure in VRM.

![](3.en.png)

We will use the default Cube as a torso.

Select the Cube in the 3D Viewport, select the tab with the "![](object_property_tab_icon.png)" icon in the lower right corner, go to `Transform` > `Scale`, and set all values to `0.2` to make it small enough to be used as a torso.

![](4.en.png)

We associate the torso with the bones of the armature. Go to `Relations`, and set `Parent` to `Armature`, `Parent Type` to `Bone`, and `Parent Bone` to `spine`. The torso will move to the spine of the 3D model.

![](5.en.png)

The next step is to create the head, press `Shift + a` in the 3D viewport to bring up an additional menu, select `Mesh` -> `UV Sphere`.

![](6.en.png)

A `Sphere` will be added.

![](7.en.png)

It is too big so we will shrink it.

Select the tab with the "![](object_property_tab_icon.png)" icon in the lower right corner, go to `Transform` > `Scale`, and set all values to `0.25`.

![](8.en.png)

Associate this sphere with the armature's bone. Go to `Relations`, and set `Parent` to `Armature`, `Parent Type` to `Bone`, and `Parent Bone` to `head`. The sphere will move to the head of the 3D model.

![](9.en.png)

Next, we will add the limbs: in the 3D viewport, press `Shift + a` to bring up the Add menu, and select `Mesh` -> `Ico Sphere`.

![](10.en.png)

The `Icosphere` will be added, and at the same time, you will see `> Add Ico Sphere` in the lower-left corner of the 3D viewport. Click on this message.

![](11.en.png)

You can then set up the new Ico Sphere to be added. We feel that the radius is too large so we will change the radius value to `0.1 m`.

![](12.en.png)

Select the tab with the "![](object_property_tab_icon.png)" icon in the lower right corner, go to `Relations`, set `Parent` to `Armature`, set `Parent Type` to `Bone`, and set `Parent Bone` to `upper_arm.L`. The sphere will move to the left upper arm of the 3D model.

![](13.en.png)

Add the Ico sphere as before, and now associate it with the `hand.L` bone. The Ico sphere will move to the left hand.

![](14.en.png)

Similarly, we will associate it with the `upper_arm.R` bone.

![](15.en.png)

Associate with the `hand.R` bone.

![](16.en.png)

Associate with the `upper_leg.L` bone.

![](17.en.png)

Associate with the `lower_leg.L` bone.

![](18.en.png)

Associate with the `upper_leg.R` bone.

![](19.en.png)

Finally, associate it with the `lower_leg.R` bone.

![](20.en.png)

Save this model as a VRM. Select `File` → `Export` → `VRM (.vrm)` from the menu.

![](21.en.png)

Enter the filename and destination when the File View window appears and press `Export VRM`.

![](22.en.png)

If successful, the VRM file will be saved to the specified location.

![](humanoid.gif)

You can check the operation on this page.

- https://hub.vroid.com/en/characters/6595382014094436897/models/1372267393572384142

## Links

- [Top]({{< ref "/" >}})
- [Create Simple VRM]({{< ref "create-simple-vrm-from-scratch" >}})
