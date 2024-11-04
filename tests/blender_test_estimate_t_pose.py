# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import sys

import bpy
from bpy.types import Armature, Context
from mathutils import Vector

from io_scene_vrm.common import ops, version
from io_scene_vrm.common.debug import assert_vector3_equals, clean_scene
from io_scene_vrm.editor.extension import (
    VrmAddonArmatureExtensionPropertyGroup,
    get_armature_extension,
)

addon_version = version.get_addon_version()
spec_version = VrmAddonArmatureExtensionPropertyGroup.SPEC_VERSION_VRM1


def get_test_command_args() -> list[list[str]]:
    return [[key.__name__] for key in FUNCTIONS]


def right_upper_arm_a(context: Context) -> None:
    clean_scene(context)

    assert ops.icyp.make_basic_armature() == {"FINISHED"}
    armature = context.object
    if not armature or not isinstance(armature.data, Armature):
        raise AssertionError

    ext = get_armature_extension(armature.data)
    ext.addon_version = addon_version
    ext.spec_version = spec_version

    bpy.ops.object.mode_set(mode="EDIT")
    right_lower_arm = armature.data.edit_bones["lower_arm.R"]
    right_lower_arm.use_connect = True
    right_upper_arm = armature.data.edit_bones["upper_arm.R"]
    right_upper_arm.tail = Vector((-0.5, 0, 1))
    bpy.ops.object.mode_set(mode="OBJECT")
    assert ops.vrm.make_estimated_humanoid_t_pose(armature_name=armature.name) == {
        "FINISHED"
    }

    assert_vector3_equals(
        Vector((-1.2638283967971802, -0.029882915318012238, 1.4166666269302368)),
        armature.pose.bones["index_distal.R"].head,
        "index_distal.R head doesn't match",
    )


def right_upper_arm_a_not_connected(context: Context) -> None:
    clean_scene(context)

    assert ops.icyp.make_basic_armature() == {"FINISHED"}
    armature = context.object
    if not armature or not isinstance(armature.data, Armature):
        raise AssertionError

    ext = get_armature_extension(armature.data)
    ext.addon_version = addon_version
    ext.spec_version = spec_version

    bpy.ops.object.mode_set(mode="EDIT")
    right_lower_arm = armature.data.edit_bones["lower_arm.R"]
    right_lower_arm.use_connect = False
    right_upper_arm = armature.data.edit_bones["upper_arm.R"]
    right_upper_arm.tail = Vector((-0.5, 0.0, 1.0))
    bpy.ops.object.mode_set(mode="OBJECT")
    assert ops.vrm.make_estimated_humanoid_t_pose(armature_name=armature.name) == {
        "FINISHED"
    }

    assert_vector3_equals(
        Vector((-0.8100490570068359, -0.02988283522427082, 1.4166666269302368)),
        armature.pose.bones["index_distal.R"].head,
        "index_distal.R head doesn't match",
    )


FUNCTIONS = [
    right_upper_arm_a,
    right_upper_arm_a_not_connected,
]


def test(context: Context, function_name: str) -> None:
    function = next((f for f in FUNCTIONS if f.__name__ == function_name), None)
    if function is None:
        message = f"No function name: {function_name}"
        raise AssertionError(message)
    function(context)


if __name__ == "__main__":
    context = bpy.context
    if "--" in sys.argv:
        test(context, *sys.argv[slice(sys.argv.index("--") + 1, sys.maxsize)])
    else:
        for arg in get_test_command_args():
            test(context, *arg)
