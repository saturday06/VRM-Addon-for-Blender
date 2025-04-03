import cProfile
from pstats import SortKey

import bpy
from bpy.types import Armature, Context
from mathutils import Vector

from io_scene_vrm.common import ops, version
from io_scene_vrm.editor.extension import (
    VrmAddonArmatureExtensionPropertyGroup,
    get_armature_extension,
)

addon_version = version.get_addon_version()
spec_version = VrmAddonArmatureExtensionPropertyGroup.SPEC_VERSION_VRM1


def clean_scene(context: Context) -> None:
    if context.view_layer.objects.active:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    while context.blend_data.collections:
        context.blend_data.collections.remove(context.blend_data.collections[0])
    bpy.ops.outliner.orphans_purge(do_recursive=True)


def benchmark_spring_bone(context: Context) -> None:
    bpy.ops.preferences.addon_enable(module="io_scene_vrm")
    clean_scene(context)

    bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
    armature = context.object
    if (
        not armature
        or not (armature_data := armature.data)
        or not isinstance(armature_data, Armature)
    ):
        raise AssertionError

    get_armature_extension(armature_data).addon_version = addon_version
    get_armature_extension(armature_data).spec_version = spec_version
    get_armature_extension(armature_data).spring_bone1.enable_animation = True

    bpy.ops.object.mode_set(mode="EDIT")
    root_bone = armature_data.edit_bones.new("root")
    root_bone.head = Vector((0, 0, 0))
    root_bone.tail = Vector((0, 1, 0))

    joint_bone0 = armature_data.edit_bones.new("joint0")
    joint_bone0.parent = root_bone
    joint_bone0.head = Vector((0, 1, 0))
    joint_bone0.tail = Vector((0, 2, 0))

    joint_bone1 = armature_data.edit_bones.new("joint1")
    joint_bone1.parent = joint_bone0
    joint_bone1.head = Vector((0, 2, 0))
    joint_bone1.tail = Vector((0, 3, 0))
    bpy.ops.object.mode_set(mode="OBJECT")

    assert ops.vrm.add_spring_bone1_spring(armature_name=armature.name) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}

    joints = get_armature_extension(armature_data).spring_bone1.springs[0].joints
    joints[0].node.bone_name = "joint0"
    joints[0].gravity_power = 1
    joints[0].drag_force = 1
    joints[0].stiffness = 0
    joints[1].node.bone_name = "joint1"
    joints[1].gravity_power = 1
    joints[1].drag_force = 1
    joints[1].stiffness = 0

    context.view_layer.update()

    profiler = cProfile.Profile()
    with profiler:
        ops.vrm.update_spring_bone1_animation(delta_time=10000)
        context.view_layer.update()

    profiler.print_stats(SortKey.CUMULATIVE)


if __name__ == "__main__":
    benchmark_spring_bone(bpy.context)
