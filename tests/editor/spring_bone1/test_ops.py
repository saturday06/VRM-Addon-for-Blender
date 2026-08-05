# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import math
import uuid
from collections.abc import Sequence
from unittest import main

import bpy
from bpy.types import Armature
from mathutils import Euler, Quaternion, Vector

from io_scene_vrm.common import ops, version
from io_scene_vrm.common.convert import Json
from io_scene_vrm.editor import migration
from io_scene_vrm.editor.extension import (
    VrmAddonArmatureExtensionPropertyGroup,
    get_armature_extension,
)
from io_scene_vrm.editor.extension import (
    VrmAddonBoneExtensionPropertyGroup as BoneExtension,
)
from io_scene_vrm.editor.extension_accessor import get_bone_extension
from io_scene_vrm.editor.spring_bone1.handler import (
    _apply_spring_bone_limit,
    _apply_spring_bone_limit_local_direction,
)
from io_scene_vrm.editor.spring_bone1.property_group import (
    SpringBone1ColliderGroupReferencePropertyGroup,
)
from io_scene_vrm.exporter.vrm1_exporter import Vrm1Exporter
from io_scene_vrm.importer.vrm1_importer import Vrm1Importer
from tests.util import AddonTestCase

ADDON_VERSION = version.get_addon_version()
SPEC_VERSION = VrmAddonArmatureExtensionPropertyGroup.SPEC_VERSION_VRM1


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
    def test_spring_bone_simulation_applies_cone_limit(self) -> None:
        context = bpy.context

        bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
        armature = context.object
        if not armature or not isinstance(armature.data, Armature):
            raise AssertionError

        extension = get_armature_extension(armature.data)
        extension.addon_version = ADDON_VERSION
        extension.spec_version = SPEC_VERSION
        extension.spring_bone1.enable_animation = True

        bpy.ops.object.mode_set(mode="EDIT")
        root_bone = armature.data.edit_bones.new("root")
        root_bone.head = Vector((0.0, 0.0, 0.0))
        root_bone.tail = Vector((0.0, 1.0, 0.0))

        head_bone = armature.data.edit_bones.new("head")
        head_bone.parent = root_bone
        head_bone.head = Vector((0.0, 1.0, 0.0))
        head_bone.tail = Vector((0.0, 2.0, 0.0))

        tail_bone = armature.data.edit_bones.new("tail")
        tail_bone.parent = head_bone
        tail_bone.head = Vector((0.0, 2.0, 0.0))
        tail_bone.tail = Vector((0.0, 3.0, 0.0))
        bpy.ops.object.mode_set(mode="OBJECT")

        spring = extension.spring_bone1.add_spring()
        head_joint = spring.add_joint()
        head_joint.node.bone_name = "head"
        head_joint.stiffness = 0.0
        head_joint.gravity_power = 1.0
        head_joint.drag_force = 1.0
        head_joint.vrmc_spring_bone_limit.limit_type = (
            head_joint.vrmc_spring_bone_limit.LIMIT_TYPE_CONE.identifier
        )
        head_joint.vrmc_spring_bone_limit.cone_angle = 0.0
        tail_joint = spring.add_joint()
        tail_joint.node.bone_name = "tail"

        context.view_layer.update()
        ops.vrm.update_spring_bone1_animation(delta_time=1.0)
        context.view_layer.update()

        assert_vector3_equals(
            Vector((0.0, 2.0, 0.0)),
            armature.pose.bones["tail"].head,
            "Cone-limited tail",
        )

    def test_spring_bone_limit_directions(self) -> None:
        context = bpy.context

        bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
        armature = context.object
        if not armature or not isinstance(armature.data, Armature):
            raise AssertionError

        limit = (
            get_armature_extension(armature.data)
            .spring_bone1.add_spring()
            .add_joint()
            .vrmc_spring_bone_limit
        )

        limit.limit_type = limit.LIMIT_TYPE_CONE.identifier
        limit.cone_angle = math.pi / 4.0
        for direction in (Vector((0.0001, -1.0, 0.0)), Vector((0.001, -1.0, 0.0))):
            with self.subTest(direction=direction):
                assert_vector3_equals(
                    Vector((math.sqrt(0.5), math.sqrt(0.5), 0.0)),
                    _apply_spring_bone_limit_local_direction(direction, limit),
                    "Cone near singular direction",
                )
        assert_vector3_equals(
            Vector((0.0, math.sqrt(0.5), math.sqrt(0.5))),
            _apply_spring_bone_limit_local_direction(Vector((0.0, -1.0, 0.0)), limit),
            "Cone singular direction",
        )

        limit.limit_type = limit.LIMIT_TYPE_HINGE.identifier
        limit.hinge_angle = math.pi / 4.0
        assert_vector3_equals(
            Vector((0.0, 1.0, 0.0)),
            _apply_spring_bone_limit_local_direction(Vector((1.0, 0.0, 0.0)), limit),
            "Hinge singular direction",
        )

        limit.limit_type = limit.LIMIT_TYPE_SPHERICAL.identifier
        limit.spherical_pitch = math.pi / 4.0
        limit.spherical_yaw = math.pi / 4.0
        assert_vector3_equals(
            Vector((0.0, math.sqrt(0.5), -math.sqrt(0.5))),
            _apply_spring_bone_limit_local_direction(
                Vector((0.0, -1.0, -0.0001)), limit
            ),
            "Spherical near negative Y",
        )
        assert_vector3_equals(
            Vector((math.sqrt(0.5), 0.5, 0.5)),
            _apply_spring_bone_limit_local_direction(Vector((1.0, 0.0, 0.0001)), limit),
            "Spherical near positive X",
        )
        assert_vector3_equals(
            Vector((0.0, math.sqrt(0.5), math.sqrt(0.5))),
            _apply_spring_bone_limit_local_direction(Vector((0.0, -1.0, 0.0)), limit),
            "Spherical singular direction",
        )

        limit.limit_type = limit.LIMIT_TYPE_CONE.identifier
        limit.cone_angle = 0.0
        rotation = Quaternion((0.0, 0.0, 1.0), math.pi / 2.0)
        limit.rotation = [rotation.w, rotation.x, rotation.y, rotation.z]
        assert_vector3_equals(
            Vector((-1.0, 0.0, 0.0)),
            _apply_spring_bone_limit(
                Vector((0.0, 0.0, 1.0)),
                Vector((0.0, 0.0, 0.0)),
                1.0,
                Quaternion(),
                Quaternion(),
                Vector((0.0, 1.0, 0.0)),
                limit,
            ),
            "Rotated cone direction",
        )

    def test_spring_bone_limit_import_export(self) -> None:
        context = bpy.context

        bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
        armature = context.object
        if not armature or not isinstance(armature.data, Armature):
            raise AssertionError

        bpy.ops.object.mode_set(mode="EDIT")
        bone = armature.data.edit_bones.new("joint")
        bone.head = Vector((0.0, 0.0, 0.0))
        bone.tail = Vector((0.0, 1.0, 0.0))
        tail_bone = armature.data.edit_bones.new("tail")
        tail_bone.parent = bone
        tail_bone.head = Vector((0.0, 1.0, 0.0))
        tail_bone.tail = Vector((0.0, 2.0, 0.0))
        bpy.ops.object.mode_set(mode="OBJECT")

        spring_bone = get_armature_extension(armature.data).spring_bone1
        spring = spring_bone.add_spring()
        joint = spring.add_joint()
        joint.node.bone_name = "joint"
        tail_joint = spring.add_joint()
        tail_joint.node.bone_name = "tail"
        tail_joint.vrmc_spring_bone_limit.limit_type = (
            tail_joint.vrmc_spring_bone_limit.LIMIT_TYPE_CONE.identifier
        )
        limit = joint.vrmc_spring_bone_limit
        limit.limit_type = limit.LIMIT_TYPE_SPHERICAL.identifier
        limit.spherical_pitch = 0.75
        limit.spherical_yaw = 0.25
        rotation = Quaternion((0.0, 1.0, 0.0), 0.5)
        limit.rotation = [rotation.w, rotation.x, rotation.y, rotation.z]

        extensions_used: list[Json] = []
        spring_dicts = Vrm1Exporter.create_spring_bone_spring_dicts(
            extensions_used,
            spring_bone,
            {"joint": 0, "tail": 1},
            {},
            armature,
        )
        self.assertEqual(extensions_used, ["VRMC_springBone_limit"])
        expected_rotation: list[Json] = [
            rotation.x,
            rotation.y,
            rotation.z,
            rotation.w,
        ]
        expected_extension: dict[str, Json] = {
            "VRMC_springBone_limit": {
                "specVersion": "1.0",
                "limit": {
                    "spherical": {
                        "pitch": 0.75,
                        "yaw": 0.25,
                        "rotation": expected_rotation,
                    }
                },
            }
        }
        self.assertEqual(
            spring_dicts,
            [
                {
                    "name": "Spring",
                    "joints": [
                        {
                            "node": 0,
                            "hitRadius": 0.0,
                            "stiffness": 1.0,
                            "gravityPower": 0.0,
                            "gravityDir": [0.0, -1.0, 0.0],
                            "dragForce": 0.5,
                            "extensions": expected_extension,
                        },
                        {
                            "node": 1,
                            "hitRadius": 0.0,
                            "stiffness": 1.0,
                            "gravityPower": 0.0,
                            "gravityDir": [0.0, -1.0, 0.0],
                            "dragForce": 0.5,
                        },
                    ],
                }
            ],
        )

        terminal_extensions_used: list[Json] = []
        terminal_springs = Vrm1Exporter.create_spring_bone_spring_dicts(
            terminal_extensions_used, spring_bone, {"joint": 0}, {}, armature
        )
        terminal_spring = terminal_springs[0]
        if not isinstance(terminal_spring, dict):
            self.fail("Expected a spring object")
        terminal_joints = terminal_spring["joints"]
        if not isinstance(terminal_joints, list):
            self.fail("Expected a joints array")
        terminal_joint = terminal_joints[0]
        if not isinstance(terminal_joint, dict):
            self.fail("Expected a joint object")
        self.assertNotIn("extensions", terminal_joint)
        self.assertEqual(terminal_extensions_used, [])

        imported_joint = spring.add_joint()
        imported_joint_dict: dict[str, Json] = {"extensions": expected_extension}
        Vrm1Importer.load_spring_bone1_joint_limit(imported_joint, imported_joint_dict)
        imported_limit = imported_joint.vrmc_spring_bone_limit
        self.assertEqual(
            imported_limit.limit_type,
            imported_limit.LIMIT_TYPE_SPHERICAL.identifier,
        )
        self.assertAlmostEqual(imported_limit.spherical_pitch, 0.75)
        self.assertAlmostEqual(imported_limit.spherical_yaw, 0.25)
        self.assertLess(
            imported_limit.rotation_quaternion()
            .rotation_difference(limit.rotation_quaternion())
            .angle,
            0.0001,
        )

        bone = armature.data.bones["joint"]
        get_bone_extension(
            bone
        ).axis_translation = (
            BoneExtension.AXIS_TRANSLATION_MINUS_Y_TO_Y_AROUND_Z.identifier
        )
        Vrm1Importer.load_spring_bone1_joint_limit(
            imported_joint, imported_joint_dict, bone, armature.data.bones["tail"]
        )
        expected_imported_rotation = (
            Quaternion((0.0, 0.0, 1.0), math.pi)
            @ Quaternion((1.0, 0.0, 0.0), math.pi)
            @ rotation
        )
        self.assertLess(
            imported_limit.rotation_quaternion()
            .rotation_difference(expected_imported_rotation)
            .angle,
            0.0001,
        )

        Vrm1Importer.load_spring_bone1_joint_limit(
            imported_joint,
            {
                "extensions": {
                    "VRMC_springBone_limit": {
                        "specVersion": "1.0",
                        "limit": {"cone": {"angle": 0.0}},
                    }
                }
            },
            bone,
            armature.data.bones["tail"],
        )
        assert_vector3_equals(
            Vector((-1.0, 0.0, 0.0)),
            imported_limit.rotation_quaternion() @ Vector((1.0, 0.0, 0.0)),
            "Default rotation with imported node axes",
        )
        assert_vector3_equals(
            Vector((0.0, 0.0, -1.0)),
            imported_limit.rotation_quaternion() @ Vector((0.0, 0.0, 1.0)),
            "Default rotation with imported node axes",
        )

        unknown_version_joint = spring.add_joint()
        Vrm1Importer.load_spring_bone1_joint_limit(
            unknown_version_joint,
            {
                "extensions": {
                    "VRMC_springBone_limit": {
                        "specVersion": "2.0",
                        "limit": {"cone": {"angle": 0.0}},
                    }
                }
            },
        )
        self.assertEqual(
            unknown_version_joint.vrmc_spring_bone_limit.limit_type,
            unknown_version_joint.vrmc_spring_bone_limit.LIMIT_TYPE_NONE.identifier,
        )

    def test_unmanaged_addon_version_migration_preserves_current_gravity_dir(
        self,
    ) -> None:
        context = bpy.context

        bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
        armature = context.object
        if not armature or not isinstance(armature.data, Armature):
            raise AssertionError

        ext = get_armature_extension(armature.data)
        ext.addon_version = ext.UNMANAGED_ADDON_VERSION
        ext.spec_version = SPEC_VERSION
        ext.spring_bone1.initial_automatic_spring_bone_assignment = False

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

        joint = ext.spring_bone1.springs[0].joints[0]
        original_gravity_dir = tuple(joint.gravity_dir)

        self.assertTrue(migration.migrate(context, armature.name, heavy_migration=True))

        assert_vector3_equals(
            Vector(original_gravity_dir),
            joint.gravity_dir,
            "Unmanaged addon version migration gravity direction",
        )

    def test_unmanaged_addon_version_migration_with_legacy_metadata(self) -> None:
        context = bpy.context

        bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
        armature = context.object
        if not armature or not isinstance(armature.data, Armature):
            raise AssertionError

        ext = get_armature_extension(armature.data)
        ext.addon_version = ext.UNMANAGED_ADDON_VERSION
        armature["humanoid_params"] = "{}"
        armature.data["hips"] = ""

        self.assertTrue(migration.migrate(context, armature.name, heavy_migration=True))
        self.assertEqual(tuple(ext.addon_version), ADDON_VERSION)
        self.assertEqual(ext.spec_version, ext.SPEC_VERSION_VRM0)

    def test_one_joint_extending_in_y_direction(self) -> None:
        context = bpy.context

        bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
        armature = context.object
        if not armature or not isinstance(armature.data, Armature):
            raise AssertionError

        get_armature_extension(armature.data).addon_version = ADDON_VERSION
        get_armature_extension(armature.data).spec_version = SPEC_VERSION
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

        get_armature_extension(armature.data).addon_version = ADDON_VERSION
        get_armature_extension(armature.data).spec_version = SPEC_VERSION
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

        get_armature_extension(armature.data).addon_version = ADDON_VERSION
        get_armature_extension(armature.data).spec_version = SPEC_VERSION
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

        get_armature_extension(armature.data).addon_version = ADDON_VERSION
        get_armature_extension(armature.data).spec_version = SPEC_VERSION
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

        get_armature_extension(armature.data).addon_version = ADDON_VERSION
        get_armature_extension(armature.data).spec_version = SPEC_VERSION
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

        get_armature_extension(armature.data).addon_version = ADDON_VERSION
        get_armature_extension(armature.data).spec_version = SPEC_VERSION
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

        get_armature_extension(armature.data).addon_version = ADDON_VERSION
        get_armature_extension(armature.data).spec_version = SPEC_VERSION
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

        get_armature_extension(armature.data).addon_version = ADDON_VERSION
        get_armature_extension(armature.data).spec_version = SPEC_VERSION
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

        get_armature_extension(armature.data).addon_version = ADDON_VERSION
        get_armature_extension(armature.data).spec_version = SPEC_VERSION
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

        get_armature_extension(armature.data).addon_version = ADDON_VERSION
        get_armature_extension(armature.data).spec_version = SPEC_VERSION
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

        get_armature_extension(armature.data).addon_version = ADDON_VERSION
        get_armature_extension(armature.data).spec_version = SPEC_VERSION
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

        get_armature_extension(armature.data).addon_version = ADDON_VERSION
        get_armature_extension(armature.data).spec_version = SPEC_VERSION
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

        get_armature_extension(armature.data).addon_version = ADDON_VERSION
        get_armature_extension(armature.data).spec_version = SPEC_VERSION
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

        get_armature_extension(armature.data).addon_version = ADDON_VERSION
        get_armature_extension(armature.data).spec_version = SPEC_VERSION
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

    def test_capsule_collider_uses_capsule_radius(self) -> None:
        context = bpy.context

        bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
        armature = context.object
        if not armature or not isinstance(armature.data, Armature):
            raise AssertionError

        ext = get_armature_extension(armature.data)
        ext.addon_version = ADDON_VERSION
        ext.spec_version = SPEC_VERSION
        ext.spring_bone1.enable_animation = True

        bpy.ops.object.mode_set(mode="EDIT")
        joint_bone0 = armature.data.edit_bones.new("joint0")
        joint_bone0.head = Vector((0, 0, 0))
        joint_bone0.tail = Vector((0, 1, 0))

        joint_bone1 = armature.data.edit_bones.new("joint1")
        joint_bone1.parent = joint_bone0
        joint_bone1.head = Vector((0, 1, 0))
        joint_bone1.tail = Vector((0, 2, 0))
        bpy.ops.object.mode_set(mode="OBJECT")

        spring_bone1 = ext.spring_bone1
        spring = spring_bone1.add_spring()
        joint0 = spring.add_joint()
        joint0.node.bone_name = "joint0"
        joint0.gravity_power = 0
        joint0.drag_force = 1
        joint0.stiffness = 0
        joint0.hit_radius = 0
        joint1 = spring.add_joint()
        joint1.node.bone_name = "joint1"
        joint1.gravity_power = 0
        joint1.drag_force = 1
        joint1.stiffness = 0
        joint1.hit_radius = 0

        collider = spring_bone1.add_collider(context, armature)
        collider.node.bone_name = "joint0"
        collider.shape_type = collider.SHAPE_TYPE_CAPSULE.identifier
        collider.shape.sphere.radius = 0
        collider.shape.capsule.radius = 0.25
        collider.shape.capsule.offset = (0.2, 0.5, 0)
        collider.shape.capsule.tail = (0.2, 1.5, 0)

        collider_group = spring_bone1.add_collider_group()
        collider_reference = collider_group.add_collider()
        collider_reference.collider_uuid = collider.uuid
        collider_group_reference = spring.add_collider_group()
        collider_group_reference.collider_group_uuid = collider_group.uuid

        context.view_layer.update()

        ops.vrm.update_spring_bone1_animation(delta_time=1)
        context.view_layer.update()

        self.assertLess(armature.pose.bones["joint1"].head.x, -0.01)


class TestAssignSpringBone1FromVrm0(AddonTestCase):
    def test_collider_group_and_spring_mapping(self) -> None:
        context = bpy.context

        bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
        armature = context.object
        if not armature or not isinstance(armature.data, Armature):
            raise AssertionError

        ext = get_armature_extension(armature.data)
        ext.addon_version = ADDON_VERSION

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

        result = ops.vrm.assign_spring_bone1_from_vrm0(
            armature_object_name=armature.name
        )
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
            spring.collider_groups[0].collider_group_uuid, collider_group.uuid
        )

    def test_no_vrm0_data_returns_finished(self) -> None:
        context = bpy.context

        bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
        armature = context.object
        if not armature or not isinstance(armature.data, Armature):
            raise AssertionError

        ext = get_armature_extension(armature.data)
        ext.addon_version = ADDON_VERSION

        # No VRM0 secondary animation data
        result = ops.vrm.assign_spring_bone1_from_vrm0(
            armature_object_name=armature.name
        )
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
        ext.addon_version = ADDON_VERSION

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

        result = ops.vrm.assign_spring_bone1_from_vrm0(
            armature_object_name=armature.name
        )
        self.assertEqual(result, {"FINISHED"})

        # Existing spring should still be there and no new springs added
        self.assertEqual(len(spring_bone1.springs), 1)
        self.assertEqual(spring_bone1.springs[0].vrm_name, "Existing")


class TestAssignUnassignSpringColliderGroup(AddonTestCase):
    """Tests for VRM_OT_assign/unassign_spring_bone1_spring_collider_group operators."""

    def setup_armature_with_spring_and_collider_group(
        self,
    ) -> tuple[Armature, SpringBone1ColliderGroupReferencePropertyGroup, str]:
        """Set up an armature with one spring and one collider group.

        Returns (armature_data, collider_group_reference, collider_group_uuid).
        """
        context = bpy.context

        bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
        armature = context.object
        if not armature or not isinstance(armature.data, Armature):
            raise AssertionError

        ext = get_armature_extension(armature.data)
        ext.addon_version = ADDON_VERSION
        ext.spec_version = SPEC_VERSION

        spring_bone1 = ext.spring_bone1

        # Add a collider group with a known UUID
        collider_group = spring_bone1.add_collider_group()
        collider_group_uuid = collider_group.uuid

        # Add a spring with one collider group reference slot
        spring = spring_bone1.add_spring()
        collider_group_reference = spring.add_collider_group()

        return armature.data, collider_group_reference, collider_group_uuid

    def test_assign_spring_collider_group_sets_uuid(self) -> None:
        """Assigning a valid collider group UUID sets collider_group_uuid."""
        armature_data, collider_group_reference, collider_group_uuid = (
            self.setup_armature_with_spring_and_collider_group()
        )

        reference_path = collider_group_reference.path_from_id()

        result = ops.vrm.assign_spring_bone1_spring_collider_group(
            armature_data_name=armature_data.name,
            collider_group_reference_path=reference_path,
            collider_group_uuid=collider_group_uuid,
        )
        self.assertEqual(result, {"FINISHED"})
        self.assertEqual(
            collider_group_reference.collider_group_uuid, collider_group_uuid
        )

    def test_assign_spring_collider_group_empty_uuid_clears(self) -> None:
        """Assigning an empty UUID clears collider_group_uuid."""
        armature_data, collider_group_reference, collider_group_uuid = (
            self.setup_armature_with_spring_and_collider_group()
        )

        reference_path = collider_group_reference.path_from_id()

        # First assign a valid UUID, then clear it
        collider_group_reference.collider_group_uuid = collider_group_uuid

        result = ops.vrm.assign_spring_bone1_spring_collider_group(
            armature_data_name=armature_data.name,
            collider_group_reference_path=reference_path,
            collider_group_uuid="",
        )
        self.assertEqual(result, {"FINISHED"})
        self.assertEqual(collider_group_reference.collider_group_uuid, "")

    def test_assign_spring_collider_group_unknown_uuid_cancels(self) -> None:
        """Assigning an unknown UUID returns CANCELLED and leaves uuid unchanged."""
        armature_data, collider_group_reference, _collider_group_uuid = (
            self.setup_armature_with_spring_and_collider_group()
        )

        reference_path = collider_group_reference.path_from_id()
        unknown_uuid = uuid.uuid4().hex

        result = ops.vrm.assign_spring_bone1_spring_collider_group(
            armature_data_name=armature_data.name,
            collider_group_reference_path=reference_path,
            collider_group_uuid=unknown_uuid,
        )
        self.assertEqual(result, {"CANCELLED"})
        self.assertEqual(collider_group_reference.collider_group_uuid, "")

    def test_assign_spring_collider_group_invalid_armature_cancels(self) -> None:
        """Assigning with a non-existent armature data name returns CANCELLED."""
        _armature_data, collider_group_reference, collider_group_uuid = (
            self.setup_armature_with_spring_and_collider_group()
        )

        reference_path = collider_group_reference.path_from_id()

        result = ops.vrm.assign_spring_bone1_spring_collider_group(
            armature_data_name="__nonexistent_armature__",
            collider_group_reference_path=reference_path,
            collider_group_uuid=collider_group_uuid,
        )
        self.assertEqual(result, {"CANCELLED"})

    def test_unassign_spring_collider_group_clears_uuid(self) -> None:
        """Unassigning a collider group clears collider_group_uuid."""
        armature_data, collider_group_reference, collider_group_uuid = (
            self.setup_armature_with_spring_and_collider_group()
        )

        reference_path = collider_group_reference.path_from_id()

        # First assign a valid UUID
        collider_group_reference.collider_group_uuid = collider_group_uuid

        result = ops.vrm.unassign_spring_bone1_spring_collider_group(
            armature_data_name=armature_data.name,
            collider_group_reference_path=reference_path,
        )
        self.assertEqual(result, {"FINISHED"})
        self.assertEqual(collider_group_reference.collider_group_uuid, "")

    def test_unassign_spring_collider_group_invalid_armature_cancels(self) -> None:
        """Unassigning with a non-existent armature data name returns CANCELLED."""
        _armature_data, collider_group_reference, _collider_group_uuid = (
            self.setup_armature_with_spring_and_collider_group()
        )

        reference_path = collider_group_reference.path_from_id()

        result = ops.vrm.unassign_spring_bone1_spring_collider_group(
            armature_data_name="__nonexistent_armature__",
            collider_group_reference_path=reference_path,
        )
        self.assertEqual(result, {"CANCELLED"})


class TestRemoveSpringBone1ColliderClampsIndex(AddonTestCase):
    """Regression tests for active index clamping after collider/group removal."""

    def test_remove_collider_clamps_collider_group_active_collider_index(
        self,
    ) -> None:
        """Removing a collider clamps collider_group.active_collider_index."""
        context = bpy.context

        bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
        armature = context.object
        if not armature or not isinstance(armature.data, Armature):
            raise AssertionError

        ext = get_armature_extension(armature.data)
        ext.addon_version = ADDON_VERSION
        ext.spec_version = SPEC_VERSION

        spring_bone1 = ext.spring_bone1

        # Add a collider and capture its UUID
        self.assertEqual(
            ops.vrm.add_spring_bone1_collider(armature_object_name=armature.name),
            {"FINISHED"},
        )
        collider_uuid = spring_bone1.colliders[0].uuid

        # Add a collider group with a reference pointing to the collider
        collider_group = spring_bone1.add_collider_group()
        collider_ref = collider_group.add_collider()
        collider_ref.collider_uuid = collider_uuid

        # Set active_collider_index to an out-of-range value
        collider_group.active_collider_index = 999

        # Remove the collider; this also removes the reference inside the group
        self.assertEqual(
            ops.vrm.remove_spring_bone1_collider(
                armature_object_name=armature.name, collider_index=0
            ),
            {"FINISHED"},
        )

        # Index must be clamped to max(0, len(colliders) - 1) == 0
        self.assertEqual(collider_group.active_collider_index, 0)

    def test_remove_collider_group_clamps_spring_active_collider_group_index(
        self,
    ) -> None:
        """Removing a collider group clamps spring.active_collider_group_index."""
        context = bpy.context

        bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
        armature = context.object
        if not armature or not isinstance(armature.data, Armature):
            raise AssertionError

        ext = get_armature_extension(armature.data)
        ext.addon_version = ADDON_VERSION
        ext.spec_version = SPEC_VERSION

        spring_bone1 = ext.spring_bone1

        # Add a collider group and capture its UUID
        collider_group = spring_bone1.add_collider_group()
        collider_group_uuid = collider_group.uuid

        # Add a spring with a collider group reference
        spring = spring_bone1.add_spring()
        collider_group_ref = spring.add_collider_group()
        collider_group_ref.collider_group_uuid = collider_group_uuid

        # Set active_collider_group_index to an out-of-range value
        spring.active_collider_group_index = 999

        # Remove the collider group; this also removes the reference from the spring
        self.assertEqual(
            ops.vrm.remove_spring_bone1_collider_group(
                armature_object_name=armature.name, collider_group_index=0
            ),
            {"FINISHED"},
        )

        # Index must be clamped to max(0, len(collider_groups) - 1) == 0
        self.assertEqual(spring.active_collider_group_index, 0)


if __name__ == "__main__":
    main()
