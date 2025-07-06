# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import TestCase

from io_scene_vrm import MINIMUM_UNSUPPORTED_BLENDER_MAJOR_MINOR_VERSION
from io_scene_vrm.common.blender_manifest import BlenderManifest


class TestBlenderManifest(TestCase):
    def test_read_default(self) -> None:
        blender_manifest = BlenderManifest.read()
        self.assertGreater(blender_manifest.version, (2,))
        self.assertGreater(blender_manifest.blender_version_min, (2, 93))
        if blender_manifest.blender_version_max is None:
            message = "blender_manifest.blender_version_max must not be None"
            raise AssertionError(message)
        self.assertGreater(blender_manifest.blender_version_max, (4,))
        self.assertEqual(
            blender_manifest.blender_version_max,
            (*MINIMUM_UNSUPPORTED_BLENDER_MAJOR_MINOR_VERSION, 0),
        )

    def test_read(self) -> None:
        text = (
            "foo = bar\n"
            + 'id = "baz"\n'
            + 'version = "1.23.456"\n'
            + 'blender_version_min = "9.8.7"\n'
            + 'blender_version_max = "12.34.56"\n'
        )
        blender_manifest = BlenderManifest.read(text)
        self.assertEqual(blender_manifest.id, "baz")
        self.assertEqual(blender_manifest.version, (1, 23, 456))
        self.assertEqual(blender_manifest.blender_version_min, (9, 8, 7))
        self.assertEqual(blender_manifest.blender_version_max, (12, 34, 56))
