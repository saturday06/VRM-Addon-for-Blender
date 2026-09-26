# VRM Add-on for Blender [![CI status](https://github.com/saturday06/VRM-Addon-for-Blender/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/saturday06/VRM-Addon-for-Blender/actions) [![CodSpeed Badge](https://img.shields.io/endpoint?url=https://codspeed.io/badge.json)](https://codspeed.io/saturday06/VRM-Addon-for-Blender?utm_source=badge)

VRM Add-on for Blender adds VRM import, export, and editing capabilities to
Blender.

## Sample Code for Generating VRM Files

Here is a sample code that generates the following 3D character model and saves
it as a `.vrm` file.

![vrm preview](https://raw.githubusercontent.com/saturday06/VRM-Addon-for-Blender/refs/heads/main/docs/assets/images/humanoid.gif)

Before running the script, please run commands such as
`pip install bpy-vrm-format` or `uv add bpy-vrm-format` to make the package
available.

```python
import bpy
from pathlib import Path

bpy.ops.preferences.addon_enable(module="io_scene_vrm")

bpy.ops.icyp.make_basic_armature()

context = bpy.context

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

output_filepath = str(Path(__file__).parent / "path_to_your_vrm_model.vrm")
result = bpy.ops.export_scene.vrm(filepath=output_filepath)
if result != {"FINISHED"}:
    raise Exception(f"Failed to export vrm: {result}")

print(f"{output_filepath=}")
```

For more information, visit
[https://vrm-addon-for-blender.info/scripting-api/](https://vrm-addon-for-blender.info/scripting-api/).
