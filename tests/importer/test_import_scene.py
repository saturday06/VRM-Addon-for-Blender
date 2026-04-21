# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import functools
import sys
from os import environ
from pathlib import Path
from unittest import main
from unittest.mock import patch

import bpy

from io_scene_vrm.common import ops
from io_scene_vrm.common.logger import get_logger
from io_scene_vrm.importer.license_validation import (
    LicenseConfirmationRequiredError,
    LicenseConfirmationRequiredProp,
)
from tests.util import (
    RESOURCES_VRM_PATH,
    AddonTestCase,
    make_test_method_name,
)

_logger = get_logger(__name__)


class TestImportScene(AddonTestCase):
    def test_import_license_confirmation_error_path(self) -> None:
        """Test that LicenseConfirmationRequiredError is caught and handled."""
        with (
            patch.dict(environ, {}, clear=False),
            # We patch `import_vrm` to raise LicenseConfirmationRequiredError
            patch("io_scene_vrm.importer.import_scene.import_vrm") as mock_import_vrm,
            # We must also mock wm.vrm_license_warning to avoid exceptions in the UI
            # code during testing
            patch("io_scene_vrm.common.ops.wm.vrm_license_warning") as mock_warning,
        ):
            environ.pop("BLENDER_VRM_AUTOMATIC_LICENSE_CONFIRMATION", None)

            mock_warning.return_value = {"FINISHED"}

            props = [
                LicenseConfirmationRequiredProp(
                    url="https://example.com",
                    json_key="dummy_key",
                    message="Dummy license message",
                )
            ]
            mock_import_vrm.side_effect = LicenseConfirmationRequiredError(props)
            filepath = str(RESOURCES_VRM_PATH / "in" / "triangle.vrm")

            # Execute the import operator
            result = ops.import_scene.vrm(filepath=filepath)

            # Verify that it didn't throw and returned {"FINISHED"}
            # (as returned by our mock warning)
            self.assertEqual(result, {"FINISHED"})

            # Verify that the mocked functions were called with the expected
            # license-confirmation-path arguments.
            mock_import_vrm.assert_called_once()
            self.assertTrue(mock_import_vrm.call_args.kwargs.get("license_validation"))

            expected_license_confirmations = LicenseConfirmationRequiredError(
                props
            ).license_confirmations()

            mock_warning.assert_called_once()
            self.assertEqual(
                mock_warning.call_args.kwargs.get("license_confirmations"),
                expected_license_confirmations,
            )
            self.assertEqual(mock_warning.call_args.kwargs.get("filepath"), filepath)
            self.assertFalse(mock_warning.call_args.kwargs.get("import_anyway"))


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
