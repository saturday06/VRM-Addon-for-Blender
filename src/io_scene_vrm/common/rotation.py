# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from typing import Final, Union

from bpy.types import (
    Object,
    PoseBone,
)
from mathutils import Quaternion

from .logger import get_logger

_logger = get_logger(__name__)


ROTATION_MODE_QUATERNION: Final = "QUATERNION"
ROTATION_MODE_AXIS_ANGLE: Final = "AXIS_ANGLE"
ROTATION_MODE_EULER: Final = ("XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX")


def get_rotation_as_quaternion(
    object_or_pose_bone: Union[Object, PoseBone],
) -> Quaternion:
    if object_or_pose_bone.rotation_mode == ROTATION_MODE_QUATERNION:
        return object_or_pose_bone.rotation_quaternion.copy()

    if object_or_pose_bone.rotation_mode == ROTATION_MODE_AXIS_ANGLE:
        # https://projects.blender.org/blender/blender/src/tag/v2.93.18/source/blender/makesrna/intern/rna_pose.c#L270-L278
        angle, axis_x, axis_y, axis_z = object_or_pose_bone.rotation_axis_angle
        return Quaternion((axis_x, axis_y, axis_z), angle)

    if object_or_pose_bone.rotation_mode in ROTATION_MODE_EULER:
        return object_or_pose_bone.rotation_euler.to_quaternion()

    _logger.error(
        "Unexpected rotation mode for %s %s: %s",
        type(object_or_pose_bone),
        object_or_pose_bone.name,
        object_or_pose_bone.rotation_mode,
    )

    return Quaternion()


def set_rotation_without_mode_change(
    object_or_pose_bone: Union[Object, PoseBone], quaternion: Quaternion
) -> None:
    if object_or_pose_bone.rotation_mode == ROTATION_MODE_QUATERNION:
        object_or_pose_bone.rotation_quaternion = quaternion.copy()
        return

    if object_or_pose_bone.rotation_mode == ROTATION_MODE_AXIS_ANGLE:
        axis, angle = quaternion.to_axis_angle()
        # https://projects.blender.org/blender/blender/src/tag/v2.93.18/source/blender/makesrna/intern/rna_pose.c#L280-L290
        object_or_pose_bone.rotation_axis_angle = [angle, axis.x, axis.y, axis.z]
        return

    if object_or_pose_bone.rotation_mode in ROTATION_MODE_EULER:
        object_or_pose_bone.rotation_euler = quaternion.to_euler(
            object_or_pose_bone.rotation_mode
        )
        return

    _logger.error(
        "Unexpected rotation mode for %s %s: %s",
        type(object_or_pose_bone),
        object_or_pose_bone.name,
        object_or_pose_bone.rotation_mode,
    )


def insert_rotation_keyframe(
    object_or_pose_bone: Union[Object, PoseBone], *, frame: int
) -> None:
    if object_or_pose_bone.rotation_mode == ROTATION_MODE_QUATERNION:
        data_path = "rotation_quaternion"
    elif object_or_pose_bone.rotation_mode == ROTATION_MODE_AXIS_ANGLE:
        data_path = "rotation_axis_angle"
    elif object_or_pose_bone.rotation_mode in ROTATION_MODE_EULER:
        data_path = "rotation_euler"
    else:
        _logger.error(
            "Unexpected rotation mode for %s %s: %s",
            type(object_or_pose_bone),
            object_or_pose_bone.name,
            object_or_pose_bone.rotation_mode,
        )
        return

    object_or_pose_bone.keyframe_insert(data_path, frame=frame)
