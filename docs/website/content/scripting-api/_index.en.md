---
title: "Automation samples with Python scripts"
description: "A sample of automating VRM-related processes using a Python script."
images: ["images/scripting_api.png"]
---

<!-- TableOfContentsの設定は自動でやりたい -->

- [Importing VRM files](#importing-vrm-files)
- [Exporting VRM files](#exporting-vrm-files)
- [VRM Metadata Settings](#vrm-metadata-settings)
- [VRM Bone Settings](#vrm-bone-settings)
- [VRM MToon Material Settings](#vrm-mtoon-material-settings)
- [Dynamically generate VRM characters and export to file](#dynamically-generate-vrm-characters-and-export-to-file)

## Importing VRM files

```python
import bpy

result = bpy.ops.import_scene.vrm(filepath="path_to_your_vrm_model.vrm")
if result != {"FINISHED"}:
    raise Exception(f"Failed to import vrm: {result}")
```

## Exporting VRM files

```python
import bpy
from pathlib import Path

output_filepath = str(Path.home() / "path_to_your_new_vrm_model.vrm")
result = bpy.ops.export_scene.vrm(filepath=output_filepath)
if result != {"FINISHED"}:
    raise Exception(f"Failed to export vrm: {result}")

print(f"{output_filepath=}")
```

## VRM Metadata Settings

For VRM 1.0

```python
import bpy

context = bpy.context

bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))

armature = context.object
armature.data.vrm_addon_extension.spec_version = "1.0"

meta = armature.data.vrm_addon_extension.vrm1.meta
meta.vrm_name = "Your Model Name"
meta.version = "1.0.0"
meta.authors.add().value = "Author 1"
meta.copyright_information = "Copyright Information"
meta.contact_information = "Contact Information"
meta.references.add().value = "https://example.com"
meta.third_party_licenses = "Third Party Licenses"
thumbnail_image = context.blend_data.images.new(name="New Image", width=32, height=32)
meta.thumbnail_image = thumbnail_image
meta.avatar_permission = "onlyAuthor"  # or "onlySeparatelyLicensedPerson", "everyone"
meta.allow_excessively_violent_usage = False
meta.allow_excessively_sexual_usage = False
meta.commercial_usage = "personalNonProfit"  # or "personalProfit", "corporation"
meta.allow_political_or_religious_usage = False
meta.allow_antisocial_or_hate_usage = False
meta.credit_notation = "required"  # or "unnecessary"
meta.allow_redistribution = False
meta.modification = "prohibited"  # or "allowModification", "allowModificationRedistribution"
meta.other_license_url = ""
```

## VRM Bone Settings

For VRM 1.0

```python
import bpy

context = bpy.context

bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
armature = context.object
armature.data.vrm_addon_extension.spec_version = "1.0"

bpy.ops.object.mode_set(mode="EDIT")

hips_bone = armature.data.edit_bones.new("hips")
hips_bone.head = (0, 0, 0.5)
hips_bone.tail = (0, 0, 0.75)

spine_bone = armature.data.edit_bones.new("spine")
spine_bone.parent = hips_bone
spine_bone.head = (0, 0, 0.75)
spine_bone.tail = (0, 0, 1)

bpy.ops.object.mode_set(mode="OBJECT")

armature.data.vrm_addon_extension.vrm1.humanoid.human_bones.hips.node.bone_name = "hips"
armature.data.vrm_addon_extension.vrm1.humanoid.human_bones.spine.node.bone_name = "spine"
```

## VRM MToon Material Settings

```python
import bpy

context = bpy.context

image = context.blend_data.images.new(name="New Image", width=32, height=32)

material = context.blend_data.materials.new("New MToon Material")
material.vrm_addon_extension.mtoon1.enabled = True

gltf = material.vrm_addon_extension.mtoon1
gltf.pbr_metallic_roughness.base_color_factor = (0, 1, 0, 1)
gltf.pbr_metallic_roughness.base_color_texture.index.source = image

# Similar settings can be made for textures other than "base_color_texture"
gltf.pbr_metallic_roughness.base_color_texture.index.sampler.mag_filter = "NEAREST"  # or "LINEAR"
gltf.pbr_metallic_roughness.base_color_texture.index.sampler.min_filter = "NEAREST"  # or "LINEAR", "NEAREST_MIPMAP_NEAREST", "LINEAR_MIPMAP_NEAREST", "NEAREST_MIPMAP_LINEAR", "LINEAR_MIPMAP_LINEAR"
gltf.pbr_metallic_roughness.base_color_texture.index.sampler.wrap_s = "REPEAT"  # or "CLAMP_TO_EDGE", "MIRRORED_REPEAT"
gltf.pbr_metallic_roughness.base_color_texture.index.sampler.wrap_t = "REPEAT"  # or "CLAMP_TO_EDGE", "MIRRORED_REPEAT"
gltf.pbr_metallic_roughness.base_color_texture.extensions.khr_texture_transform.offset = (0, 0)
gltf.pbr_metallic_roughness.base_color_texture.extensions.khr_texture_transform.scale = (1, 1)

gltf.alpha_mode = "OPAQUE"  # or "MASK", "BLEND"
gltf.double_sided = False
gltf.alpha_cutoff = 0.5
gltf.normal_texture.index.source = image
gltf.normal_texture.scale = 1
gltf.emissive_texture.index.source = image
gltf.emissive_factor = (0, 0, 0)
gltf.extensions.khr_materials_emissive_strength.emissive_strength = 1.0

mtoon = gltf.extensions.vrmc_materials_mtoon
mtoon.transparent_with_z_write = False
mtoon.render_queue_offset_number = 0
mtoon.shade_multiply_texture.index.source = image
mtoon.shade_color_factor = (0, 0, 1)
mtoon.shading_shift_texture.index.source = image
mtoon.shading_shift_texture.scale = 1
mtoon.shading_shift_factor = 0
mtoon.shading_toony_factor = 0
mtoon.gi_equalization_factor = 0
mtoon.matcap_factor = (1, 1, 1)
mtoon.matcap_texture.index.source = image
mtoon.parametric_rim_color_factor = (0, 0, 0)
mtoon.rim_multiply_texture.index.source = image
mtoon.rim_lighting_mix_factor = 0
mtoon.parametric_rim_fresnel_power_factor = 1.0
mtoon.parametric_rim_lift_factor = 1.0
mtoon.outline_width_mode = "worldCoordinates"  # or "none", "screenCoordinates"
mtoon.outline_width_factor = 0.01
mtoon.outline_width_multiply_texture.index.source = image
mtoon.outline_color_factor = (0, 0, 0)
mtoon.outline_lighting_mix_factor = 0
mtoon.uv_animation_mask_texture.index.source = image
mtoon.uv_animation_scroll_x_speed_factor = 0
mtoon.uv_animation_scroll_y_speed_factor = 0
mtoon.uv_animation_rotation_speed_factor = 0
```

## Dynamically generate VRM characters and export to file

![](humanoid.gif)

The script automates the steps in [Create Humanoid VRM]({{< ref "create-humanoid-vrm-from-scratch" >}}) and exports it as a VRM.

```python
import bpy
from pathlib import Path

context = bpy.context

bpy.ops.icyp.make_basic_armature()

armature = context.active_object
armature.data.vrm_addon_extension.spec_version = "1.0"

meta = armature.data.vrm_addon_extension.vrm1.meta
meta.vrm_name = "Your Model Name"
meta.version = "1.0.0"

humanoid = armature.data.vrm_addon_extension.vrm1.humanoid

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25)
head = context.active_object
head.parent = armature
head.parent_bone = humanoid.human_bones.head.node.bone_name
head.parent_type = "BONE"

bpy.ops.mesh.primitive_cube_add(size=0.4)
spine = context.active_object
spine.parent = armature
spine.parent_bone = humanoid.human_bones.spine.node.bone_name
spine.parent_type = "BONE"

bpy.ops.mesh.primitive_ico_sphere_add(radius=0.1)
left_upper_arm = context.active_object
left_upper_arm.parent = armature
left_upper_arm.parent_bone = humanoid.human_bones.left_upper_arm.node.bone_name
left_upper_arm.parent_type = "BONE"

bpy.ops.mesh.primitive_ico_sphere_add(radius=0.1)
left_hand = context.active_object
left_hand.parent = armature
left_hand.parent_bone = humanoid.human_bones.left_hand.node.bone_name
left_hand.parent_type = "BONE"

bpy.ops.mesh.primitive_ico_sphere_add(radius=0.1)
right_upper_arm = context.active_object
right_upper_arm.parent = armature
right_upper_arm.parent_bone = humanoid.human_bones.right_upper_arm.node.bone_name
right_upper_arm.parent_type = "BONE"

bpy.ops.mesh.primitive_ico_sphere_add(radius=0.1)
right_hand = context.active_object
right_hand.parent = armature
right_hand.parent_bone = humanoid.human_bones.right_hand.node.bone_name
right_hand.parent_type = "BONE"

bpy.ops.mesh.primitive_ico_sphere_add(radius=0.1)
left_upper_leg = context.active_object
left_upper_leg.parent = armature
left_upper_leg.parent_bone = humanoid.human_bones.left_upper_leg.node.bone_name
left_upper_leg.parent_type = "BONE"

bpy.ops.mesh.primitive_ico_sphere_add(radius=0.1)
right_upper_leg = context.active_object
right_upper_leg.parent = armature
right_upper_leg.parent_bone = humanoid.human_bones.right_upper_leg.node.bone_name
right_upper_leg.parent_type = "BONE"

bpy.ops.mesh.primitive_ico_sphere_add(radius=0.1)
left_lower_leg = context.active_object
left_lower_leg.parent = armature
left_lower_leg.parent_bone = humanoid.human_bones.left_lower_leg.node.bone_name
left_lower_leg.parent_type = "BONE"

bpy.ops.mesh.primitive_ico_sphere_add(radius=0.1)
right_lower_leg = context.active_object
right_lower_leg.parent = armature
right_lower_leg.parent_bone = humanoid.human_bones.right_lower_leg.node.bone_name
right_lower_leg.parent_type = "BONE"

output_filepath = str(Path.home() / "path_to_your_vrm_model.vrm")
result = bpy.ops.export_scene.vrm(filepath=output_filepath)
if result != {"FINISHED"}:
    raise Exception(f"Failed to export vrm: {result}")

print(f"{output_filepath=}")
```

## Related links

- [Top]({{< ref "/" >}})
