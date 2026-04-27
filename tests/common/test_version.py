# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import TestCase
from unittest.mock import patch

from io_scene_vrm.common import version


class TestVersion(TestCase):
    def test_version(self) -> None:
        self.assertEqual(
            version.get_addon_version(),
            (
                3,  # x-release-please-major
                26,  # x-release-please-minor
                8,  # x-release-please-patch
            ),
        )

    def test_validation_warning_message(self) -> None:
        with (
            patch(
                "io_scene_vrm.common.version._blender_restart_required"
            ) as mock_restart,
            patch("io_scene_vrm.common.version._stable_release") as mock_stable,
            patch("io_scene_vrm.common.version.supported") as mock_supported,
            patch("io_scene_vrm.common.version.bpy") as mock_bpy,
            patch(
                "io_scene_vrm.common.version.pgettext",
                side_effect=str,
            ),
        ):
            with self.subTest("restart required"):
                mock_restart.return_value = True
                mock_stable.return_value = True
                mock_supported.return_value = True
                message = version.validation_warning_message()
                self.assertEqual(
                    message,
                    "The VRM add-on has been updated."
                    " Please restart Blender to apply the changes.",
                )

            with self.subTest("not stable release"):
                mock_restart.return_value = False
                mock_stable.return_value = False
                mock_supported.return_value = True
                mock_bpy.app.version_cycle = "alpha"
                message = version.validation_warning_message()
                self.assertEqual(
                    message,
                    "VRM add-on is not compatible with Blender Alpha."
                    " The VRM may not be exported correctly.",
                )

            with self.subTest("not supported"):
                mock_restart.return_value = False
                mock_stable.return_value = True
                mock_supported.return_value = False
                mock_bpy.app.version = (3, 5, 0)
                message = version.validation_warning_message()
                self.assertEqual(
                    message,
                    "The installed VRM add-on is not compatible with Blender 3.5.0."
                    " The VRM may not be exported correctly.",
                )

            with self.subTest("all ok"):
                mock_restart.return_value = False
                mock_stable.return_value = True
                mock_supported.return_value = True
                self.assertIsNone(version.validation_warning_message())
