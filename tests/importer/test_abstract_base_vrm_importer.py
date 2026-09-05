# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import TestCase

from io_scene_vrm.common.convert import Json
from io_scene_vrm.importer.abstract_base_vrm_importer import AbstractBaseVrmImporter


class TestFindMiddleBoneIndices(TestCase):
    def test_normal_chain(self) -> None:
        node_dicts: list[dict[str, Json]] = [
            {"children": [1]},
            {"children": [2]},
            {"children": [3]},
            {},
        ]
        self.assertEqual(
            AbstractBaseVrmImporter.find_middle_bone_indices(node_dicts, [0, 3], 0, []),
            [0, 1],
        )

    def test_self_cycle(self) -> None:
        node_dicts: list[dict[str, Json]] = [
            {"children": [1]},
            {"children": [1]},
        ]
        self.assertEqual(
            AbstractBaseVrmImporter.find_middle_bone_indices(node_dicts, [0], 0, []),
            [],
        )

    def test_cycle_with_bone_exit(self) -> None:
        node_dicts: list[dict[str, Json]] = [
            {"children": [1]},
            {"children": [2]},
            {"children": [1, 3]},
            {},
        ]
        self.assertEqual(
            AbstractBaseVrmImporter.find_middle_bone_indices(node_dicts, [0, 3], 0, []),
            [0, 1],
        )

    def test_shared_descendant_preserves_both_paths(self) -> None:
        node_dicts: list[dict[str, Json]] = [
            {"children": [1, 2]},
            {"children": [3]},
            {"children": [3]},
            {"children": [4]},
            {},
        ]
        self.assertEqual(
            AbstractBaseVrmImporter.find_middle_bone_indices(node_dicts, [0, 4], 0, []),
            [0, 1, 0, 2],
        )

    def test_invalid_children(self) -> None:
        node_dicts: list[dict[str, Json]] = [
            {"children": [-1, 99, "1", None, 1]},
            {},
        ]
        self.assertEqual(
            AbstractBaseVrmImporter.find_middle_bone_indices(node_dicts, [0, 1], 0, []),
            [],
        )
