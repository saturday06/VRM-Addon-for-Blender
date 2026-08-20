# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import TestCase

from io_scene_vrm.importer.vrm_diff import vrm_diff
from tests.util import RESOURCES_VRM_PATH


class TestVrmDiff(TestCase):
    def test_vrm_diff_same_file(self) -> None:
        vrm_path = RESOURCES_VRM_PATH / "in" / "basic_armature.vrm"
        vrm_bytes = vrm_path.read_bytes()

        float_tolerance = 0.000001
        diffs = vrm_diff(vrm_bytes, vrm_bytes, float_tolerance)
        self.assertEqual(diffs, [])
