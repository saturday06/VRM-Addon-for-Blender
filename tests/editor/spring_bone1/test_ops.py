# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import math
import uuid
from collections.abc import Sequence
from unittest import main

import bpy
from bpy.types import Armature
from mathutils import Euler, Quaternion, Vector

from io_scene_vrm.common import ops, version
from io_scene_vrm.editor.extension import (
    VrmAddonArmatureExtensionPropertyGroup,
    get_armature_extension,
)
from io_scene_vrm.editor.spring_bone1.ops import assign_spring_bone1_from_vrm0
from tests.util import AddonTestCase

addon_version = version.get_addon_version()
spec_version = VrmAddonArmatureExtensionPropertyGroup.SPEC_VERSION_VRM1


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


class TestSpringBone1(AddonTestCase):
    def test_one_joint_extending_in_y_direction(self) -> None:
        context = bpy.context

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

        self.assertEqual(
            ops.vrm.add_spring_bone1_spring(armature_object_name=armature.name),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )

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
            armature.pose.bones["joint0"].head, (0, 1, 0), "Initial state joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head, (0, 2, 0), "Initial state joint1"
        )

        ops.vrm.update_spring_bone1_animation(delta_time=1)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head, (0, 1, 0), "After 1 second joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (0, 1.7071, -0.7071),
            "After 1 second joint1",
        )

        ops.vrm.update_spring_bone1_animation(delta_time=10000)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head, (0, 1, 0), "After 10000 seconds joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head, (0, 1, -1), "After 10000 seconds joint1"
        )

    def test_one_joint_extending_in_y_direction_with_rotating_armature(self) -> None:
        context = bpy.context

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

        self.assertEqual(
            ops.vrm.add_spring_bone1_spring(armature_object_name=armature.name),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )

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
            armature.pose.bones["joint0"].head, (0, 1, 0), "Initial state joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head, (0, 2, 0), "Initial state joint1"
        )

        ops.vrm.update_spring_bone1_animation(delta_time=1)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head, (0, 1, 0), "After 1 second joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (0, 1.7071, -0.7071),
            "After 1 second joint1",
        )

        ops.vrm.update_spring_bone1_animation(delta_time=100000)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head, (0, 1, 0), "After 100000 seconds joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (0, 1, -1),
            "After 100000 seconds joint1",
        )

    def test_one_joint_extending_in_y_direction_with_rotating_armature_stiffness(
        self,
    ) -> None:
        context = bpy.context

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

        self.assertEqual(
            ops.vrm.add_spring_bone1_spring(armature_object_name=armature.name),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )

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
            armature.pose.bones["joint0"].head, (0, 1, 0), "Initial state joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head, (0, 1, -1), "Initial state joint1"
        )

        ops.vrm.update_spring_bone1_animation(delta_time=1)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head, (0, 1, 0), "After 1 second joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (0, 1.7071, -0.7071),
            "After 1 second joint1",
        )

        ops.vrm.update_spring_bone1_animation(delta_time=100000)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head, (0, 1, 0), "After 100000 seconds joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head, (0, 2, 0), "After 100000 seconds joint1"
        )

    def test_two_joints_extending_in_y_direction(self) -> None:
        context = bpy.context

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

        self.assertEqual(
            ops.vrm.add_spring_bone1_spring(armature_object_name=armature.name),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )

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
            armature.pose.bones["joint0"].head, (0, 1, 0), "Initial state joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head, (0, 2, 0), "Initial state joint1"
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head, (0, 3, 0), "Initial state joint2"
        )

        ops.vrm.update_spring_bone1_animation(delta_time=1)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head, (0, 1, 0), "After 1 second joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (0, 1.7071, -0.7071),
            "After 1 second joint1",
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head,
            (0, 2.6824, -0.9280),
            "After 1 second joint2",
        )

        ops.vrm.update_spring_bone1_animation(delta_time=100000)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head, (0, 1, 0), "After 100000 seconds joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (0, 1, -1),
            "After 100000 seconds joint1",
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head,
            (0, 1, -2),
            "After 100000 seconds joint2",
        )

    def test_two_joints_extending_in_y_direction_roll(self) -> None:
        context = bpy.context

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

        self.assertEqual(
            ops.vrm.add_spring_bone1_spring(armature_object_name=armature.name),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )

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
            armature.pose.bones["joint0"].head, (0, 1, 0), "Initial state joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head, (0, 2, 0), "Initial state joint1"
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head, (0, 3, 0), "Initial state joint2"
        )

        ops.vrm.update_spring_bone1_animation(delta_time=1)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head, (0, 1, 0), "After 1 second joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (0, 1.7071, -0.7071),
            "After 1 second joint1",
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head,
            (0, 2.6824, -0.9280),
            "After 1 second joint2",
        )

        ops.vrm.update_spring_bone1_animation(delta_time=100000)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head, (0, 1, 0), "After 100000 seconds joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (0, 1, -1),
            "After 100000 seconds joint1",
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head,
            (0, 1, -2),
            "After 100000 seconds joint2",
        )

    def test_two_joints_extending_in_y_direction_local_translation(self) -> None:
        context = bpy.context

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

        self.assertEqual(
            ops.vrm.add_spring_bone1_spring(armature_object_name=armature.name),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )

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
            armature.pose.bones["joint0"].head, (0, 1, 0), "Initial state joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head, (0, 2, 0), "Initial state joint1"
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head, (0, 3, 0), "Initial state joint2"
        )

        ops.vrm.update_spring_bone1_animation(delta_time=1)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head, (0, 1, 0), "After 1 second joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (0, 1.7071, -0.7071),
            "After 1 second joint1",
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head,
            (0, 2.6824, -0.9280),
            "After 1 second joint2",
        )

        ops.vrm.update_spring_bone1_animation(delta_time=100000)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head, (0, 1, 0), "After 100000 seconds joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (0, 1, -1),
            "After 100000 seconds joint1",
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head,
            (0, 1, -2),
            "After 100000 seconds joint2",
        )

    def test_two_joints_extending_in_y_direction_connected(self) -> None:
        context = bpy.context

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

        self.assertEqual(
            ops.vrm.add_spring_bone1_spring(armature_object_name=armature.name),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )

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
            armature.pose.bones["joint0"].head, (0, 1, 0), "Initial state joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head, (0, 2, 0), "Initial state joint1"
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head, (0, 3, 0), "Initial state joint2"
        )

        ops.vrm.update_spring_bone1_animation(delta_time=1)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head, (0, 1, 0), "After 1 second joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (0, 1.7071, -0.7071),
            "After 1 second joint1",
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head,
            (0, 2.6824, -0.9280),
            "After 1 second joint2",
        )

        ops.vrm.update_spring_bone1_animation(delta_time=100000)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head, (0, 1, 0), "After 100000 seconds joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (0, 1, -1),
            "After 100000 seconds joint1",
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head,
            (0, 1, -2),
            "After 100000 seconds joint2",
        )

    def test_one_joint_extending_in_y_direction_gravity_y_object_move_to_z(
        self,
    ) -> None:
        context = bpy.context

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

        self.assertEqual(
            ops.vrm.add_spring_bone1_spring(armature_object_name=armature.name),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )

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
            armature.pose.bones["joint0"].head, (0, 1, 0), "Initial state joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head, (0, 2, 0), "Initial state joint1"
        )

        ops.vrm.update_spring_bone1_animation(delta_time=1)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head, (0, 1, 0), "After 1 second joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head, (0, 2, 0), "After 1 second joint1"
        )

        armature.location = Vector((0, 0, 1))
        context.view_layer.update()
        ops.vrm.update_spring_bone1_animation(delta_time=1)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head, (0, 1, 0), "After 2 seconds joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (0, 1.8944271802, -0.4472135901),
            "After 2 seconds joint1",
        )

        ops.vrm.update_spring_bone1_animation(delta_time=1000000)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head,
            (0, 1, 0),
            "After 1000000 seconds joint0",
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (0, 2, 0),
            "After 1000000 seconds joint1",
        )

    def test_one_joint_extending_in_y_direction_rounding_180_degree(self) -> None:
        context = bpy.context

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

        self.assertEqual(
            ops.vrm.add_spring_bone1_spring(armature_object_name=armature.name),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )

        joints = get_armature_extension(armature.data).spring_bone1.springs[0].joints
        joints[0].node.bone_name = "joint0"
        joints[0].gravity_power = 1  # First apply gravity to gain momentum
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
            armature.pose.bones["joint0"].head, (0, 1, 0), "After 1 second joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (0, 1.7071, -0.7071),
            "After 1 second joint1",
        )

    def test_two_joints_extending_in_y_direction_root_down(self) -> None:
        context = bpy.context

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

        self.assertEqual(
            ops.vrm.add_spring_bone1_spring(armature_object_name=armature.name),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )

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
            armature.pose.bones["joint0"].head, (0, 0, -1), "Initial state joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head, (0, 0, -2), "Initial state joint1"
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head, (0, 0, -3), "Initial state joint2"
        )

        ops.vrm.update_spring_bone1_animation(delta_time=1)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head, (0, 0, -1), "After 1 second joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (0, 0, -2),
            "After 1 second joint1",
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head,
            (0, 0, -3),
            "After 1 second joint2",
        )

    def test_two_joints_extending_in_y_direction_with_child_stiffness(self) -> None:
        context = bpy.context

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

        self.assertEqual(
            ops.vrm.add_spring_bone1_spring(armature_object_name=armature.name),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )

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
            "Initial state joint0",
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (0, 1, 1),
            "Initial state joint1",
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head,
            (0, 0, 1),
            "Initial state joint2",
        )

        ops.vrm.update_spring_bone1_animation(delta_time=1)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head,
            (0, 1, 0),
            "After 1 second joint0",
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (0, 1, 1),
            "After 1 second joint1",
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head,
            (0, 0.2929, 1.7071),
            "After 1 second joint2",
        )

        ops.vrm.update_spring_bone1_animation(delta_time=100000)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head,
            (0, 1, 0),
            "After 100000 seconds joint0",
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (0, 1, 1),
            "After 100000 seconds joint1",
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head,
            (0, 1, 2),
            "After 100000 seconds joint2",
        )

    def test_one_joint_extending_in_y_direction_with_roll_stiffness(self) -> None:
        context = bpy.context

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

        self.assertEqual(
            ops.vrm.add_spring_bone1_spring(armature_object_name=armature.name),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )

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
            "Initial state joint0",
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (-1, 0, -1),
            "Initial state joint1",
        )

        ops.vrm.update_spring_bone1_animation(delta_time=1)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head,
            (-1, 0, 0),
            "After 1 second joint0",
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head,
            (-1, 0, -1),
            "After 1 second joint1",
        )

    def test_two_joints_extending_in_y_direction_center_move_to_z(self) -> None:
        context = bpy.context

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

        self.assertEqual(
            ops.vrm.add_spring_bone1_spring(armature_object_name=armature.name),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )

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
            armature.pose.bones["joint0"].head, (0, 0, 0), "After 1 second joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head, (0, 1, 0), "After 1 second joint1"
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head, (0, 2, 0), "After 1 second joint2"
        )

        ops.vrm.update_spring_bone1_animation(delta_time=1)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head, (0, 0, 0), "After 2 seconds joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head, (0, 1, 0), "After 2 seconds joint1"
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head, (0, 2, 0), "After 2 seconds joint2"
        )

    def test_two_joints_extending_in_y_direction_center_move_to_z_no_inertia(
        self,
    ) -> None:
        context = bpy.context

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

        self.assertEqual(
            ops.vrm.add_spring_bone1_spring(armature_object_name=armature.name),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )
        self.assertEqual(
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature.name, spring_index=0
            ),
            {"FINISHED"},
        )

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
            armature.pose.bones["joint0"].head, (0, 0, 0), "After 1 second joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head, (0, 1, 0), "After 1 second joint1"
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head, (0, 2, 0), "After 1 second joint2"
        )

        ops.vrm.update_spring_bone1_animation(delta_time=1)
        context.view_layer.update()

        assert_vector3_equals(
            armature.pose.bones["joint0"].head, (0, 0, 0), "After 2 seconds joint0"
        )
        assert_vector3_equals(
            armature.pose.bones["joint1"].head, (0, 1, 0), "After 2 seconds joint1"
        )
        assert_vector3_equals(
            armature.pose.bones["joint2"].head, (0, 2, 0), "After 2 seconds joint2"
        )


class TestAssignSpringBone1FromVrm0(AddonTestCase):
    def test_collider_group_and_spring_mapping(self) -> None:
        context = bpy.context

        bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
        armature = context.object
        if not armature or not isinstance(armature.data, Armature):
            raise AssertionError

        ext = get_armature_extension(armature.data)
        ext.addon_version = addon_version

        bpy.ops.object.mode_set(mode="EDIT")
        root_bone = armature.data.edit_bones.new("root")
        root_bone.head = Vector((0, 0, 0))
        root_bone.tail = Vector((0, 1, 0))

        child_bone = armature.data.edit_bones.new("child")
        child_bone.parent = root_bone
        child_bone.head = Vector((0, 1, 0))
        child_bone.tail = Vector((0, 2, 0))
        bpy.ops.object.mode_set(mode="OBJECT")

        secondary_animation = ext.vrm0.secondary_animation

        # Set up a collider group with one collider
        vrm0_collider_group = secondary_animation.collider_groups.add()
        vrm0_collider_group.uuid = uuid.uuid4().hex
        vrm0_collider_group.node.bone_name = "root"
        vrm0_collider_obj = context.blend_data.objects.new(
            name="root_collider_0", object_data=None
        )
        context.scene.collection.objects.link(vrm0_collider_obj)
        vrm0_collider_obj.parent = armature
        vrm0_collider_obj.empty_display_size = 0.05
        vrm0_collider_obj.empty_display_type = "SPHERE"
        vrm0_collider = vrm0_collider_group.colliders.add()
        vrm0_collider.name = "root_collider_0"
        vrm0_collider.bpy_object = vrm0_collider_obj

        # Set up a bone group referencing the collider group
        vrm0_bone_group = secondary_animation.bone_groups.add()
        vrm0_bone_group.comment = "TestGroup"
        vrm0_bone_group.stiffiness = 1.5
        vrm0_bone_group.gravity_power = 0.3
        vrm0_bone_group.drag_force = 0.4
        vrm0_bone_group.hit_radius = 0.02
        vrm0_root_bone_ref = vrm0_bone_group.bones.add()
        vrm0_root_bone_ref.bone_name = "root"
        vrm0_collider_group_reference = vrm0_bone_group.collider_groups.add()
        vrm0_collider_group_reference.collider_group_uuid = vrm0_collider_group.uuid
        vrm0_collider_group.fixup(armature)

        result = assign_spring_bone1_from_vrm0(context, armature.name)
        self.assertEqual(result, {"FINISHED"})

        spring_bone1 = ext.spring_bone1

        # Verify collider group count and naming
        self.assertEqual(len(spring_bone1.collider_groups), 1)
        collider_group = spring_bone1.collider_groups[0]
        self.assertIn(vrm0_collider_group.uuid, collider_group.vrm_name)
        self.assertIn("root", collider_group.vrm_name)

        # Verify collider is created with correct bone and shape
        self.assertEqual(len(spring_bone1.colliders), 1)
        collider = spring_bone1.colliders[0]
        self.assertEqual(collider.node.bone_name, "root")
        self.assertEqual(collider.shape_type, collider.SHAPE_TYPE_SPHERE.identifier)
        # Radius should equal empty_display_size (scale is identity)
        self.assertAlmostEqual(collider.shape.sphere.radius, 0.05, places=3)

        # The collider group should reference the collider
        self.assertEqual(len(collider_group.colliders), 1)
        self.assertEqual(collider_group.colliders[0].collider_uuid, collider.uuid)
        self.assertEqual(
            collider_group.colliders[0].collider_display_name, collider.display_name
        )

        # Verify springs were created
        self.assertGreater(len(spring_bone1.springs), 0)
        spring = spring_bone1.springs[0]
        self.assertIn("TestGroup", spring.vrm_name)

        # Verify joints cover the bone chain
        joint_bone_names = [j.node.bone_name for j in spring.joints]
        self.assertIn("root", joint_bone_names)

        # Verify joint parameters were copied from the VRM0 bone group
        joint = spring.joints[0]
        self.assertAlmostEqual(joint.stiffness, 1.5, places=5)
        self.assertAlmostEqual(joint.gravity_power, 0.3, places=5)
        self.assertAlmostEqual(joint.drag_force, 0.4, places=5)
        self.assertAlmostEqual(joint.hit_radius, 0.02, places=5)

        # Verify the spring references the collider group
        self.assertEqual(len(spring.collider_groups), 1)
        self.assertEqual(
            spring.collider_groups[0].collider_group_name, collider_group.name
        )

    def test_no_vrm0_data_returns_finished(self) -> None:
        context = bpy.context

        bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
        armature = context.object
        if not armature or not isinstance(armature.data, Armature):
            raise AssertionError

        ext = get_armature_extension(armature.data)
        ext.addon_version = addon_version

        # No VRM0 secondary animation data
        result = assign_spring_bone1_from_vrm0(context, armature.name)
        self.assertEqual(result, {"FINISHED"})

        spring_bone1 = ext.spring_bone1
        self.assertEqual(len(spring_bone1.colliders), 0)
        self.assertEqual(len(spring_bone1.springs), 0)

    def test_existing_spring_bone1_data_is_not_overwritten(self) -> None:
        context = bpy.context

        bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
        armature = context.object
        if not armature or not isinstance(armature.data, Armature):
            raise AssertionError

        ext = get_armature_extension(armature.data)
        ext.addon_version = addon_version

        bpy.ops.object.mode_set(mode="EDIT")
        root_bone = armature.data.edit_bones.new("root")
        root_bone.head = Vector((0, 0, 0))
        root_bone.tail = Vector((0, 1, 0))
        bpy.ops.object.mode_set(mode="OBJECT")

        secondary_animation = ext.vrm0.secondary_animation
        bone_group = secondary_animation.bone_groups.add()
        bone_group.comment = "TestGroup"
        root_bone_ref = bone_group.bones.add()
        root_bone_ref.bone_name = "root"

        # Pre-populate spring_bone1 springs to simulate existing data
        spring_bone1 = ext.spring_bone1
        existing_spring = spring_bone1.add_spring()
        existing_spring.vrm_name = "Existing"

        result = assign_spring_bone1_from_vrm0(context, armature.name)
        self.assertEqual(result, {"FINISHED"})

        # Existing spring should still be there and no new springs added
        self.assertEqual(len(spring_bone1.springs), 1)
        self.assertEqual(spring_bone1.springs[0].vrm_name, "Existing")


if __name__ == "__main__":
    main()
