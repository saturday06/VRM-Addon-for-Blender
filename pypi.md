# bpy-vrm-format [![CI status](https://github.com/saturday06/VRM-Addon-for-Blender/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/saturday06/VRM-Addon-for-Blender/actions) [![CodSpeed Badge](https://img.shields.io/endpoint?url=https://codspeed.io/badge.json)](https://codspeed.io/saturday06/VRM-Addon-for-Blender?utm_source=badge)

`bpy-vrm-format` is a library for working with `VRM` files, a format for 3D humanoid
avatars. It is derived from
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

For more information, see the
[Scripting API documentation](https://vrm-addon-for-blender.info/en-us/scripting-api/).
