# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import TestCase

from io_scene_vrm import MINIMUM_UNSUPPORTED_BLENDER_MAJOR_MINOR_VERSION, bl_info
from io_scene_vrm.common import version


class TestLegacyAddonInit(TestCase):
    def test_version(self) -> None:
        self.assertEqual(
            version.get_addon_version(),
            bl_info.get("version"),
        )

    def test_max_supported_blender_major_minor_version(self) -> None:
        self.assertEqual(
            version.min_unsupported_blender_major_minor_version(),
            MINIMUM_UNSUPPORTED_BLENDER_MAJOR_MINOR_VERSION,
        )
