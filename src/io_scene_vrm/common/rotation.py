# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from typing import Union

from bpy.types import (
    Object,
    PoseBone,
)
from mathutils import Quaternion

from .logging import get_logger

logger = get_logger(__name__)


def get_rotation_as_quaternion(
    object_or_pose_bone: Union[Object, PoseBone],
) -> Quaternion:
    if object_or_pose_bone.rotation_mode == "QUATERNION":
        return object_or_pose_bone.rotation_quaternion.copy()

    if object_or_pose_bone.rotation_mode == "AXIS_ANGLE":
        axis_x, axis_y, axis_z, angle = object_or_pose_bone.rotation_axis_angle
        return Quaternion((axis_x, axis_y, axis_z), angle)

    if object_or_pose_bone.rotation_mode in ["XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX"]:
        return object_or_pose_bone.rotation_euler.to_quaternion()

    logger.error(
        "Unexpected rotation mode for bone %s: %s",
        object_or_pose_bone.name,
        object_or_pose_bone.rotation_mode,
    )

    return Quaternion()


def set_rotation_without_mode_change(
    object_or_pose_bone: Union[Object, PoseBone], quaternion: Quaternion
) -> None:
    if object_or_pose_bone.rotation_mode == "QUATERNION":
        object_or_pose_bone.rotation_quaternion = quaternion.copy()
        return

    if object_or_pose_bone.rotation_mode == "AXIS_ANGLE":
        axis, angle = quaternion.to_axis_angle()
        object_or_pose_bone.rotation_axis_angle = [axis.x, axis.y, axis.z, angle]
        return

    if object_or_pose_bone.rotation_mode in ["XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX"]:
        object_or_pose_bone.rotation_euler = quaternion.to_euler(
            object_or_pose_bone.rotation_mode
        )
        return

    logger.error(
        "Unexpected rotation mode for bone %s: %s",
        object_or_pose_bone.name,
        object_or_pose_bone.rotation_mode,
    )
