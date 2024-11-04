# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import math
import sys
from collections.abc import Sequence

import bpy
from bpy.types import Armature, Context
from mathutils import Euler, Quaternion, Vector

from io_scene_vrm.common import ops, version
from io_scene_vrm.editor.extension import (
    VrmAddonArmatureExtensionPropertyGroup,
    get_armature_extension,
)

addon_version = version.get_addon_version()
spec_version = VrmAddonArmatureExtensionPropertyGroup.SPEC_VERSION_VRM1


def get_test_command_args() -> list[list[str]]:
    return [[key.__name__] for key in FUNCTIONS]


def assert_vector3_equals(
    expected: Vector, actual: Sequence[float], message: str
) -> None:
    if len(actual) != 3:
        message = f"actual length is not 3: {actual}"
        raise AssertionError(message)

    threshold = 0.0001
    if abs(expected[0] - actual[0]) > threshold:
        message = f"{message}: {tuple(expected)} is different from {tuple(actual)}"
        raise AssertionError(message)
    if abs(expected[1] - actual[1]) > threshold:
        message = f"{message}: {tuple(expected)} is different from {tuple(actual)}"
        raise AssertionError(message)
    if abs(expected[2] - actual[2]) > threshold:
        message = f"{message}: {tuple(expected)} is different from {tuple(actual)}"
        raise AssertionError(message)


def clean_scene(context: Context) -> None:
    if context.view_layer.objects.active:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    while context.blend_data.collections:
        context.blend_data.collections.remove(context.blend_data.collections[0])
    bpy.ops.outliner.orphans_purge(do_recursive=True)


def one_joint_extending_in_y_direction(context: Context) -> None:
    clean_scene(context)

    bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
    armature = context.object
    if not armature or not isinstance(armature.data, Armature):
        raise AssertionError

    get_armature_extension(armature.data).addon_version = addon_version
    get_armature_extension(armature.data).spec_version = spec_version
    get_armature_extension(armature.data).spring_bone1.enable_animation = True

    bpy.ops.object.mode_set(mode="EDIT")
    root_bone = armature.data.edit_bones.new("root")
    root_bone.head = Vector((0, 0, 0))
    root_bone.tail = Vector((0, 1, 0))

    joint_bone0 = armature.data.edit_bones.new("joint0")
    joint_bone0.parent = root_bone
    joint_bone0.head = Vector((0, 1, 0))
    joint_bone0.tail = Vector((0, 2, 0))

    joint_bone1 = armature.data.edit_bones.new("joint1")
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

    joints = get_armature_extension(armature.data).spring_bone1.springs[0].joints
    joints[0].node.bone_name = "joint0"
    joints[0].gravity_power = 1
    joints[0].drag_force = 1
    joints[0].stiffness = 0
    joints[1].node.bone_name = "joint1"
    joints[1].gravity_power = 1
    joints[1].drag_force = 1
    joints[1].stiffness = 0

    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "初期状態のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 2, 0), "初期状態のjoint1"
    )

    ops.vrm.update_spring_bone1_animation(delta_time=1)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "1秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 1.7071, -0.7071), "1秒後のjoint1"
    )

    ops.vrm.update_spring_bone1_animation(delta_time=10000)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "10000秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 1, -1), "10000秒後のjoint1"
    )


def one_joint_extending_in_y_direction_with_rotating_armature(context: Context) -> None:
    clean_scene(context)

    bpy.ops.object.add(
        type="ARMATURE", location=(1, 0, 0), rotation=(0, 0, math.pi / 2)
    )
    armature = context.object
    if not armature or not isinstance(armature.data, Armature):
        raise AssertionError

    get_armature_extension(armature.data).addon_version = addon_version
    get_armature_extension(armature.data).spec_version = spec_version
    get_armature_extension(armature.data).spring_bone1.enable_animation = True

    bpy.ops.object.mode_set(mode="EDIT")
    root_bone = armature.data.edit_bones.new("root")
    root_bone.head = Vector((0, 0, 0))
    root_bone.tail = Vector((0, 0.1, 0))

    joint_bone0 = armature.data.edit_bones.new("joint0")
    joint_bone0.parent = root_bone
    joint_bone0.head = Vector((0, 1, 0))
    joint_bone0.tail = Vector((0, 1.1, 0))

    joint_bone1 = armature.data.edit_bones.new("joint1")
    joint_bone1.parent = joint_bone0
    joint_bone1.head = Vector((0, 2, 0))
    joint_bone1.tail = Vector((0, 2.1, 0))
    bpy.ops.object.mode_set(mode="OBJECT")

    assert ops.vrm.add_spring_bone1_spring(armature_name=armature.name) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}

    joints = get_armature_extension(armature.data).spring_bone1.springs[0].joints
    joints[0].node.bone_name = "joint0"
    joints[0].gravity_power = 1
    joints[0].drag_force = 1
    joints[0].stiffness = 0
    joints[1].node.bone_name = "joint1"
    joints[1].gravity_power = 1
    joints[1].drag_force = 1
    joints[1].stiffness = 0

    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "初期状態のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 2, 0), "初期状態のjoint1"
    )

    ops.vrm.update_spring_bone1_animation(delta_time=1)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "1秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 1.7071, -0.7071), "1秒後のjoint1"
    )

    ops.vrm.update_spring_bone1_animation(delta_time=100000)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "100000秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 1, -1), "100000秒後のjoint1"
    )


def one_joint_extending_in_y_direction_with_rotating_armature_stiffness(
    context: Context,
) -> None:
    clean_scene(context)

    bpy.ops.object.add(
        type="ARMATURE", location=(1, 0, 0), rotation=(0, 0, math.pi / 2)
    )
    armature = context.object
    if not armature or not isinstance(armature.data, Armature):
        raise AssertionError

    get_armature_extension(armature.data).addon_version = addon_version
    get_armature_extension(armature.data).spec_version = spec_version
    get_armature_extension(armature.data).spring_bone1.enable_animation = True

    bpy.ops.object.mode_set(mode="EDIT")
    root_bone = armature.data.edit_bones.new("root")
    root_bone.head = Vector((0, 0, 0))
    root_bone.tail = Vector((0, 0.8, 0))

    joint_bone0 = armature.data.edit_bones.new("joint0")
    joint_bone0.parent = root_bone
    joint_bone0.head = Vector((0, 1, 0))
    joint_bone0.tail = Vector((0, 1.8, 0))

    joint_bone1 = armature.data.edit_bones.new("joint1")
    joint_bone1.parent = joint_bone0
    joint_bone1.head = Vector((0, 2, 0))
    joint_bone1.tail = Vector((0, 2.8, 0))
    bpy.ops.object.mode_set(mode="OBJECT")
    armature.pose.bones["joint0"].rotation_mode = "QUATERNION"
    armature.pose.bones["joint0"].rotation_quaternion = Quaternion(
        (1, 0, 0), math.radians(-90)
    )

    assert ops.vrm.add_spring_bone1_spring(armature_name=armature.name) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}

    joints = get_armature_extension(armature.data).spring_bone1.springs[0].joints
    joints[0].node.bone_name = "joint0"
    joints[0].gravity_power = 0
    joints[0].drag_force = 1
    joints[0].stiffness = 1
    joints[1].node.bone_name = "joint1"
    joints[1].gravity_power = 0
    joints[1].drag_force = 1
    joints[1].stiffness = 1

    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "初期状態のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 1, -1), "初期状態のjoint1"
    )

    ops.vrm.update_spring_bone1_animation(delta_time=1)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "1秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 1.7071, -0.7071), "1秒後のjoint1"
    )

    ops.vrm.update_spring_bone1_animation(delta_time=100000)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "100000秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 2, 0), "100000秒後のjoint1"
    )


def two_joints_extending_in_y_direction(context: Context) -> None:
    clean_scene(context)

    bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
    armature = context.object
    if not armature or not isinstance(armature.data, Armature):
        raise AssertionError

    get_armature_extension(armature.data).addon_version = addon_version
    get_armature_extension(armature.data).spec_version = spec_version
    get_armature_extension(armature.data).spring_bone1.enable_animation = True

    bpy.ops.object.mode_set(mode="EDIT")
    root_bone = armature.data.edit_bones.new("root")
    root_bone.head = Vector((0, 0, 0))
    root_bone.tail = Vector((0, 0.1, 0))

    joint_bone0 = armature.data.edit_bones.new("joint0")
    joint_bone0.parent = root_bone
    joint_bone0.head = Vector((0, 1, 0))
    joint_bone0.tail = Vector((0, 1.1, 0))

    joint_bone1 = armature.data.edit_bones.new("joint1")
    joint_bone1.parent = joint_bone0
    joint_bone1.head = Vector((0, 2, 0))
    joint_bone1.tail = Vector((0, 2.1, 0))

    joint_bone2 = armature.data.edit_bones.new("joint2")
    joint_bone2.parent = joint_bone1
    joint_bone2.head = Vector((0, 3, 0))
    joint_bone2.tail = Vector((0, 3.1, 0))
    bpy.ops.object.mode_set(mode="OBJECT")

    assert ops.vrm.add_spring_bone1_spring(armature_name=armature.name) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}

    joints = get_armature_extension(armature.data).spring_bone1.springs[0].joints
    joints[0].node.bone_name = "joint0"
    joints[0].gravity_power = 1
    joints[0].drag_force = 1
    joints[0].stiffness = 0
    joints[1].node.bone_name = "joint1"
    joints[1].gravity_power = 1
    joints[1].drag_force = 1
    joints[1].stiffness = 0
    joints[2].node.bone_name = "joint2"
    joints[2].gravity_power = 1
    joints[2].drag_force = 1
    joints[2].stiffness = 0

    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "初期状態のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 2, 0), "初期状態のjoint1"
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head, (0, 3, 0), "初期状態のjoint2"
    )

    ops.vrm.update_spring_bone1_animation(delta_time=1)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "1秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 1.7071, -0.7071), "1秒後のjoint1"
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head, (0, 2.6824, -0.9280), "1秒後のjoint2"
    )

    ops.vrm.update_spring_bone1_animation(delta_time=100000)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "100000秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 1, -1), "100000秒後のjoint1"
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head, (0, 1, -2), "100000秒後のjoint2"
    )


def two_joints_extending_in_y_direction_roll(context: Context) -> None:
    clean_scene(context)

    bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
    armature = context.object
    if not armature or not isinstance(armature.data, Armature):
        raise AssertionError

    get_armature_extension(armature.data).addon_version = addon_version
    get_armature_extension(armature.data).spec_version = spec_version
    get_armature_extension(armature.data).spring_bone1.enable_animation = True

    bpy.ops.object.mode_set(mode="EDIT")
    root_bone = armature.data.edit_bones.new("root")
    root_bone.head = Vector((0, 0, 0))
    root_bone.tail = Vector((0, 0.1, 0))
    root_bone.roll = math.radians(90)

    joint_bone0 = armature.data.edit_bones.new("joint0")
    joint_bone0.parent = root_bone
    joint_bone0.head = Vector((0, 1, 0))
    joint_bone0.tail = Vector((0, 1.1, 0))
    joint_bone0.roll = math.radians(45)

    joint_bone1 = armature.data.edit_bones.new("joint1")
    joint_bone1.parent = joint_bone0
    joint_bone1.head = Vector((0, 2, 0))
    joint_bone1.tail = Vector((0, 2.1, 0))
    joint_bone1.roll = math.radians(45)

    joint_bone2 = armature.data.edit_bones.new("joint2")
    joint_bone2.parent = joint_bone1
    joint_bone2.head = Vector((0, 3, 0))
    joint_bone2.tail = Vector((0, 3.1, 0))
    bpy.ops.object.mode_set(mode="OBJECT")

    assert ops.vrm.add_spring_bone1_spring(armature_name=armature.name) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}

    joints = get_armature_extension(armature.data).spring_bone1.springs[0].joints
    joints[0].node.bone_name = "joint0"
    joints[0].gravity_power = 1
    joints[0].drag_force = 1
    joints[0].stiffness = 0
    joints[1].node.bone_name = "joint1"
    joints[1].gravity_power = 1
    joints[1].drag_force = 1
    joints[1].stiffness = 0
    joints[2].node.bone_name = "joint2"
    joints[2].gravity_power = 1
    joints[2].drag_force = 1
    joints[2].stiffness = 0

    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "初期状態のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 2, 0), "初期状態のjoint1"
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head, (0, 3, 0), "初期状態のjoint2"
    )

    ops.vrm.update_spring_bone1_animation(delta_time=1)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "1秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 1.7071, -0.7071), "1秒後のjoint1"
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head, (0, 2.6824, -0.9280), "1秒後のjoint2"
    )

    ops.vrm.update_spring_bone1_animation(delta_time=100000)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "100000秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 1, -1), "100000秒後のjoint1"
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head, (0, 1, -2), "100000秒後のjoint2"
    )


def two_joints_extending_in_y_direction_local_translation(context: Context) -> None:
    clean_scene(context)

    bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
    armature = context.object
    if not armature or not isinstance(armature.data, Armature):
        raise AssertionError

    get_armature_extension(armature.data).addon_version = addon_version
    get_armature_extension(armature.data).spec_version = spec_version
    get_armature_extension(armature.data).spring_bone1.enable_animation = True

    bpy.ops.object.mode_set(mode="EDIT")
    root_bone = armature.data.edit_bones.new("root")
    root_bone.head = Vector((0, 0, 0))
    root_bone.tail = Vector((0, 0.1, 0))
    root_bone.use_local_location = True

    joint_bone0 = armature.data.edit_bones.new("joint0")
    joint_bone0.parent = root_bone
    joint_bone0.head = Vector((0, 1, 0))
    joint_bone0.tail = Vector((0, 1.1, 0))
    joint_bone0.use_local_location = True

    joint_bone1 = armature.data.edit_bones.new("joint1")
    joint_bone1.parent = joint_bone0
    joint_bone1.head = Vector((0, 2, 0))
    joint_bone1.tail = Vector((0, 2.1, 0))
    joint_bone1.use_local_location = True

    joint_bone2 = armature.data.edit_bones.new("joint2")
    joint_bone2.parent = joint_bone1
    joint_bone2.head = Vector((0, 3, 0))
    joint_bone2.tail = Vector((0, 3.1, 0))
    joint_bone2.use_local_location = False
    bpy.ops.object.mode_set(mode="OBJECT")

    assert ops.vrm.add_spring_bone1_spring(armature_name=armature.name) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}

    joints = get_armature_extension(armature.data).spring_bone1.springs[0].joints
    joints[0].node.bone_name = "joint0"
    joints[0].gravity_power = 1
    joints[0].drag_force = 1
    joints[0].stiffness = 0
    joints[1].node.bone_name = "joint1"
    joints[1].gravity_power = 1
    joints[1].drag_force = 1
    joints[1].stiffness = 0
    joints[2].node.bone_name = "joint2"
    joints[2].gravity_power = 1
    joints[2].drag_force = 1
    joints[2].stiffness = 0

    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "初期状態のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 2, 0), "初期状態のjoint1"
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head, (0, 3, 0), "初期状態のjoint2"
    )

    ops.vrm.update_spring_bone1_animation(delta_time=1)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "1秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 1.7071, -0.7071), "1秒後のjoint1"
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head, (0, 2.6824, -0.9280), "1秒後のjoint2"
    )

    ops.vrm.update_spring_bone1_animation(delta_time=100000)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "100000秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 1, -1), "100000秒後のjoint1"
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head, (0, 1, -2), "100000秒後のjoint2"
    )


def two_joints_extending_in_y_direction_connected(context: Context) -> None:
    clean_scene(context)

    bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
    armature = context.object
    if not armature or not isinstance(armature.data, Armature):
        raise AssertionError

    get_armature_extension(armature.data).addon_version = addon_version
    get_armature_extension(armature.data).spec_version = spec_version
    get_armature_extension(armature.data).spring_bone1.enable_animation = True

    bpy.ops.object.mode_set(mode="EDIT")
    root_bone = armature.data.edit_bones.new("root")
    root_bone.head = Vector((0, 0, 0))
    root_bone.tail = Vector((0, 1, 0))

    joint_bone0 = armature.data.edit_bones.new("joint0")
    joint_bone0.parent = root_bone
    joint_bone0.head = Vector((0, 1, 0))
    joint_bone0.tail = Vector((0, 2, 0))

    joint_bone1 = armature.data.edit_bones.new("joint1")
    joint_bone1.parent = joint_bone0
    joint_bone1.head = Vector((0, 2, 0))
    joint_bone1.tail = Vector((0, 3, 0))

    joint_bone2 = armature.data.edit_bones.new("joint2")
    joint_bone2.parent = joint_bone1
    joint_bone2.head = Vector((0, 3, 0))
    joint_bone2.tail = Vector((0, 4, 0))

    joint_bone0.use_connect = True
    joint_bone1.use_connect = True
    joint_bone2.use_connect = True
    bpy.ops.object.mode_set(mode="OBJECT")

    assert ops.vrm.add_spring_bone1_spring(armature_name=armature.name) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}

    joints = get_armature_extension(armature.data).spring_bone1.springs[0].joints
    joints[0].node.bone_name = "joint0"
    joints[0].gravity_power = 1
    joints[0].drag_force = 1
    joints[0].stiffness = 0
    joints[1].node.bone_name = "joint1"
    joints[1].gravity_power = 1
    joints[1].drag_force = 1
    joints[1].stiffness = 0
    joints[2].node.bone_name = "joint2"
    joints[2].gravity_power = 1
    joints[2].drag_force = 1
    joints[2].stiffness = 0

    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "初期状態のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 2, 0), "初期状態のjoint1"
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head, (0, 3, 0), "初期状態のjoint2"
    )

    ops.vrm.update_spring_bone1_animation(delta_time=1)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "1秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 1.7071, -0.7071), "1秒後のjoint1"
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head, (0, 2.6824, -0.9280), "1秒後のjoint2"
    )

    ops.vrm.update_spring_bone1_animation(delta_time=100000)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "100000秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 1, -1), "100000秒後のjoint1"
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head, (0, 1, -2), "100000秒後のjoint2"
    )


def one_joint_extending_in_y_direction_gravity_y_object_move_to_z(
    context: Context,
) -> None:
    clean_scene(context)

    bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
    armature = context.object
    if not armature or not isinstance(armature.data, Armature):
        raise AssertionError

    get_armature_extension(armature.data).addon_version = addon_version
    get_armature_extension(armature.data).spec_version = spec_version
    get_armature_extension(armature.data).spring_bone1.enable_animation = True

    bpy.ops.object.mode_set(mode="EDIT")
    root_bone = armature.data.edit_bones.new("root")
    root_bone.head = Vector((0, 0, 0))
    root_bone.tail = Vector((0, 1, 0))

    joint_bone0 = armature.data.edit_bones.new("joint0")
    joint_bone0.parent = root_bone
    joint_bone0.head = Vector((0, 1, 0))
    joint_bone0.tail = Vector((0, 2, 0))

    joint_bone1 = armature.data.edit_bones.new("joint1")
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

    joints = get_armature_extension(armature.data).spring_bone1.springs[0].joints
    joints[0].node.bone_name = "joint0"
    joints[0].gravity_power = 1
    joints[0].gravity_dir = (0, 1, 0)
    joints[0].drag_force = 0
    joints[0].stiffness = 0
    joints[1].node.bone_name = "joint1"
    joints[1].gravity_power = 1
    joints[1].gravity_dir = (0, 1, 0)
    joints[1].drag_force = 0
    joints[1].stiffness = 0

    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "初期状態のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 2, 0), "初期状態のjoint1"
    )

    ops.vrm.update_spring_bone1_animation(delta_time=1)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "1秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 2, 0), "1秒後のjoint1"
    )

    armature.location = Vector((0, 0, 1))
    context.view_layer.update()
    ops.vrm.update_spring_bone1_animation(delta_time=1)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "2秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head,
        (0, 1.8944271802, -0.4472135901),
        "2秒後のjoint1",
    )

    ops.vrm.update_spring_bone1_animation(delta_time=1000000)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "1000000秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 2, 0), "1000000秒後のjoint1"
    )


def one_joint_extending_in_y_direction_rounding_180_degree(context: Context) -> None:
    clean_scene(context)

    bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
    armature = context.object
    if not armature or not isinstance(armature.data, Armature):
        raise AssertionError

    get_armature_extension(armature.data).addon_version = addon_version
    get_armature_extension(armature.data).spec_version = spec_version
    get_armature_extension(armature.data).spring_bone1.enable_animation = True

    bpy.ops.object.mode_set(mode="EDIT")
    root_bone = armature.data.edit_bones.new("root")
    root_bone.head = Vector((0, 0, 0))
    root_bone.tail = Vector((0, 1, 0))

    joint_bone0 = armature.data.edit_bones.new("joint0")
    joint_bone0.parent = root_bone
    joint_bone0.head = Vector((0, 1, 0))
    joint_bone0.tail = Vector((0, 2, 0))

    joint_bone1 = armature.data.edit_bones.new("joint1")
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

    joints = get_armature_extension(armature.data).spring_bone1.springs[0].joints
    joints[0].node.bone_name = "joint0"
    joints[0].gravity_power = 1  # はじめに重力で勢いをつける
    joints[0].drag_force = 0
    joints[0].stiffness = 0
    joints[1].node.bone_name = "joint1"
    joints[1].gravity_power = 0
    joints[1].drag_force = 0
    joints[1].stiffness = 0

    armature.pose.bones["joint0"].rotation_mode = "QUATERNION"
    armature.pose.bones["joint0"].rotation_quaternion.rotate(Euler((0, math.pi, 0)))

    context.view_layer.update()

    ops.vrm.update_spring_bone1_animation(delta_time=1)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 1, 0), "1秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 1.7071, -0.7071), "1秒後のjoint1"
    )


def two_joints_extending_in_y_direction_root_down(context: Context) -> None:
    clean_scene(context)

    bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
    armature = context.object
    if not armature or not isinstance(armature.data, Armature):
        raise AssertionError

    get_armature_extension(armature.data).addon_version = addon_version
    get_armature_extension(armature.data).spec_version = spec_version
    get_armature_extension(armature.data).spring_bone1.enable_animation = True

    bpy.ops.object.mode_set(mode="EDIT")
    root_bone = armature.data.edit_bones.new("root")
    root_bone.head = Vector((0, 0, 0))
    root_bone.tail = Vector((0, 0.8, 0))

    joint_bone0 = armature.data.edit_bones.new("joint0")
    joint_bone0.parent = root_bone
    joint_bone0.head = Vector((0, 1, 0))
    joint_bone0.tail = Vector((0, 1.8, 0))

    joint_bone1 = armature.data.edit_bones.new("joint1")
    joint_bone1.parent = joint_bone0
    joint_bone1.head = Vector((0, 2, 0))
    joint_bone1.tail = Vector((0, 2.8, 0))

    joint_bone2 = armature.data.edit_bones.new("joint2")
    joint_bone2.parent = joint_bone1
    joint_bone2.head = Vector((0, 3, 0))
    joint_bone2.tail = Vector((0, 3.8, 0))
    bpy.ops.object.mode_set(mode="OBJECT")

    assert ops.vrm.add_spring_bone1_spring(armature_name=armature.name) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}

    joints = get_armature_extension(armature.data).spring_bone1.springs[0].joints
    joints[0].node.bone_name = "joint0"
    joints[0].gravity_power = 1
    joints[0].drag_force = 1
    joints[0].stiffness = 0
    joints[1].node.bone_name = "joint1"
    joints[1].gravity_power = 1
    joints[1].drag_force = 1
    joints[1].stiffness = 0
    joints[2].node.bone_name = "joint2"
    joints[2].gravity_power = 1
    joints[2].drag_force = 1
    joints[2].stiffness = 0

    root_pose_bone = armature.pose.bones["root"]
    if root_pose_bone.rotation_mode != "QUATERNION":
        root_pose_bone.rotation_mode = "QUATERNION"
    root_pose_bone.rotation_quaternion = Quaternion((1, 0, 0), math.radians(-90.0))

    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 0, -1), "初期状態のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 0, -2), "初期状態のjoint1"
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head, (0, 0, -3), "初期状態のjoint2"
    )

    ops.vrm.update_spring_bone1_animation(delta_time=1)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 0, -1), "1秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head,
        (0, 0, -2),
        "1秒後のjoint1",
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head,
        (0, 0, -3),
        "1秒後のjoint2",
    )


def two_joints_extending_in_y_direction_with_child_stiffness(context: Context) -> None:
    clean_scene(context)

    bpy.ops.object.add(type="ARMATURE")
    armature = context.object
    if not armature or not isinstance(armature.data, Armature):
        raise AssertionError

    get_armature_extension(armature.data).addon_version = addon_version
    get_armature_extension(armature.data).spec_version = spec_version
    get_armature_extension(armature.data).spring_bone1.enable_animation = True

    bpy.ops.object.mode_set(mode="EDIT")
    root_bone = armature.data.edit_bones.new("root")
    root_bone.head = Vector((0, 0, 0))
    root_bone.tail = Vector((0, 0.8, 0))

    joint_bone0 = armature.data.edit_bones.new("joint0")
    joint_bone0.parent = root_bone
    joint_bone0.head = Vector((0, 1, 0))
    joint_bone0.tail = Vector((0, 1.8, 0))

    joint_bone1 = armature.data.edit_bones.new("joint1")
    joint_bone1.parent = joint_bone0
    joint_bone1.head = Vector((0, 2, 0))
    joint_bone1.tail = Vector((0, 2.8, 0))

    joint_bone2 = armature.data.edit_bones.new("joint2")
    joint_bone2.parent = joint_bone1
    joint_bone2.head = Vector((0, 3, 0))
    joint_bone2.tail = Vector((0, 3.8, 0))
    bpy.ops.object.mode_set(mode="OBJECT")

    assert ops.vrm.add_spring_bone1_spring(armature_name=armature.name) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}

    joints = get_armature_extension(armature.data).spring_bone1.springs[0].joints
    joints[0].node.bone_name = "joint0"
    joints[0].gravity_power = 0
    joints[0].drag_force = 1
    joints[0].stiffness = 0
    joints[1].node.bone_name = "joint1"
    joints[1].gravity_power = 0
    joints[1].drag_force = 1
    joints[1].stiffness = 1
    joints[2].node.bone_name = "joint2"
    joints[2].gravity_power = 0
    joints[2].drag_force = 1
    joints[2].stiffness = 0

    armature.pose.bones["joint0"].rotation_mode = "QUATERNION"
    armature.pose.bones["joint0"].rotation_quaternion = Quaternion(
        (1, 0, 0), math.radians(90)
    )

    armature.pose.bones["joint1"].rotation_mode = "QUATERNION"
    armature.pose.bones["joint1"].rotation_quaternion = Quaternion(
        (1, 0, 0), math.radians(90)
    )

    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head,
        (0, 1, 0),
        "初期状態のjoint0",
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head,
        (0, 1, 1),
        "初期状態のjoint1",
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head,
        (0, 0, 1),
        "初期状態のjoint2",
    )

    ops.vrm.update_spring_bone1_animation(delta_time=1)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head,
        (0, 1, 0),
        "1秒後のjoint0",
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head,
        (0, 1, 1),
        "1秒後のjoint1",
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head,
        (0, 0.2929, 1.7071),
        "1秒後のjoint2",
    )

    ops.vrm.update_spring_bone1_animation(delta_time=100000)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head,
        (0, 1, 0),
        "100000秒後のjoint0",
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head,
        (0, 1, 1),
        "100000秒後のjoint1",
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head,
        (0, 1, 2),
        "100000秒後のjoint2",
    )


def one_joint_extending_in_y_direction_with_roll_stiffness(context: Context) -> None:
    clean_scene(context)

    bpy.ops.object.add(type="ARMATURE")
    armature = context.object
    if not armature or not isinstance(armature.data, Armature):
        raise AssertionError

    get_armature_extension(armature.data).addon_version = addon_version
    get_armature_extension(armature.data).spec_version = spec_version
    get_armature_extension(armature.data).spring_bone1.enable_animation = True

    bpy.ops.object.mode_set(mode="EDIT")
    root_bone = armature.data.edit_bones.new("root")
    root_bone.head = Vector((0, 0, 0))
    root_bone.tail = Vector((-0.8, 0, 0))

    joint_bone0 = armature.data.edit_bones.new("joint0")
    joint_bone0.parent = root_bone
    joint_bone0.head = Vector((-1, 0, 0))
    joint_bone0.tail = Vector((-1, 0, -1))
    joint_bone0.roll = math.radians(90)

    joint_bone1 = armature.data.edit_bones.new("joint1")
    joint_bone1.parent = joint_bone0
    joint_bone1.head = Vector((-1, 0, -1))
    joint_bone1.tail = Vector((-1, 0, -2))
    bpy.ops.object.mode_set(mode="OBJECT")

    assert ops.vrm.add_spring_bone1_spring(armature_name=armature.name) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}

    joints = get_armature_extension(armature.data).spring_bone1.springs[0].joints
    joints[0].node.bone_name = "joint0"
    joints[0].gravity_power = 0
    joints[0].drag_force = 1
    joints[0].stiffness = 1
    joints[1].node.bone_name = "joint1"
    joints[1].gravity_power = 0
    joints[1].drag_force = 1
    joints[1].stiffness = 1

    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head,
        (-1, 0, 0),
        "初期状態のjoint0",
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head,
        (-1, 0, -1),
        "初期状態のjoint1",
    )

    ops.vrm.update_spring_bone1_animation(delta_time=1)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head,
        (-1, 0, 0),
        "1秒後のjoint0",
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head,
        (-1, 0, -1),
        "1秒後のjoint1",
    )


def two_joints_extending_in_y_direction_center_move_to_z(context: Context) -> None:
    clean_scene(context)

    bpy.ops.object.add(type="ARMATURE")
    armature = context.object
    if not armature or not isinstance(armature.data, Armature):
        raise AssertionError

    get_armature_extension(armature.data).addon_version = addon_version
    get_armature_extension(armature.data).spec_version = spec_version
    get_armature_extension(armature.data).spring_bone1.enable_animation = True

    bpy.ops.object.mode_set(mode="EDIT")
    joint_bone0 = armature.data.edit_bones.new("joint0")
    joint_bone0.head = Vector((0, 0, 0))
    joint_bone0.tail = Vector((0, 0.8, 0))

    joint_bone1 = armature.data.edit_bones.new("joint1")
    joint_bone1.parent = joint_bone0
    joint_bone1.head = Vector((0, 1, 0))
    joint_bone1.tail = Vector((0, 1.8, 0))

    joint_bone2 = armature.data.edit_bones.new("joint2")
    joint_bone2.parent = joint_bone1
    joint_bone2.head = Vector((0, 2, 0))
    joint_bone2.tail = Vector((0, 2.001, 0))
    bpy.ops.object.mode_set(mode="OBJECT")

    assert ops.vrm.add_spring_bone1_spring(armature_name=armature.name) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}

    spring = get_armature_extension(armature.data).spring_bone1.springs[0]
    spring.center.bone_name = "joint0"
    joints = spring.joints
    joints[0].node.bone_name = "joint0"
    joints[0].gravity_power = 0
    joints[0].drag_force = 1
    joints[0].stiffness = 0
    joints[1].node.bone_name = "joint1"
    joints[1].gravity_power = 0
    joints[1].drag_force = 1
    joints[1].stiffness = 0
    joints[2].node.bone_name = "joint2"
    joints[2].gravity_power = 0
    joints[2].drag_force = 1
    joints[2].stiffness = 0

    ops.vrm.update_spring_bone1_animation(delta_time=1)
    context.view_layer.update()

    armature.location = Vector((0, 0, 1))

    ops.vrm.update_spring_bone1_animation(delta_time=1)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 0, 0), "1秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 1, 0), "1秒後のjoint1"
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head, (0, 2, 0), "1秒後のjoint2"
    )

    ops.vrm.update_spring_bone1_animation(delta_time=1)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 0, 0), "2秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 1, 0), "2秒後のjoint1"
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head, (0, 2, 0), "2秒後のjoint2"
    )


def two_joints_extending_in_y_direction_center_move_to_z_no_inertia(
    context: Context,
) -> None:
    clean_scene(context)

    bpy.ops.object.add(type="ARMATURE")
    armature = context.object
    if not armature or not isinstance(armature.data, Armature):
        raise AssertionError

    get_armature_extension(armature.data).addon_version = addon_version
    get_armature_extension(armature.data).spec_version = spec_version
    get_armature_extension(armature.data).spring_bone1.enable_animation = True

    bpy.ops.object.mode_set(mode="EDIT")
    joint_bone0 = armature.data.edit_bones.new("joint0")
    joint_bone0.head = Vector((0, 0, 0))
    joint_bone0.tail = Vector((0, 0.8, 0))

    joint_bone1 = armature.data.edit_bones.new("joint1")
    joint_bone1.parent = joint_bone0
    joint_bone1.head = Vector((0, 1, 0))
    joint_bone1.tail = Vector((0, 1.8, 0))

    joint_bone2 = armature.data.edit_bones.new("joint2")
    joint_bone2.parent = joint_bone1
    joint_bone2.head = Vector((0, 2, 0))
    joint_bone2.tail = Vector((0, 2.001, 0))
    bpy.ops.object.mode_set(mode="OBJECT")

    assert ops.vrm.add_spring_bone1_spring(armature_name=armature.name) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}
    assert ops.vrm.add_spring_bone1_spring_joint(
        armature_name=armature.name, spring_index=0
    ) == {"FINISHED"}

    spring = get_armature_extension(armature.data).spring_bone1.springs[0]
    spring.center.bone_name = "joint0"
    joints = spring.joints
    joints[0].node.bone_name = "joint0"
    joints[0].gravity_power = 0
    joints[0].drag_force = 1
    joints[0].stiffness = 0
    joints[1].node.bone_name = "joint1"
    joints[1].gravity_power = 0
    joints[1].drag_force = 1
    joints[1].stiffness = 0
    joints[2].node.bone_name = "joint2"
    joints[2].gravity_power = 0
    joints[2].drag_force = 1
    joints[2].stiffness = 0

    ops.vrm.update_spring_bone1_animation(delta_time=1)
    context.view_layer.update()

    armature.location = Vector((0, 0, 1))

    ops.vrm.update_spring_bone1_animation(delta_time=1)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 0, 0), "1秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 1, 0), "1秒後のjoint1"
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head, (0, 2, 0), "1秒後のjoint2"
    )

    ops.vrm.update_spring_bone1_animation(delta_time=1)
    context.view_layer.update()

    assert_vector3_equals(
        armature.pose.bones["joint0"].head, (0, 0, 0), "2秒後のjoint0"
    )
    assert_vector3_equals(
        armature.pose.bones["joint1"].head, (0, 1, 0), "2秒後のjoint1"
    )
    assert_vector3_equals(
        armature.pose.bones["joint2"].head, (0, 2, 0), "2秒後のjoint2"
    )


FUNCTIONS = [
    one_joint_extending_in_y_direction,
    one_joint_extending_in_y_direction_gravity_y_object_move_to_z,
    one_joint_extending_in_y_direction_with_rotating_armature,
    one_joint_extending_in_y_direction_with_rotating_armature_stiffness,
    one_joint_extending_in_y_direction_rounding_180_degree,
    one_joint_extending_in_y_direction_with_roll_stiffness,
    two_joints_extending_in_y_direction,
    two_joints_extending_in_y_direction_root_down,
    two_joints_extending_in_y_direction_roll,
    two_joints_extending_in_y_direction_connected,
    two_joints_extending_in_y_direction_local_translation,
    two_joints_extending_in_y_direction_with_child_stiffness,
    two_joints_extending_in_y_direction_center_move_to_z,
    two_joints_extending_in_y_direction_center_move_to_z_no_inertia,
]


def test(context: Context, function_name: str) -> None:
    function = next((f for f in FUNCTIONS if f.__name__ == function_name), None)
    if function is None:
        message = f"No function name: {function_name}"
        raise AssertionError(message)
    function(context)


if __name__ == "__main__":
    context = bpy.context
    if "--" in sys.argv:
        test(context, *sys.argv[slice(sys.argv.index("--") + 1, sys.maxsize)])
    else:
        for arg in get_test_command_args():
            test(context, *arg)
