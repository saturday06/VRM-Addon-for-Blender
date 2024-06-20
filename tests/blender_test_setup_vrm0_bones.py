import sys
from collections.abc import Sequence

import bpy
from bpy.types import Armature, Context
from mathutils import Vector

from io_scene_vrm.common import ops
from io_scene_vrm.importer.vrm0_importer import setup_bones


def assert_vector3_equals(
    expected: Vector, actual: Sequence[float], message: str
) -> None:
    if len(actual) != 3:
        message = f"actual length is not 3: {actual}"
        raise AssertionError(message)

    threshold = 0.0001
    if abs(expected[0] - actual[0]) > threshold:
        message = f"{message}: {tuple(expected)} is different from {tuple(actual)}"
        raise AssertionError(message)
    if abs(expected[1] - actual[1]) > threshold:
        message = f"{message}: {tuple(expected)} is different from {tuple(actual)}"
        raise AssertionError(message)
    if abs(expected[2] - actual[2]) > threshold:
        message = f"{message}: {tuple(expected)} is different from {tuple(actual)}"
        raise AssertionError(message)


def get_test_command_args() -> list[list[str]]:
    return [[key.__name__] for key in FUNCTIONS]


def clean_scene(context: Context) -> None:
    if context.view_layer.objects.active:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    while context.blend_data.collections:
        context.blend_data.collections.remove(context.blend_data.collections[0])
    bpy.ops.outliner.orphans_purge(do_recursive=True)


def test_eye_bone_world_minus_y(context: Context) -> None:
    clean_scene(context)
    ops.icyp.make_basic_armature()
    armature = context.view_layer.objects.active
    if not armature or not isinstance(armature.data, Armature):
        message = "No armature"
        raise AssertionError(message)

    bpy.ops.object.mode_set(mode="EDIT")
    eye_r = armature.data.edit_bones["eye.R"]
    eye_r.tail = Vector((-0.2, -0.2, 1.55))
    eye_l = armature.data.edit_bones["eye.L"]
    eye_l.tail = Vector((0.2, -0.2, 1.55))
    bpy.ops.object.mode_set(mode="OBJECT")
    # return
    setup_bones(context, armature)

    bpy.ops.object.mode_set(mode="EDIT")
    eye_r = armature.data.edit_bones["eye.R"]
    eye_l = armature.data.edit_bones["eye.L"]

    assert_vector3_equals(
        Vector((0, -1, 0)),
        (eye_r.tail - eye_r.head).normalized(),
        "eye.R direction is minus y",
    )
    assert_vector3_equals(
        Vector((0, -1, 0)),
        (eye_l.tail - eye_l.head).normalized(),
        "eye.L direction is minus y",
    )


def test_head_bone_world_plus_z(context: Context) -> None:
    clean_scene(context)
    ops.icyp.make_basic_armature()
    armature = context.view_layer.objects.active
    if not armature or not isinstance(armature.data, Armature):
        message = "No armature"
        raise AssertionError(message)

    bpy.ops.object.mode_set(mode="EDIT")
    neck = armature.data.edit_bones["neck"]
    neck.tail = Vector((0, -0.2, 1.5))
    head = armature.data.edit_bones["head"]
    head.tail = Vector((0, -0.4, 1.57))
    bpy.ops.object.mode_set(mode="OBJECT")
    # return
    setup_bones(context, armature)


FUNCTIONS = [
    test_eye_bone_world_minus_y,
    test_head_bone_world_plus_z,
]


def test(context: Context, function_name: str) -> None:
    function = next((f for f in FUNCTIONS if f.__name__ == function_name), None)
    if function is None:
        message = f"No function name: {function_name}"
        raise AssertionError(message)
    function(context)


if __name__ == "__main__":
    context = bpy.context
    if "--" in sys.argv and len(sys.argv) != (sys.argv.index("--") + 2):
        test(context, *sys.argv[slice(sys.argv.index("--") + 1, sys.maxsize)])
    else:
        for arg in get_test_command_args():
            test(context, *arg)
