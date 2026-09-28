# bpy-vrm-format [![CI status](https://github.com/saturday06/VRM-Addon-for-Blender/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/saturday06/VRM-Addon-for-Blender/actions) [![CodSpeed Badge](https://img.shields.io/endpoint?url=https://codspeed.io/badge.json)](https://codspeed.io/saturday06/VRM-Addon-for-Blender?utm_source=badge)

`bpy-vrm-format` is a library for working with `VRM` files, a format for 3D
humanoid avatars. It is derived from
[VRM Add-on for Blender](https://github.com/saturday06/VRM-Addon-for-Blender)
and provides the same API without requiring an installation of Blender itself.

## Sample Code for Generating VRM Files

The following sample code generates the 3D character model shown below and saves
it as a `.vrm` file.

![VRM model preview](https://raw.githubusercontent.com/saturday06/VRM-Addon-for-Blender/refs/heads/main/docs/assets/images/humanoid.gif)

[View the 3D model](https://hub.vroid.com/characters/6595382014094436897/models/1372267393572384142)

Before running the script, install the package using
`pip install bpy-vrm-format` or add it to your project using
`uv add bpy-vrm-format`.

```python
from pathlib import Path

import bpy

# Initialize

bpy.ops.preferences.addon_enable(module="io_scene_vrm")

# Create an armature

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

# Assign VRM human bones

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

# Add meshes

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

# Set metadata

meta = armature_data.vrm_addon_extension.vrm1.meta
meta.vrm_name = "Your Model Name"
meta.version = "1.0.0"

# Save to a file

output_filepath = str(Path(__file__).parent / "path_to_your_vrm_model.vrm")
result = bpy.ops.export_scene.vrm(filepath=output_filepath)
if result != {"FINISHED"}:
    message = f"Failed to export vrm: {result}"
    raise RuntimeError(message)

print(f'Saved the VRM file to "{output_filepath}"')
```

For more information, see the
[Scripting API documentation](https://vrm-addon-for-blender.info/en-us/scripting-api/).
