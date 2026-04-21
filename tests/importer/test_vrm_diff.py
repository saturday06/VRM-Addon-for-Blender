# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import TestCase
from unittest.mock import MagicMock, patch

from io_scene_vrm.importer.vrm_diff import vrm_diff
from tests.util import RESOURCES_VRM_PATH


class TestVrmDiff(TestCase):
    @patch("io_scene_vrm.importer.vrm_diff._create_vrm_json_dict")
    @patch("io_scene_vrm.importer.vrm_diff.deep.diff")
    def test_vrm_diff_mocked(
        self, mock_diff: MagicMock, mock_create_vrm_json_dict: MagicMock
    ) -> None:
        mock_create_vrm_json_dict.side_effect = [{"before": "dict"}, {"after": "dict"}]
        mock_diff.return_value = ["diff item"]

        before_bytes = b"before_bytes"
        after_bytes = b"after_bytes"
        float_tolerance = 0.001

        result = vrm_diff(before_bytes, after_bytes, float_tolerance)

        self.assertEqual(mock_create_vrm_json_dict.call_count, 2)
        mock_create_vrm_json_dict.assert_any_call(before_bytes)
        mock_create_vrm_json_dict.assert_any_call(after_bytes)

        mock_diff.assert_called_once_with(
            {"before": "dict"}, {"after": "dict"}, float_tolerance
        )
        self.assertEqual(result, ["diff item"])

    def test_vrm_diff_same_file(self) -> None:
        vrm_path = RESOURCES_VRM_PATH / "in" / "basic_armature.vrm"
        vrm_bytes = vrm_path.read_bytes()

        float_tolerance = 0.000001
        diffs = vrm_diff(vrm_bytes, vrm_bytes, float_tolerance)
        self.assertEqual(diffs, [])
