# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import shutil
import sys
from os import environ
from pathlib import Path
from sys import float_info
from unittest import main

import bpy
from bpy.types import Armature
from mathutils import Vector

from io_scene_vrm.common import ops
from io_scene_vrm.editor.make_armature import MIN_BONE_LENGTH
from io_scene_vrm.importer.vrm_diff import vrm_diff

from ..addon_test_case import AddonTestCase


class TestMakeArmature(AddonTestCase):
    def test_make_basic_armature(self) -> None:
        environ["BLENDER_VRM_USE_TEST_EXPORTER_VERSION"] = "true"

        repository_root_dir = Path(__file__).resolve(strict=True).parent.parent.parent
        vrm_dir = Path(
            environ.get(
                "BLENDER_VRM_TEST_RESOURCES_PATH",
                str(repository_root_dir / "tests" / "resources"),
            ),
            "vrm",
        )
        major_minor = f"{bpy.app.version[0]}.{bpy.app.version[1]}"
        vrm = Path("basic_armature.vrm")
        expected_path = vrm_dir / "in" / vrm
        temp_dir_path = vrm_dir / major_minor / "temp"
        temp_dir_path.mkdir(parents=True, exist_ok=True)

        self.assertEqual(ops.icyp.make_basic_armature(), {"FINISHED"})
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})

        actual_path = temp_dir_path / ("test_basic_armature." + vrm.name)
        if actual_path.exists():
            actual_path.unlink()
        ops.export_scene.vrm(filepath=str(actual_path))
        if not expected_path.exists():
            shutil.copy(actual_path, expected_path)

        float_tolerance = 0.000001
        diffs = vrm_diff(
            actual_path.read_bytes(),
            expected_path.read_bytes(),
            float_tolerance,
        )
        if not diffs:
            return

        diffs_str = "\n".join(diffs)
        message = (
            f"Exceeded the VRM diff threshold:{float_tolerance:19.17f}\n"
            + f"left ={actual_path}\n"
            + f"right={expected_path}\n"
            + f"{diffs_str}\n"
        )
        if sys.platform == "win32":
            sys.stderr.buffer.write(message.encode())
            raise AssertionError
        raise AssertionError(message)

    def test_min_bone_length(self) -> None:
        context = bpy.context

        bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
        armature = context.object
        if not armature or not isinstance(armature.data, Armature):
            raise AssertionError

        bpy.ops.object.mode_set(mode="EDIT")
        zero_length_bone = armature.data.edit_bones.new("ZeroLengthBone")
        zero_length_bone.head = Vector((0, 0, 0))
        zero_length_bone.tail = Vector((0, 0, 0))
        bpy.ops.object.mode_set(mode="OBJECT")
        self.assertEqual(len(armature.data.bones), 0)

        bpy.ops.object.mode_set(mode="EDIT")
        bone = armature.data.edit_bones.new("Bone")
        bone.head = Vector((0, 0, 0))
        bone.tail = Vector((0, 0, MIN_BONE_LENGTH))
        bpy.ops.object.mode_set(mode="OBJECT")
        self.assertEqual(len(armature.data.bones), 1)

        bpy.ops.object.mode_set(mode="EDIT")
        too_short_bone_length = MIN_BONE_LENGTH / 10
        too_short_bone = armature.data.edit_bones.new("TooShortBone")
        too_short_bone.head = Vector((0, 0, 0))
        too_short_bone.tail = Vector((0, 0, too_short_bone_length))
        bpy.ops.object.mode_set(mode="OBJECT")
        self.assertGreater(too_short_bone_length, float_info.epsilon)
        self.assertEqual(len(armature.data.bones), 1)


if __name__ == "__main__":
    main()
