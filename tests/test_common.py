# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import tempfile
from pathlib import Path
from unittest import TestCase

from io_scene_vrm.common import version
from io_scene_vrm.common.blender_manifest import BlenderManifest
from io_scene_vrm.common.fs import (
    create_unique_indexed_directory_path,
    create_unique_indexed_file_path,
)
from io_scene_vrm.common.vrm0 import human_bone as vrm0_human_bone
from io_scene_vrm.common.vrm1 import human_bone as vrm1_human_bone


class TestVersion(TestCase):
    def test_version(self) -> None:
        self.assertEqual(
            version.get_addon_version(),
            (
                2,  # x-release-please-major
                34,  # x-release-please-minor
                1,  # x-release-please-patch
            ),
        )


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


class TestPath(TestCase):
    def test_create_unique_indexed_directory_path_no_suffix_no_binary(self) -> None:
        with tempfile.TemporaryDirectory() as dir_str:
            dir_path = Path(dir_str)

            exist_a = create_unique_indexed_directory_path(dir_path / "a")
            self.assertEqual(exist_a, dir_path / "a")
            self.assertTrue(exist_a.is_dir())

            exist_a_1 = create_unique_indexed_directory_path(dir_path / "a")
            self.assertEqual(exist_a_1, dir_path / "a.1")
            self.assertTrue(exist_a_1.is_dir())

            exist_a_2 = create_unique_indexed_directory_path(dir_path / "a")
            self.assertEqual(exist_a_2, dir_path / "a.2")
            self.assertTrue(exist_a_2.is_dir())

    def test_create_unique_indexed_file_path_no_suffix_no_binary(self) -> None:
        with tempfile.TemporaryDirectory() as dir_str:
            dir_path = Path(dir_str)

            not_exist_a = create_unique_indexed_file_path(dir_path / "a")
            self.assertEqual(not_exist_a, dir_path / "a")
            self.assertFalse(not_exist_a.is_file())

            not_exist_a = create_unique_indexed_file_path(not_exist_a)
            self.assertEqual(not_exist_a, dir_path / "a")
            self.assertFalse(not_exist_a.is_file())

            not_exist_a.touch()

            not_exist_a_1 = create_unique_indexed_file_path(dir_path / "a")
            self.assertEqual(not_exist_a_1, dir_path / "a.1")
            self.assertFalse(not_exist_a_1.is_file())

            not_exist_a_1 = create_unique_indexed_file_path(dir_path / "a")
            self.assertEqual(not_exist_a_1, dir_path / "a.1")
            self.assertFalse(not_exist_a_1.is_file())

            not_exist_a_1.touch()

            not_exist_a_2 = create_unique_indexed_file_path(dir_path / "a")
            self.assertEqual(not_exist_a_2, dir_path / "a.2")
            self.assertFalse(not_exist_a_2.is_file())

    def test_create_unique_indexed_file_path_no_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as dir_str:
            dir_path = Path(dir_str)

            exist_a = create_unique_indexed_file_path(dir_path / "a", b"a")
            self.assertEqual(exist_a, dir_path / "a")
            self.assertEqual(exist_a.read_bytes(), b"a")
            self.assertTrue(exist_a.is_file())

            exist_a_1 = create_unique_indexed_file_path(dir_path / "a", b"a1")
            self.assertEqual(exist_a_1, dir_path / "a.1")
            self.assertEqual(exist_a_1.read_bytes(), b"a1")
            self.assertTrue(exist_a_1.is_file())

            exist_a_2 = create_unique_indexed_file_path(dir_path / "a", b"a2")
            self.assertEqual(exist_a_2, dir_path / "a.2")
            self.assertEqual(exist_a_2.read_bytes(), b"a2")
            self.assertTrue(exist_a_2.is_file())

    def test_create_unique_indexed_file_path_no_binary(self) -> None:
        with tempfile.TemporaryDirectory() as dir_str:
            dir_path = Path(dir_str)

            not_exist_a = create_unique_indexed_file_path(dir_path / "a.txt")
            self.assertEqual(not_exist_a, dir_path / "a.txt")
            self.assertFalse(not_exist_a.is_file())

            not_exist_a = create_unique_indexed_file_path(not_exist_a)
            self.assertEqual(not_exist_a, dir_path / "a.txt")
            self.assertFalse(not_exist_a.is_file())

            not_exist_a.touch()

            not_exist_a_1 = create_unique_indexed_file_path(dir_path / "a.txt")
            self.assertEqual(not_exist_a_1, dir_path / "a.1.txt")
            self.assertFalse(not_exist_a_1.is_file())

            not_exist_a_1 = create_unique_indexed_file_path(dir_path / "a.txt")
            self.assertEqual(not_exist_a_1, dir_path / "a.1.txt")
            self.assertFalse(not_exist_a_1.is_file())

            not_exist_a_1.touch()

            not_exist_a_2 = create_unique_indexed_file_path(dir_path / "a.txt")
            self.assertEqual(not_exist_a_2, dir_path / "a.2.txt")
            self.assertFalse(not_exist_a_2.is_file())

    def test_create_unique_indexed_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as dir_str:
            dir_path = Path(dir_str)

            exist_a = create_unique_indexed_file_path(dir_path / "a.txt", b"a")
            self.assertEqual(exist_a, dir_path / "a.txt")
            self.assertEqual(exist_a.read_bytes(), b"a")
            self.assertTrue(exist_a.is_file())

            exist_a_1 = create_unique_indexed_file_path(dir_path / "a.txt", b"a1")
            self.assertEqual(exist_a_1, dir_path / "a.1.txt")
            self.assertEqual(exist_a_1.read_bytes(), b"a1")
            self.assertTrue(exist_a_1.is_file())

            exist_a_2 = create_unique_indexed_file_path(dir_path / "a.txt", b"a2")
            self.assertEqual(exist_a_2, dir_path / "a.2.txt")
            self.assertEqual(exist_a_2.read_bytes(), b"a2")
            self.assertTrue(exist_a_2.is_file())


class TestVrm0HumanBone(TestCase):
    def test_all(self) -> None:
        all_human_bone_names = sorted(n.value for n in vrm0_human_bone.HumanBoneName)
        self.assertEqual(
            all_human_bone_names,
            sorted(
                b.name.value
                for b in vrm0_human_bone.HumanBoneSpecifications.all_human_bones
            ),
        )
        self.assertEqual(
            all_human_bone_names,
            sorted(vrm0_human_bone.HumanBoneSpecifications.all_names),
        )

        structure_human_bone_names: list[str] = []
        children: list[vrm0_human_bone.HumanBoneStructure] = [
            vrm0_human_bone.HUMAN_BONE_STRUCTURE
        ]
        while children:
            current = children.pop()
            for human_bone_name, child in current.items():
                children.append(child)
                structure_human_bone_names.append(human_bone_name.value)

        self.assertEqual(all_human_bone_names, sorted(structure_human_bone_names))

    def test_parent(self) -> None:
        self.assertEqual(vrm0_human_bone.HumanBoneSpecifications.HIPS.parent_name, None)
        self.assertEqual(vrm0_human_bone.HumanBoneSpecifications.HIPS.parent(), None)

        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.RIGHT_TOES.parent_name,
            vrm0_human_bone.HumanBoneName.RIGHT_FOOT,
        )
        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.RIGHT_TOES.parent(),
            vrm0_human_bone.HumanBoneSpecifications.RIGHT_FOOT,
        )

        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.LEFT_SHOULDER.parent_name,
            vrm0_human_bone.HumanBoneName.UPPER_CHEST,
        )
        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.LEFT_SHOULDER.parent(),
            vrm0_human_bone.HumanBoneSpecifications.UPPER_CHEST,
        )

        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.NECK.parent_name,
            vrm0_human_bone.HumanBoneName.UPPER_CHEST,
        )
        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.NECK.parent(),
            vrm0_human_bone.HumanBoneSpecifications.UPPER_CHEST,
        )

    def test_children(self) -> None:
        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.HIPS.children_names,
            [
                vrm0_human_bone.HumanBoneName.SPINE,
                vrm0_human_bone.HumanBoneName.LEFT_UPPER_LEG,
                vrm0_human_bone.HumanBoneName.RIGHT_UPPER_LEG,
            ],
        )
        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.HIPS.children(),
            [
                vrm0_human_bone.HumanBoneSpecifications.SPINE,
                vrm0_human_bone.HumanBoneSpecifications.LEFT_UPPER_LEG,
                vrm0_human_bone.HumanBoneSpecifications.RIGHT_UPPER_LEG,
            ],
        )

        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.RIGHT_TOES.children_names, []
        )
        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.RIGHT_TOES.children(), []
        )

        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.LEFT_SHOULDER.children_names,
            [vrm0_human_bone.HumanBoneName.LEFT_UPPER_ARM],
        )
        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.LEFT_SHOULDER.children(),
            [vrm0_human_bone.HumanBoneSpecifications.LEFT_UPPER_ARM],
        )

        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.UPPER_CHEST.children_names,
            [
                vrm0_human_bone.HumanBoneName.NECK,
                vrm0_human_bone.HumanBoneName.LEFT_SHOULDER,
                vrm0_human_bone.HumanBoneName.RIGHT_SHOULDER,
            ],
        )
        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.UPPER_CHEST.children(),
            [
                vrm0_human_bone.HumanBoneSpecifications.NECK,
                vrm0_human_bone.HumanBoneSpecifications.LEFT_SHOULDER,
                vrm0_human_bone.HumanBoneSpecifications.RIGHT_SHOULDER,
            ],
        )


class TestVrm1HumanBone(TestCase):
    def test_all(self) -> None:
        all_human_bone_names = sorted(n.value for n in vrm1_human_bone.HumanBoneName)
        self.assertEqual(
            all_human_bone_names,
            sorted(
                b.name.value
                for b in vrm1_human_bone.HumanBoneSpecifications.all_human_bones
            ),
        )
        self.assertEqual(
            all_human_bone_names,
            sorted(vrm1_human_bone.HumanBoneSpecifications.all_names),
        )

        structure_human_bone_names: list[str] = []
        children: list[vrm1_human_bone.HumanBoneStructure] = [
            vrm1_human_bone.HUMAN_BONE_STRUCTURE
        ]
        while children:
            current = children.pop()
            for human_bone_name, child in current.items():
                children.append(child)
                structure_human_bone_names.append(human_bone_name.value)

        self.assertEqual(all_human_bone_names, sorted(structure_human_bone_names))

    def test_parent(self) -> None:
        self.assertEqual(vrm1_human_bone.HumanBoneSpecifications.HIPS.parent_name, None)
        self.assertEqual(vrm1_human_bone.HumanBoneSpecifications.HIPS.parent(), None)

        self.assertEqual(
            vrm1_human_bone.HumanBoneSpecifications.RIGHT_TOES.parent_name,
            vrm1_human_bone.HumanBoneName.RIGHT_FOOT,
        )
        self.assertEqual(
            vrm1_human_bone.HumanBoneSpecifications.RIGHT_TOES.parent(),
            vrm1_human_bone.HumanBoneSpecifications.RIGHT_FOOT,
        )

        self.assertEqual(
            vrm1_human_bone.HumanBoneSpecifications.LEFT_SHOULDER.parent_name,
            vrm1_human_bone.HumanBoneName.UPPER_CHEST,
        )
        self.assertEqual(
            vrm1_human_bone.HumanBoneSpecifications.LEFT_SHOULDER.parent(),
            vrm1_human_bone.HumanBoneSpecifications.UPPER_CHEST,
        )

        self.assertEqual(
            vrm1_human_bone.HumanBoneSpecifications.NECK.parent_name,
            vrm1_human_bone.HumanBoneName.UPPER_CHEST,
        )
        self.assertEqual(
            vrm1_human_bone.HumanBoneSpecifications.NECK.parent(),
            vrm1_human_bone.HumanBoneSpecifications.UPPER_CHEST,
        )

    def test_children(self) -> None:
        self.assertEqual(
            vrm1_human_bone.HumanBoneSpecifications.HIPS.children_names,
            [
                vrm1_human_bone.HumanBoneName.SPINE,
                vrm1_human_bone.HumanBoneName.LEFT_UPPER_LEG,
                vrm1_human_bone.HumanBoneName.RIGHT_UPPER_LEG,
            ],
        )
        self.assertEqual(
            vrm1_human_bone.HumanBoneSpecifications.HIPS.children(),
            [
                vrm1_human_bone.HumanBoneSpecifications.SPINE,
                vrm1_human_bone.HumanBoneSpecifications.LEFT_UPPER_LEG,
                vrm1_human_bone.HumanBoneSpecifications.RIGHT_UPPER_LEG,
            ],
        )

        self.assertEqual(
            vrm1_human_bone.HumanBoneSpecifications.RIGHT_TOES.children_names, []
        )
        self.assertEqual(
            vrm1_human_bone.HumanBoneSpecifications.RIGHT_TOES.children(), []
        )

        self.assertEqual(
            vrm1_human_bone.HumanBoneSpecifications.LEFT_SHOULDER.children_names,
            [vrm1_human_bone.HumanBoneName.LEFT_UPPER_ARM],
        )
        self.assertEqual(
            vrm1_human_bone.HumanBoneSpecifications.LEFT_SHOULDER.children(),
            [vrm1_human_bone.HumanBoneSpecifications.LEFT_UPPER_ARM],
        )

        self.assertEqual(
            vrm1_human_bone.HumanBoneSpecifications.UPPER_CHEST.children_names,
            [
                vrm1_human_bone.HumanBoneName.NECK,
                vrm1_human_bone.HumanBoneName.LEFT_SHOULDER,
                vrm1_human_bone.HumanBoneName.RIGHT_SHOULDER,
            ],
        )
        self.assertEqual(
            vrm1_human_bone.HumanBoneSpecifications.UPPER_CHEST.children(),
            [
                vrm1_human_bone.HumanBoneSpecifications.NECK,
                vrm1_human_bone.HumanBoneSpecifications.LEFT_SHOULDER,
                vrm1_human_bone.HumanBoneSpecifications.RIGHT_SHOULDER,
            ],
        )
