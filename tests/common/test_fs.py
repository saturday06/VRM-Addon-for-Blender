# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import tempfile
from pathlib import Path
from unittest import TestCase

from io_scene_vrm.common.fs import (
    create_unique_indexed_directory_path,
    create_unique_indexed_file_path,
)


class TestFs(TestCase):
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
