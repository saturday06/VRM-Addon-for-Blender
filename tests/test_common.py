from unittest import TestCase

from io_scene_vrm.common import deep


class TestDeep(TestCase):
    def test_nested_json_value_getter(self) -> None:
        self.assertEqual(
            123,
            deep.get({"foo": [{"bar": 123}]}, ["foo", 0, "bar"]),
        )
