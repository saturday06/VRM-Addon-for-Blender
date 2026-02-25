# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import math
from unittest import TestCase

from io_scene_vrm.common import deep


class TestDeep(TestCase):
    def test_make_json(self) -> None:
        self.assertEqual(deep.make_json(None), None)
        self.assertEqual(deep.make_json(True), True)
        self.assertEqual(deep.make_json(False), False)
        self.assertEqual(deep.make_json(1), 1)
        self.assertEqual(deep.make_json(1.5), 1.5)
        self.assertEqual(deep.make_json("foo"), "foo")

        # Non-finite floats
        with self.assertLogs("io_scene_vrm.common.deep", level="WARNING") as cm:
            self.assertEqual(deep.make_json(math.nan), 0.0)
            self.assertEqual(deep.make_json(math.inf), 0.0)
            self.assertEqual(deep.make_json(-math.inf), 0.0)
        self.assertEqual(len(cm.output), 3)
        self.assertIn("is non-finite value", cm.output[0])

        # Nested non-finite floats
        with self.assertLogs("io_scene_vrm.common.deep", level="WARNING") as cm:
            self.assertEqual(
                deep.make_json([math.nan, math.inf, -math.inf]),
                [0.0, 0.0, 0.0],
            )
            self.assertEqual(
                deep.make_json({"a": math.nan, "b": math.inf, "c": -math.inf}),
                {"a": 0.0, "b": 0.0, "c": 0.0},
            )
        self.assertEqual(len(cm.output), 6)

        # Lists
        self.assertEqual(deep.make_json([1, "bar"]), [1, "bar"])
        self.assertEqual(deep.make_json((1, 2)), [1, 2])
        self.assertEqual(deep.make_json(iter([1, 2])), [1, 2])

        # Dicts
        self.assertEqual(deep.make_json({"key": "val"}), {"key": "val"})
        self.assertEqual(deep.make_json({"a": {"b": 1}}), {"a": {"b": 1}})

        # Invalid dict keys
        with self.assertLogs("io_scene_vrm.common.deep", level="WARNING") as cm:
            self.assertEqual(deep.make_json({1: "a", "b": "c"}), {"b": "c"})
        self.assertEqual(len(cm.output), 1)
        self.assertIn("is unrecognized type for dict key", cm.output[0])

        # Unrecognized types
        with self.assertLogs("io_scene_vrm.common.deep", level="WARNING") as cm:
            self.assertEqual(deep.make_json(object()), None)
        self.assertEqual(len(cm.output), 1)
        self.assertIn("is unrecognized type", cm.output[0])

    def test_make_json_dict(self) -> None:
        self.assertEqual(
            deep.make_json_dict({"a": 1, "b": "c", "d": [True, None]}),
            {"a": 1, "b": "c", "d": [True, None]},
        )

    def test_diff(self) -> None:
        # Equality
        self.assertEqual(deep.diff(None, None), [])
        self.assertEqual(deep.diff(True, True), [])
        self.assertEqual(deep.diff(False, False), [])
        self.assertEqual(deep.diff(1, 1), [])
        self.assertEqual(deep.diff(1.5, 1.5), [])
        self.assertEqual(deep.diff("foo", "foo"), [])
        self.assertEqual(deep.diff([1, 2], [1, 2]), [])
        self.assertEqual(deep.diff({"a": 1}, {"a": 1}), [])

        # Type mismatches
        self.assertEqual(
            deep.diff([1], {"a": 1}), [": left is list but right is <class 'dict'>"]
        )
        self.assertEqual(
            deep.diff({"a": 1}, [1]), [": left is dict but right is <class 'list'>"]
        )
        self.assertEqual(
            deep.diff(True, 1), [": left is bool but right is <class 'int'>"]
        )
        self.assertEqual(
            deep.diff("foo", 1), [": left is str but right is <class 'int'>"]
        )
        self.assertEqual(
            deep.diff(None, 1), [": left is None but right is <class 'int'>"]
        )
        self.assertEqual(
            deep.diff(1, None), [": left is <class 'int'> but right is None"]
        )

        # Value differences
        self.assertEqual(deep.diff(True, False), [": left is True but right is False"])
        self.assertEqual(
            deep.diff("foo", "bar"), [': left is "foo" but right is "bar"']
        )
        self.assertEqual(deep.diff(1, 2), [": left is 1 but right is 2"])

        # Lists
        self.assertEqual(
            deep.diff([1, 2], [1, 3]),
            ["[1]: left is 2 but right is 3"],
        )
        diff_result = deep.diff([1, 2], [1, 2, 3])
        self.assertIn(": left length is 2 but right length is 3", diff_result)
        self.assertTrue(any(line.startswith("--- ") for line in diff_result))

        # Dicts
        self.assertEqual(
            deep.diff({"a": 1, "b": 2}, {"a": 1, "b": 3}),
            ['["b"]: left is 2 but right is 3'],
        )
        self.assertEqual(
            deep.diff({"a": 1}, {"a": 1, "b": 2}),
            [': b not in left. right["b"]=2'],
        )
        self.assertEqual(
            deep.diff({"a": 1, "b": 2}, {"a": 1}),
            [': b not in right, left["b"]=2'],
        )

        # Floats and tolerance
        self.assertEqual(
            deep.diff(1.0, 1.1),
            [
                ": left is  1.00000000000000000 but right is  "
                + "1.10000000000000009, error=0.10000000000000009"
            ],
        )
        self.assertEqual(deep.diff(1.0, 1.1, float_tolerance=0.2), [])
        self.assertEqual(deep.diff(1, 1.1, float_tolerance=0.2), [])

        # Non-finite floats
        self.assertEqual(
            deep.diff(math.nan, 1.0),
            [": left is nan but right is 1.0, They are not comparable numbers"],
        )
        self.assertEqual(
            deep.diff(1.0, math.inf),
            [": left is 1.0 but right is inf, They are not comparable numbers"],
        )
