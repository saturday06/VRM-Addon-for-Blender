# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import math
import struct
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import main

import bpy
from bpy.types import Armature, Object
from mathutils import Euler, Matrix, Quaternion, Vector

from io_scene_vrm.common import ops
from io_scene_vrm.common.convert import Json
from io_scene_vrm.common.gltf import pack_glb
from io_scene_vrm.editor.extension_accessor import get_armature_extension
from io_scene_vrm.importer.vrm_animation_importer import VrmAnimationImporter
from tests.util import AddonTestCase


class TestVrmAnimationImporter(AddonTestCase):
    def make_armature(self, transform: Matrix, *, parented: bool) -> Object:
        self.assertEqual(ops.icyp.make_basic_armature(), {"FINISHED"})
        armature = bpy.context.object
        if not armature or not isinstance(armature.data, Armature):
            raise AssertionError
        ext = get_armature_extension(armature.data)
        ext.spec_version = ext.SPEC_VERSION_VRM1
        ext.vrm1.humanoid.pose = ext.vrm1.humanoid.POSE_CURRENT_POSE.identifier
        # Keep the world rest pose identical while changing the object basis.
        armature.data.transform(transform.inverted())
        if parented:
            parent = bpy.data.objects.new("RotatedParent", None)
            bpy.context.scene.collection.objects.link(parent)
            parent.matrix_world = transform
            armature.parent = parent
        else:
            armature.matrix_world = transform
        bpy.context.view_layer.update()
        return armature

    @staticmethod
    def write_animation(
        path: Path,
        *,
        translation: bool = False,
        source_scale: tuple[float, float, float] = (1, 1, 1),
    ) -> None:
        binary = bytearray(struct.pack("<3f", 0, 1 / 8, 1 / 4))
        for axis in ((0, 0, 1), (1, 0, 0)):
            for angle in (0, math.pi / 4, -math.pi / 6):
                rotation = Quaternion(axis, angle)
                binary.extend(
                    struct.pack("<4f", rotation.x, rotation.y, rotation.z, rotation.w)
                )
        for position in ((0, 1, 0), (0.2, 1.3, -0.4), (-0.1, 0.8, 0.25)):
            binary.extend(struct.pack("<3f", *position))
        channels: list[Json] = [
            {"sampler": 0, "target": {"node": 0, "path": "rotation"}},
            {"sampler": 1, "target": {"node": 1, "path": "rotation"}},
        ]
        if translation:
            channels.append(
                {"sampler": 2, "target": {"node": 0, "path": "translation"}}
            )
        vrma: dict[str, Json] = {
            "asset": {"version": "2.0"},
            "extensionsUsed": ["VRMC_vrm_animation"],
            "extensions": {
                "VRMC_vrm_animation": {
                    "specVersion": "1.0",
                    "humanoid": {
                        "humanBones": {"hips": {"node": 0}, "spine": {"node": 1}}
                    },
                }
            },
            "nodes": [
                {"translation": [0, 1, 0], "children": [1]},
                {"translation": [0, 0.3, 0]},
                {"children": [0], "scale": list(source_scale)},
            ],
            "scenes": [{"nodes": [2]}],
            "scene": 0,
            "buffers": [{"byteLength": len(binary)}],
            "bufferViews": [
                {"buffer": 0, "byteOffset": 0, "byteLength": 12},
                {"buffer": 0, "byteOffset": 12, "byteLength": 48},
                {"buffer": 0, "byteOffset": 60, "byteLength": 48},
                {"buffer": 0, "byteOffset": 108, "byteLength": 36},
            ],
            "accessors": [
                {
                    "bufferView": 0,
                    "componentType": 5126,
                    "count": 3,
                    "type": "SCALAR",
                    "min": [0],
                    "max": [1 / 4],
                },
                {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC4"},
                {"bufferView": 2, "componentType": 5126, "count": 3, "type": "VEC4"},
                {"bufferView": 3, "componentType": 5126, "count": 3, "type": "VEC3"},
            ],
            "animations": [
                {
                    "channels": channels,
                    "samplers": [
                        {"input": 0, "output": 1, "interpolation": "LINEAR"},
                        {"input": 0, "output": 2, "interpolation": "LINEAR"},
                        {"input": 0, "output": 3, "interpolation": "LINEAR"},
                    ],
                }
            ],
        }
        path.write_bytes(pack_glb(vrma, binary))

    def test_hips_translation_with_object_transform(self) -> None:
        scene = bpy.context.scene
        scene.render.fps = 24
        scene.render.fps_base = 1
        rotation = Euler((0.3, -0.5, 0.7)).to_matrix().to_4x4()
        nonuniform_scale = Matrix.Diagonal((0.5, 2, 3, 1))
        transforms = (
            Matrix.Identity(4),
            Euler((math.pi / 2, 0, 0)).to_matrix().to_4x4(),
            rotation,
            Matrix.Diagonal((0.01, 0.01, 0.01, 1)),
            Matrix.Diagonal((100, 100, 100, 1)),
            nonuniform_scale,
            rotation @ nonuniform_scale,
        )
        with TemporaryDirectory() as directory:
            path = Path(directory) / "translation.vrma"
            self.write_animation(path, translation=True)
            for transform in transforms:
                for parented in (False, True):
                    with self.subTest(transform=transform, parented=parented):
                        scene.frame_set(1)
                        armature = self.make_armature(transform, parented=parented)
                        # Scene placement must not affect the height ratio.
                        armature.matrix_world.translation = Vector((2, -3, 4))
                        bpy.context.view_layer.update()
                        self.assert_hips_translation(armature, path, Vector((1, 1, 1)))

    def test_hips_translation_with_source_scale_and_pose_offset(self) -> None:
        scene = bpy.context.scene
        scene.render.fps = 24
        scene.render.fps_base = 1
        with TemporaryDirectory() as directory:
            path = Path(directory) / "translation.vrma"
            for source_scale in ((1, 1, 1), (2, 2, 2), (2, 3, 4)):
                for posed in (False, True):
                    with self.subTest(source_scale=source_scale, posed=posed):
                        scene.frame_set(1)
                        self.write_animation(
                            path, translation=True, source_scale=source_scale
                        )
                        armature = self.make_armature(
                            Matrix.Identity(4), parented=False
                        )
                        # Also cover a model whose actual world size is doubled.
                        armature.scale = Vector((2, 2, 2))
                        if posed:
                            armature_data = armature.data
                            if not isinstance(armature_data, Armature):
                                raise TypeError
                            hips_name = get_armature_extension(
                                armature_data
                            ).vrm1.humanoid.human_bones.hips.node.bone_name
                            hips = armature.pose.bones[hips_name]
                            hips.location = Vector((0.1, 0.2, 0.3))
                            hips.rotation_mode = "QUATERNION"
                            hips.rotation_quaternion = Euler(
                                (0.2, -0.4, 0.6)
                            ).to_quaternion()
                            hips.scale = Vector((0.7, 1.3, 2))
                        bpy.context.view_layer.update()
                        self.assert_hips_translation(
                            armature,
                            path,
                            Vector((source_scale[0], source_scale[2], source_scale[1])),
                        )

    def test_hips_translation_with_parent_bone(self) -> None:
        scene = bpy.context.scene
        scene.render.fps = 24
        scene.render.fps_base = 1
        with TemporaryDirectory() as directory:
            path = Path(directory) / "translation.vrma"
            self.write_animation(path, translation=True)
            for local_location in (False, True):
                with self.subTest(local_location=local_location):
                    scene.frame_set(1)
                    armature = self.make_armature(Matrix.Identity(4), parented=False)
                    armature_data = armature.data
                    if not isinstance(armature_data, Armature):
                        raise TypeError
                    hips_name = get_armature_extension(
                        armature_data
                    ).vrm1.humanoid.human_bones.hips.node.bone_name
                    bpy.ops.object.mode_set(mode="EDIT")
                    hips = armature_data.edit_bones[hips_name]
                    parent = armature_data.edit_bones.new("TranslationParent")
                    parent.head = hips.head - Vector((0, 0, 0.2))
                    parent.tail = hips.head
                    hips.parent = parent
                    hips.use_connect = True
                    hips.use_local_location = local_location
                    bpy.ops.object.mode_set(mode="OBJECT")
                    parent_pose = armature.pose.bones["TranslationParent"]
                    parent_pose.rotation_mode = "QUATERNION"
                    parent_pose.rotation_quaternion = Euler(
                        (0.2, -0.4, 0.6)
                    ).to_quaternion()
                    parent_pose.scale = Vector((0.7, 1.3, 2))
                    bpy.context.view_layer.update()
                    self.assert_hips_translation(armature, path, Vector((1, 1, 1)))

    def assert_hips_translation(
        self, armature: Object, path: Path, source_scale: Vector
    ) -> None:
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            raise TypeError
        hips_name = get_armature_extension(
            armature_data
        ).vrm1.humanoid.human_bones.hips.node.bone_name
        hips = armature.pose.bones[hips_name]
        initial_position = (armature.matrix_world @ hips.matrix).translation.copy()
        height = initial_position.z - armature.matrix_world.translation.z
        object_matrix = armature.matrix_world.copy()
        rest_matrices = {
            bone.name: bone.matrix_local.copy() for bone in armature_data.bones
        }
        self.assertEqual(
            VrmAnimationImporter.execute(bpy.context, path, armature), {"FINISHED"}
        )
        offsets = (
            Vector((0, 0, 0)),
            Vector((0.2, 0.4, 0.3)),
            Vector((-0.1, -0.25, -0.2)),
        )
        for frame in range(1, 8):
            if frame <= 4:
                offset = offsets[0].lerp(offsets[1], (frame - 1) / 3)
            else:
                offset = offsets[1].lerp(offsets[2], (frame - 4) / 3)
            expected = initial_position + Vector(
                tuple(value * scale for value, scale in zip(offset, source_scale))
            ) * (height / source_scale.z)
            bpy.context.scene.frame_set(frame)
            actual = (armature.matrix_world @ hips.matrix).translation
            for actual_value, expected_value in zip(actual, expected):
                self.assertAlmostEqual(
                    actual_value, expected_value, delta=0.00001, msg=f"frame={frame}"
                )
            self.assertEqual(armature.matrix_world, object_matrix)
            for bone in armature_data.bones:
                # Disconnecting hips enters edit mode, which can round bone rolls.
                for actual_row, expected_row in zip(
                    bone.matrix_local, rest_matrices[bone.name]
                ):
                    for actual_value, expected_value in zip(actual_row, expected_row):
                        self.assertAlmostEqual(
                            actual_value, expected_value, delta=0.00001
                        )

    def test_world_rotation_with_object_rotation(self) -> None:
        scene = bpy.context.scene
        scene.render.fps = 24
        scene.render.fps_base = 1
        with TemporaryDirectory() as directory:
            path = Path(directory) / "rotation.vrma"
            self.write_animation(path)
            reference = self.make_armature(Matrix.Identity(4), parented=False)
            self.assertEqual(
                VrmAnimationImporter.execute(bpy.context, path, reference), {"FINISHED"}
            )
            expected: dict[int, dict[str, Matrix]] = {}
            for frame in range(1, 8):
                scene.frame_set(frame)
                expected[frame] = {
                    bone.name: (reference.matrix_world @ bone.matrix)
                    .to_quaternion()
                    .to_matrix()
                    for bone in reference.pose.bones
                }
            self.assertTrue(
                any(expected[1][name] != expected[4][name] for name in expected[1])
            )
            for angles, parented in (
                ((0, 0, 0), False),
                ((math.pi / 2, 0, 0), False),
                ((0.3, -0.5, 0.7), False),
                ((0.3, -0.5, 0.7), True),
            ):
                with self.subTest(angles=angles, parented=parented):
                    scene.frame_set(1)
                    armature = self.make_armature(
                        Euler(angles).to_matrix().to_4x4(), parented=parented
                    )
                    armature_data = armature.data
                    if not isinstance(armature_data, Armature):
                        raise TypeError
                    object_matrix = armature.matrix_world.copy()
                    rest_matrices = {
                        bone.name: bone.matrix_local.copy()
                        for bone in armature_data.bones
                    }
                    self.assertEqual(
                        VrmAnimationImporter.execute(bpy.context, path, armature),
                        {"FINISHED"},
                    )
                    for frame, rotations in expected.items():
                        scene.frame_set(frame)
                        self.assertEqual(armature.matrix_world, object_matrix)
                        for bone in armature_data.bones:
                            self.assertEqual(
                                bone.matrix_local, rest_matrices[bone.name]
                            )
                        for bone in armature.pose.bones:
                            actual = (
                                (armature.matrix_world @ bone.matrix)
                                .to_quaternion()
                                .to_matrix()
                            )
                            for actual_row, expected_row in zip(
                                actual, rotations[bone.name]
                            ):
                                for actual_value, expected_value in zip(
                                    actual_row, expected_row
                                ):
                                    self.assertAlmostEqual(
                                        actual_value,
                                        expected_value,
                                        delta=0.00001,
                                        msg=f"frame={frame}, bone={bone.name}",
                                    )


if __name__ == "__main__":
    main()
