# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import TestCase

from io_scene_vrm.common.blender_manifest import BlenderManifest


class TestBlenderManifest(TestCase):
    def test_read_default(self) -> None:
        blender_manifest = BlenderManifest.read()
        self.assertGreater(blender_manifest.version, (2,))
        self.assertGreater(blender_manifest.blender_version_min, (2, 93))
        if blender_manifest.blender_version_max is not None:
            self.assertGreater(blender_manifest.blender_version_max, (4,))

    def test_read(self) -> None:
        text = (
            "foo = bar\n"
            + 'version = "1.23.456"\n'
            + 'blender_version_min = "9.8.7"\n'
            + 'blender_version_max = "12.34.56"\n'
        )
        blender_manifest = BlenderManifest.read(text)
        self.assertEqual(blender_manifest.version, (1, 23, 456))
        self.assertEqual(blender_manifest.blender_version_min, (9, 8, 7))
        self.assertEqual(blender_manifest.blender_version_max, (12, 34, 56))
