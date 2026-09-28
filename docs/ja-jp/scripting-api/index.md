---
title: "Pythonスクリプトによる自動化サンプル"
description: "Pythonスクリプトを利用してVRM関連処理を自動化するサンプルです。"
---

Pythonスクリプトを利用してVRM関連処理を自動化するサンプルです。

![](/assets/images/scripting_api.gif)

## VRMファイルのインポート

```python
import bpy

result = bpy.ops.import_scene.vrm(filepath="path_to_your_vrm_model.vrm")
if result != {"FINISHED"}:
    raise Exception(f"Failed to import vrm: {result}")
```

## VRMファイルのエクスポート

```python
import bpy
from pathlib import Path

output_filepath = str(Path.home() / "path_to_your_new_vrm_model.vrm")
result = bpy.ops.export_scene.vrm(filepath=output_filepath)
if result != {"FINISHED"}:
    raise Exception(f"Failed to export vrm: {result}")

print(f"{output_filepath=}")
```

## VRMメタデータの設定

VRM 1.0のモデルを想定します。

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
meta.modification = (
    "prohibited"  # or "allowModification", "allowModificationRedistribution"
)
meta.other_license_url = ""
```

## VRMヒューマンボーンの設定

VRM 1.0のモデルを想定します。

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
armature.data.vrm_addon_extension.vrm1.humanoid.human_bones.spine.node.bone_name = (
    "spine"
)
```

## VRM MToonマテリアルの値を設定

```python
import bpy

context = bpy.context

image = context.blend_data.images.new(name="New Image", width=32, height=32)

material = context.blend_data.materials.new("New MToon Material")
material.vrm_addon_extension.mtoon1.enabled = True

gltf = material.vrm_addon_extension.mtoon1
gltf.pbr_metallic_roughness.base_color_factor = (0, 1, 0, 1)
gltf.pbr_metallic_roughness.base_color_texture.index.source = image

# base_color_texture以外のテクスチャにも同様の設定が可能
gltf.pbr_metallic_roughness.base_color_texture.index.sampler.mag_filter = (
    "NEAREST"  # or "LINEAR"
)
gltf.pbr_metallic_roughness.base_color_texture.index.sampler.min_filter = "NEAREST"  # or "LINEAR", "NEAREST_MIPMAP_NEAREST", "LINEAR_MIPMAP_NEAREST", "NEAREST_MIPMAP_LINEAR", "LINEAR_MIPMAP_LINEAR"
gltf.pbr_metallic_roughness.base_color_texture.index.sampler.wrap_s = (
    "REPEAT"  # or "CLAMP_TO_EDGE", "MIRRORED_REPEAT"
)
gltf.pbr_metallic_roughness.base_color_texture.index.sampler.wrap_t = (
    "REPEAT"  # or "CLAMP_TO_EDGE", "MIRRORED_REPEAT"
)
gltf.pbr_metallic_roughness.base_color_texture.extensions.khr_texture_transform.offset = (
    0,
    0,
)
gltf.pbr_metallic_roughness.base_color_texture.extensions.khr_texture_transform.scale = (
    1,
    1,
)

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

## VRMのキャラクターを動的に生成しファイルにエクスポート

![](/assets/images/humanoid.gif)

[人型のVRMモデルを作る](../create-humanoid-vrm-from-scratch/)の手順をスクリプトで自動化し、VRMとしてエクスポートします。

```python
from pathlib import Path

import bpy

# 初期化

if bpy.app.module:
    bpy.ops.preferences.addon_enable(module="io_scene_vrm")

# アーマチュアを作成

armature_data = bpy.data.armatures.new("Armature")
armature_object = bpy.data.objects.new("Armature", armature_data)
bpy.context.scene.collection.objects.link(armature_object)
bpy.context.view_layer.objects.active = armature_object

bpy.ops.object.mode_set(mode="EDIT")

hips_bone = armature_data.edit_bones.new("hips")
hips_bone.head = (0, 0, 0.5)
hips_bone.tail = (0, 1, 0.5)
hips_bone_name = hips_bone.name

right_upper_leg_bone = armature_data.edit_bones.new("upper_leg.R")
right_upper_leg_bone.head = (-0.125, 0, 0.5)
right_upper_leg_bone.tail = (-0.125, 1, 0.5)
right_upper_leg_bone.parent = hips_bone
right_upper_leg_bone_name = right_upper_leg_bone.name

right_lower_leg_bone = armature_data.edit_bones.new("lower_leg.R")
right_lower_leg_bone.head = (-0.125, 0, 0.25)
right_lower_leg_bone.tail = (-0.125, 1, 0.25)
right_lower_leg_bone.parent = right_upper_leg_bone
right_lower_leg_bone_name = right_lower_leg_bone.name

right_foot_bone = armature_data.edit_bones.new("foot.R")
right_foot_bone.head = (-0.125, 0, 0)
right_foot_bone.tail = (-0.125, 1, 0)
right_foot_bone.parent = right_lower_leg_bone
right_foot_bone_name = right_foot_bone.name

left_upper_leg_bone = armature_data.edit_bones.new("upper_leg.L")
left_upper_leg_bone.head = (0.125, 0, 0.5)
left_upper_leg_bone.tail = (0.125, 1, 0.5)
left_upper_leg_bone.parent = hips_bone
left_upper_leg_bone_name = left_upper_leg_bone.name

left_lower_leg_bone = armature_data.edit_bones.new("lower_leg.L")
left_lower_leg_bone.head = (0.125, 0, 0.25)
left_lower_leg_bone.tail = (0.125, 1, 0.25)
left_lower_leg_bone.parent = left_upper_leg_bone
left_lower_leg_bone_name = left_lower_leg_bone.name

left_foot_bone = armature_data.edit_bones.new("foot.L")
left_foot_bone.head = (0.125, 0, 0)
left_foot_bone.tail = (0.125, 1, 0)
left_foot_bone.parent = left_lower_leg_bone
left_foot_bone_name = left_foot_bone.name

spine_bone = armature_data.edit_bones.new("spine")
spine_bone.head = (0, 0, 0.625)
spine_bone.tail = (0, 1, 0.625)
spine_bone.parent = hips_bone
spine_bone_name = spine_bone.name

right_upper_arm_bone = armature_data.edit_bones.new("upper_arm.R")
right_upper_arm_bone.head = (-0.125, 0, 0.75)
right_upper_arm_bone.tail = (-0.125, 1, 0.75)
right_upper_arm_bone.parent = spine_bone
right_upper_arm_bone_name = right_upper_arm_bone.name

right_lower_arm_bone = armature_data.edit_bones.new("lower_arm.R")
right_lower_arm_bone.head = (-0.25, 0, 0.75)
right_lower_arm_bone.tail = (-0.25, 1, 0.75)
right_lower_arm_bone.parent = right_upper_arm_bone
right_lower_arm_bone_name = right_lower_arm_bone.name

right_hand_bone = armature_data.edit_bones.new("hand.R")
right_hand_bone.head = (-0.375, 0, 0.75)
right_hand_bone.tail = (-0.375, 1, 0.75)
right_hand_bone.parent = right_lower_arm_bone
right_hand_bone_name = right_hand_bone.name

left_upper_arm_bone = armature_data.edit_bones.new("upper_arm.L")
left_upper_arm_bone.head = (0.125, 0, 0.75)
left_upper_arm_bone.tail = (0.125, 1, 0.75)
left_upper_arm_bone.parent = spine_bone
left_upper_arm_bone_name = left_upper_arm_bone.name

left_lower_arm_bone = armature_data.edit_bones.new("lower_arm.L")
left_lower_arm_bone.head = (0.25, 0, 0.75)
left_lower_arm_bone.tail = (0.25, 1, 0.75)
left_lower_arm_bone.parent = left_upper_arm_bone
left_lower_arm_bone_name = left_lower_arm_bone.name

left_hand_bone = armature_data.edit_bones.new("hand.L")
left_hand_bone.head = (0.375, 0, 0.75)
left_hand_bone.tail = (0.375, 1, 0.75)
left_hand_bone.parent = left_lower_arm_bone
left_hand_bone_name = left_hand_bone.name

head_bone = armature_data.edit_bones.new("head")
head_bone.head = (0, 0, 0.75)
head_bone.tail = (0, 1, 0.75)
head_bone.parent = spine_bone
head_bone_name = head_bone.name

bpy.ops.object.mode_set(mode="OBJECT")

# VRM Human Boneを割り当て

humanoid = armature_data.vrm_addon_extension.vrm1.humanoid
humanoid.human_bones.head.node.bone_name = head_bone_name
humanoid.human_bones.spine.node.bone_name = spine_bone_name
humanoid.human_bones.hips.node.bone_name = hips_bone_name
humanoid.human_bones.right_upper_arm.node.bone_name = right_upper_arm_bone_name
humanoid.human_bones.right_lower_arm.node.bone_name = right_lower_arm_bone_name
humanoid.human_bones.right_hand.node.bone_name = right_hand_bone_name
humanoid.human_bones.left_upper_arm.node.bone_name = left_upper_arm_bone_name
humanoid.human_bones.left_lower_arm.node.bone_name = left_lower_arm_bone_name
humanoid.human_bones.left_hand.node.bone_name = left_hand_bone_name
humanoid.human_bones.right_upper_leg.node.bone_name = right_upper_leg_bone_name
humanoid.human_bones.right_lower_leg.node.bone_name = right_lower_leg_bone_name
humanoid.human_bones.right_foot.node.bone_name = right_foot_bone_name
humanoid.human_bones.left_upper_leg.node.bone_name = left_upper_leg_bone_name
humanoid.human_bones.left_lower_leg.node.bone_name = left_lower_leg_bone_name
humanoid.human_bones.left_foot.node.bone_name = left_foot_bone_name

# メッシュを追加

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25)
head = bpy.context.active_object
head.parent = armature_object
head.parent_bone = humanoid.human_bones.head.node.bone_name
head.parent_type = "BONE"

bpy.ops.mesh.primitive_cube_add(size=0.4)
spine = bpy.context.active_object
spine.parent = armature_object
spine.parent_bone = humanoid.human_bones.spine.node.bone_name
spine.parent_type = "BONE"

bpy.ops.mesh.primitive_ico_sphere_add(radius=0.1)
left_upper_arm = bpy.context.active_object
left_upper_arm.parent = armature_object
left_upper_arm.parent_bone = humanoid.human_bones.left_upper_arm.node.bone_name
left_upper_arm.parent_type = "BONE"

bpy.ops.mesh.primitive_ico_sphere_add(radius=0.1)
left_hand = bpy.context.active_object
left_hand.parent = armature_object
left_hand.parent_bone = humanoid.human_bones.left_hand.node.bone_name
left_hand.parent_type = "BONE"

bpy.ops.mesh.primitive_ico_sphere_add(radius=0.1)
right_upper_arm = bpy.context.active_object
right_upper_arm.parent = armature_object
right_upper_arm.parent_bone = humanoid.human_bones.right_upper_arm.node.bone_name
right_upper_arm.parent_type = "BONE"

bpy.ops.mesh.primitive_ico_sphere_add(radius=0.1)
right_hand = bpy.context.active_object
right_hand.parent = armature_object
right_hand.parent_bone = humanoid.human_bones.right_hand.node.bone_name
right_hand.parent_type = "BONE"

bpy.ops.mesh.primitive_ico_sphere_add(radius=0.1)
left_upper_leg = bpy.context.active_object
left_upper_leg.parent = armature_object
left_upper_leg.parent_bone = humanoid.human_bones.left_upper_leg.node.bone_name
left_upper_leg.parent_type = "BONE"

bpy.ops.mesh.primitive_ico_sphere_add(radius=0.1)
right_upper_leg = bpy.context.active_object
right_upper_leg.parent = armature_object
right_upper_leg.parent_bone = humanoid.human_bones.right_upper_leg.node.bone_name
right_upper_leg.parent_type = "BONE"

bpy.ops.mesh.primitive_ico_sphere_add(radius=0.1)
left_lower_leg = bpy.context.active_object
left_lower_leg.parent = armature_object
left_lower_leg.parent_bone = humanoid.human_bones.left_lower_leg.node.bone_name
left_lower_leg.parent_type = "BONE"

bpy.ops.mesh.primitive_ico_sphere_add(radius=0.1)
right_lower_leg = bpy.context.active_object
right_lower_leg.parent = armature_object
right_lower_leg.parent_bone = humanoid.human_bones.right_lower_leg.node.bone_name
right_lower_leg.parent_type = "BONE"

# メタデータを設定

meta = armature_data.vrm_addon_extension.vrm1.meta
meta.vrm_name = "Your Model Name"
meta.version = "1.0.0"

# ファイルに保存

output_filepath = str(Path(__file__).parent / "path_to_your_vrm_model.vrm")
result = bpy.ops.export_scene.vrm(filepath=output_filepath)
if result != {"FINISHED"}:
    message = f"Failed to export vrm: {result}"
    raise RuntimeError(message)

print(f'Saved the VRM file to "{output_filepath}"')
```
