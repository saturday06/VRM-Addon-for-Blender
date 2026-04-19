# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Iterator
from unittest import TestCase

from io_scene_vrm.common import convert_any


class TestConvertAny(TestCase):
    def test_to_object(self) -> None:
        obj = object()
        self.assertIs(convert_any.to_object(obj), obj)
        self.assertIs(convert_any.to_object(None), None)
        self.assertEqual(convert_any.to_object(1), 1)
        self.assertEqual(convert_any.to_object("a"), "a")

        lst = [1, 2, 3]
        self.assertIs(convert_any.to_object(lst), lst)

        dct = {"a": 1}
        self.assertIs(convert_any.to_object(dct), dct)

    def test_iterator_to_object_iterator(self) -> None:
        self.assertIsNone(convert_any.iterator_to_object_iterator(None))
        self.assertIsNone(convert_any.iterator_to_object_iterator(1))
        self.assertIsNone(convert_any.iterator_to_object_iterator(True))

        # A list is an Iterable, but not an Iterator
        self.assertIsNone(convert_any.iterator_to_object_iterator([1, 2, 3]))

        # A valid iterator
        iterator = convert_any.iterator_to_object_iterator(iter([1, 2, 3]))
        self.assertIsNotNone(iterator)
        if iterator is not None:
            self.assertIsInstance(iterator, Iterator)
            self.assertEqual(list(iterator), [1, 2, 3])

        iterator = convert_any.iterator_to_object_iterator(iter(["a", "b", "c"]))
        self.assertIsNotNone(iterator)
        if iterator is not None:
            self.assertIsInstance(iterator, Iterator)
            self.assertEqual(list(iterator), ["a", "b", "c"])

    def test_mapping_to_object_mapping(self) -> None:
        self.assertIsNone(convert_any.mapping_to_object_mapping(None))
        self.assertIsNone(convert_any.mapping_to_object_mapping(123))
        self.assertIsNone(convert_any.mapping_to_object_mapping([1, 2, 3]))

        self.assertEqual(
            convert_any.mapping_to_object_mapping({"a": 1, "b": 2}),
            {"a": 1, "b": 2},
        )
        self.assertEqual(
            convert_any.mapping_to_object_mapping({}),
            {},
        )
