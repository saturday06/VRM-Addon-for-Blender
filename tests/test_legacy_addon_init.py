# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import TestCase

from io_scene_vrm import bl_info
from io_scene_vrm.common import version


class TestLegacyAddonInit(TestCase):
    def test_version(self) -> None:
        self.assertEqual(
            version.get_addon_version(),
            bl_info.get("version"),
        )
