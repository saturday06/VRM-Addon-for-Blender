# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import functools
import sys
from os import environ
from pathlib import Path
from unittest import main

import bpy

from io_scene_vrm.common import ops
from io_scene_vrm.common.logger import get_logger
from tests.util import (
    RESOURCES_VRM_PATH,
    AddonTestCase,
    make_test_method_name,
)

_logger = get_logger(__name__)


class TestImportNonObjectMode(AddonTestCase):
    def test_import_non_object_mode(self) -> None:
        self.assertEqual(ops.icyp.make_basic_armature(), {"FINISHED"})
        self.assertEqual(bpy.ops.object.posemode_toggle(), {"FINISHED"})
        self.assertEqual(
            ops.import_scene.vrm(
                filepath=str(RESOURCES_VRM_PATH / "in" / "triangle.vrm")
            ),
            {"FINISHED"},
        )


class __TestImportSceneBrokenVrmBase(AddonTestCase):
    def assert_broken_vrm(self, vrm_path: Path) -> None:
        environ["BLENDER_VRM_AUTOMATIC_LICENSE_CONFIRMATION"] = "true"

        success = True
        if (
            vrm_path.name == "draco.vrm"
            and (sys.platform in ("linux", "win32"))
            and not bpy.app.binary_path
            and bpy.app.version < (4, 5)
        ):
            # On Linux when built as a module, the draco library cannot be read
            # and causes an error
            success = False

        if (
            vrm_path.name == "empty.vrm"
            and bpy.app.binary_path
            and (4, 5) <= bpy.app.version < (4, 5, 8)
        ):
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
        make_test_method_name(path.stem): functools.partialmethod(
            __TestImportSceneBrokenVrmBase.assert_broken_vrm, path
        )
        for path in sorted((RESOURCES_VRM_PATH / "broken").glob("*.vrm"))
    },
)

if __name__ == "__main__":
    main()
