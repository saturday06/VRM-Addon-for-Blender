# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import functools
import sys
from os import environ
from pathlib import Path
from unittest import TestCase, main

import bpy

from io_scene_vrm.common import ops
from io_scene_vrm.common.debug import clean_scene
from io_scene_vrm.common.logger import get_logger

logger = get_logger(__name__)

repository_root_dir = Path(__file__).resolve(strict=True).parent.parent.parent
resources_dir = Path(
    environ.get(
        "BLENDER_VRM_TEST_RESOURCES_PATH",
        str(repository_root_dir / "tests" / "resources"),
    )
)
major_minor = f"{bpy.app.version[0]}.{bpy.app.version[1]}"
vrm_dir = resources_dir / "vrm"
blend_dir = resources_dir / "blend"


class TestImportNonObjectMode(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        bpy.ops.preferences.addon_enable(module="io_scene_vrm")

    def setUp(self) -> None:
        clean_scene(bpy.context)

    def test_import_non_object_mode(self) -> None:
        bpy.ops.preferences.addon_enable(module="io_scene_vrm")
        self.assertEqual(ops.icyp.make_basic_armature(), {"FINISHED"})
        self.assertEqual(bpy.ops.object.posemode_toggle(), {"FINISHED"})
        self.assertEqual(
            ops.import_scene.vrm(
                filepath=str(
                    Path(__file__).parent.parent
                    / "resources"
                    / "vrm"
                    / "in"
                    / "triangle.vrm"
                )
            ),
            {"FINISHED"},
        )


class __TestImportSceneBrokenVrmBase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        bpy.ops.preferences.addon_enable(module="io_scene_vrm")

    def setUp(self) -> None:
        clean_scene(bpy.context)

    def assert_broken_vrm(self, vrm_path: Path) -> None:
        environ["BLENDER_VRM_AUTOMATIC_LICENSE_CONFIRMATION"] = "true"

        if (
            vrm_path.name == "draco.vrm"
            and sys.platform == "linux"
            and not bpy.app.binary_path
        ):
            # Linuxかつmoduleとしてビルドされている場合、dracoのライブラリが読めなくて
            # エラーになるので該当するテストは実施しない
            return

        self.assertEqual(ops.import_scene.vrm(filepath=str(vrm_path)), {"FINISHED"})


TestImportSceneBrokenVrm = type(
    "TestImportSceneBrokenVrm",
    (__TestImportSceneBrokenVrmBase,),
    {
        "test_" + path.stem: functools.partialmethod(
            __TestImportSceneBrokenVrmBase.assert_broken_vrm, path
        )
        for path in sorted((resources_dir / "vrm" / "broken").glob("*.vrm"))
    },
)

if __name__ == "__main__":
    main()
