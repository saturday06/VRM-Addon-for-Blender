# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import functools
import sys
from os import environ
from pathlib import Path
from unittest import main

import bpy

from io_scene_vrm.common import ops
from io_scene_vrm.common.logger import get_logger
from io_scene_vrm.common.test_helper import AddonTestCase

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


class TestImportNonObjectMode(AddonTestCase):
    def test_import_non_object_mode(self) -> None:
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


class __TestImportSceneBrokenVrmBase(AddonTestCase):
    def assert_broken_vrm(self, vrm_path: Path) -> None:
        environ["BLENDER_VRM_AUTOMATIC_LICENSE_CONFIRMATION"] = "true"

        success = True
        if (
            vrm_path.name == "draco.vrm"
            and sys.platform == "linux"
            and not bpy.app.binary_path
        ):
            # On Linux when built as a module, the draco library cannot be read
            # and causes an error
            success = False
        elif bpy.app.version >= (4, 5) and vrm_path.name == "empty.vrm":
            success = False

        if success:
            self.assertEqual(ops.import_scene.vrm(filepath=str(vrm_path)), {"FINISHED"})
            return

        self.assertRaises(
            RuntimeError,
            lambda: ops.import_scene.vrm(filepath=str(vrm_path)),
        )


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
