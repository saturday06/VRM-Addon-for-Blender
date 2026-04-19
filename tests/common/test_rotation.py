# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import math
from unittest import TestCase
from unittest.mock import MagicMock

import bpy
from mathutils import Euler, Quaternion

from io_scene_vrm.common.rotation import (
    get_rotation_as_quaternion,
    insert_rotation_keyframe,
    set_rotation_without_mode_change,
)


class TestRotation(TestCase):
    def setUp(self) -> None:
        super().setUp()
        bpy.ops.wm.read_homefile(use_empty=True)

    def test_get_rotation_as_quaternion(self) -> None:
        obj = bpy.data.objects.new("TestObj", None)

        obj.rotation_mode = "QUATERNION"
        expected_quat = Quaternion((0.5, 0.5, 0.5, 0.5))
        obj.rotation_quaternion = expected_quat
        self.assertEqual(get_rotation_as_quaternion(obj), expected_quat)

        obj.rotation_mode = "AXIS_ANGLE"
        obj.rotation_axis_angle = [math.pi / 2, 1.0, 0.0, 0.0]
        self.assertEqual(
            get_rotation_as_quaternion(obj),
            Quaternion((1.0, 0.0, 0.0), math.pi / 2),
        )

        obj.rotation_mode = "XYZ"
        obj.rotation_euler = Euler((math.pi / 2, 0.0, 0.0), "XYZ")
        self.assertEqual(
            get_rotation_as_quaternion(obj),
            Euler((math.pi / 2, 0.0, 0.0), "XYZ").to_quaternion(),
        )

        # Invalid mode with mocked object because Blender prevents invalid assignment
        mock_obj = MagicMock()
        mock_obj.rotation_mode = "INVALID_MODE"
        self.assertEqual(get_rotation_as_quaternion(mock_obj), Quaternion())

    def test_set_rotation_without_mode_change(self) -> None:
        obj = bpy.data.objects.new("TestObj", None)
        target_quat = Quaternion((0.5, 0.5, 0.5, 0.5))

        obj.rotation_mode = "QUATERNION"
        set_rotation_without_mode_change(obj, target_quat)
        self.assertEqual(obj.rotation_mode, "QUATERNION")
        self.assertEqual(obj.rotation_quaternion, target_quat)

        obj.rotation_mode = "AXIS_ANGLE"
        set_rotation_without_mode_change(obj, target_quat)
        self.assertEqual(obj.rotation_mode, "AXIS_ANGLE")
        axis, angle = target_quat.to_axis_angle()
        self.assertAlmostEqual(obj.rotation_axis_angle[0], angle)
        self.assertAlmostEqual(obj.rotation_axis_angle[1], axis.x)
        self.assertAlmostEqual(obj.rotation_axis_angle[2], axis.y)
        self.assertAlmostEqual(obj.rotation_axis_angle[3], axis.z)

        obj.rotation_mode = "XYZ"
        set_rotation_without_mode_change(obj, target_quat)
        self.assertEqual(obj.rotation_mode, "XYZ")
        self.assertEqual(obj.rotation_euler, target_quat.to_euler("XYZ"))

        # Invalid mode with mocked object
        mock_obj = MagicMock()
        mock_obj.rotation_mode = "INVALID_MODE"
        set_rotation_without_mode_change(mock_obj, target_quat)
        # Verify it doesn't crash

    def test_insert_rotation_keyframe(self) -> None:
        obj = bpy.data.objects.new("TestObj", None)

        obj.rotation_mode = "QUATERNION"
        insert_rotation_keyframe(obj, frame=1)
        animation_data = obj.animation_data
        if animation_data is None:
            self.fail("Animation data should not be None after inserting keyframe")
        action = animation_data.action
        if action is None:
            self.fail("Action should not be None after inserting keyframe")
        self.assertTrue(
            any(fc.data_path == "rotation_quaternion" for fc in action.fcurves)
        )
        animation_data = None
        action = None

        obj.animation_data_clear()
        obj.rotation_mode = "AXIS_ANGLE"
        insert_rotation_keyframe(obj, frame=2)
        animation_data = obj.animation_data
        if animation_data is None:
            self.fail("Animation data should not be None after inserting keyframe")
        action = animation_data.action
        if action is None:
            self.fail("Action should not be None after inserting keyframe")
        self.assertTrue(
            any(fc.data_path == "rotation_axis_angle" for fc in action.fcurves)
        )
        animation_data = None
        action = None

        obj.animation_data_clear()
        obj.rotation_mode = "XYZ"
        insert_rotation_keyframe(obj, frame=3)
        animation_data = obj.animation_data
        if animation_data is None:
            self.fail("Animation data should not be None after inserting keyframe")
        action = animation_data.action
        if action is None:
            self.fail("Action should not be None after inserting keyframe")
        self.assertTrue(any(fc.data_path == "rotation_euler" for fc in action.fcurves))
        animation_data = None
        action = None

        # Invalid mode with mocked object
        mock_obj = MagicMock()
        mock_obj.rotation_mode = "INVALID_MODE"
        insert_rotation_keyframe(mock_obj, frame=4)
        mock_obj.keyframe_insert.assert_not_called()
