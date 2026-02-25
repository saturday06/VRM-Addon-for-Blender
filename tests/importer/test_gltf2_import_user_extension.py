# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from io_scene_vrm.common.test_helper import AddonTestCase
from io_scene_vrm.importer.gltf2_import_user_extension import (
    get_list_from_json_ld,
    get_string_from_json_ld_value,
)


class TestGetListFromJsonLd(AddonTestCase):
    def test_at_list_dict(self) -> None:
        self.assertEqual(
            get_list_from_json_ld({"@list": ["a", "b", "c"]}),
            ["a", "b", "c"],
        )

    def test_at_list_dict_filters_non_strings(self) -> None:
        self.assertEqual(
            get_list_from_json_ld({"@list": ["a", 1, None, "b"]}),
            ["a", "b"],
        )

    def test_plain_list(self) -> None:
        self.assertEqual(
            get_list_from_json_ld(["x", "y"]),
            ["x", "y"],
        )

    def test_plain_list_filters_non_strings(self) -> None:
        self.assertEqual(
            get_list_from_json_ld(["x", 42, True, "y"]),
            ["x", "y"],
        )

    def test_empty_list(self) -> None:
        self.assertEqual(get_list_from_json_ld([]), [])

    def test_empty_at_list(self) -> None:
        self.assertEqual(get_list_from_json_ld({"@list": []}), [])

    def test_none(self) -> None:
        self.assertEqual(get_list_from_json_ld(None), [])

    def test_string(self) -> None:
        self.assertEqual(get_list_from_json_ld("not a list"), [])

    def test_integer(self) -> None:
        self.assertEqual(get_list_from_json_ld(42), [])

    def test_dict_without_at_list(self) -> None:
        self.assertEqual(get_list_from_json_ld({"key": "value"}), [])


class TestGetStringFromJsonLdValue(AddonTestCase):
    def test_plain_string(self) -> None:
        self.assertEqual(get_string_from_json_ld_value("hello"), "hello")

    def test_localized_dict(self) -> None:
        result = get_string_from_json_ld_value({"und": "world"})
        self.assertEqual(result, "world")

    def test_localized_dict_multiple_languages(self) -> None:
        # dict iteration is deterministic in Python 3.7+; "en" is inserted first
        result = get_string_from_json_ld_value({"en": "hello", "ja": "こんにちは"})
        self.assertEqual(result, "hello")

    def test_none(self) -> None:
        self.assertEqual(get_string_from_json_ld_value(None), "")

    def test_integer(self) -> None:
        self.assertEqual(get_string_from_json_ld_value(42), "")

    def test_empty_string(self) -> None:
        self.assertEqual(get_string_from_json_ld_value(""), "")

    def test_empty_dict(self) -> None:
        self.assertEqual(get_string_from_json_ld_value({}), "")
