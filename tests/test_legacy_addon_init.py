from unittest import TestCase

from io_scene_vrm import MAX_SUPPORTED_BLENDER_MAJOR_MINOR_VERSION, bl_info
from io_scene_vrm.common import version
from io_scene_vrm.common.blender_manifest import BlenderManifest


class TestLegacyAddonInit(TestCase):
    def test_version(self) -> None:
        self.assertEqual(
            version.get_addon_version(),
            bl_info.get("version"),
        )

    def test_max_supported_blender_major_minor_version(self) -> None:
        self.assertEqual(
            version.max_supported_blender_major_minor_version(),
            MAX_SUPPORTED_BLENDER_MAJOR_MINOR_VERSION,
        )

    def test_min_supported_blender_version(self) -> None:
        self.assertEqual(
            bl_info.get("blender"),
            BlenderManifest.read().blender_version_min,
        )
