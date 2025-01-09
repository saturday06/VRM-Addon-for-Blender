# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
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

    bpy.ops.object.mode_set(mode="EDIT")
    head = armature.data.edit_bones["head"]
    assert_vector3_equals(
        Vector((0, 0, 1)),
        (head.tail - head.head).normalized(),
        "head direction is plus z",
    )

    parent = head.parent
    if not parent:
        message = "head has no parent"
        raise AssertionError(message)

    assert (head.length - parent.length) < 0.0001, (
        f"head length {head.length} is same as neck length {parent.length}"
    )


def test_multiple_children_right_toes_direction_is_same_as_foot(
    context: Context,
) -> None:
    clean_scene(context)
    ops.icyp.make_basic_armature()
    armature = context.view_layer.objects.active
    if not armature or not isinstance(armature.data, Armature):
        message = "No armature"
        raise AssertionError(message)

    bpy.ops.object.mode_set(mode="EDIT")
    right_foot = armature.data.edit_bones["foot.R"]
    right_foot.tail = Vector((-0.2, -0.2, -0.2))
    right_toes = armature.data.edit_bones["toes.R"]
    right_toes.tail = Vector((0, -0.4, 1.57))

    right_toes_child1 = armature.data.edit_bones.new("toes_child1.R")
    right_toes_child1.parent = right_toes
    right_toes_child1.head = Vector((-0.5, -0.25, 0))
    right_toes_child1.tail = Vector((-0.5, -0.5, 0))

    right_toes_child2 = armature.data.edit_bones.new("toes_child2.R")
    right_toes_child2.parent = right_toes
    right_toes_child2.head = Vector((-0.75, -0.25, 0))
    right_toes_child2.tail = Vector((-0.75, -0.5, 0))
    bpy.ops.object.mode_set(mode="OBJECT")
    # return
    setup_bones(context, armature)

    bpy.ops.object.mode_set(mode="EDIT")
    right_foot = armature.data.edit_bones["foot.R"]
    right_toes = armature.data.edit_bones["toes.R"]
    assert_vector3_equals(
        right_foot.vector.normalized(),
        right_toes.vector.normalized(),
        "foot.R and toes.R direction are same direction",
    )

    parent = right_toes.parent
    if not parent:
        message = "toes.R has no parent"
        raise AssertionError(message)

    assert (right_toes.length * 2 - parent.length) < 0.0001, (
        f"toes.R length {right_toes.length} is half as "
        + f"foot.R length {parent.length}"
    )


def test_multiple_children_no_left_toes(context: Context) -> None:
    clean_scene(context)
    ops.icyp.make_basic_armature()
    armature = context.view_layer.objects.active
    if not armature or not isinstance(armature.data, Armature):
        message = "No armature"
        raise AssertionError(message)

    bpy.ops.object.mode_set(mode="EDIT")
    armature.data.edit_bones.remove(armature.data.edit_bones["toes.R"])
    right_lower_leg = armature.data.edit_bones["lower_leg.R"]
    right_lower_leg.tail = Vector((-0.2, 0.2, 0.5))
    right_lower_leg.tail = Vector((-0.2, 0.2, 0))
    right_foot = armature.data.edit_bones["foot.R"]
    right_foot.tail = Vector((-0.2, 0.2, 0))
    right_foot.tail = Vector((-0.2, -0.2, 0))

    right_foot_child1 = armature.data.edit_bones.new("foot_child1.R")
    right_foot_child1.parent = right_foot
    right_foot_child1.head = Vector((-0.5, -0.25, 0))
    right_foot_child1.tail = Vector((-0.5, -0.5, 0))

    right_foot_child2 = armature.data.edit_bones.new("foot_child2.R")
    right_foot_child2.parent = right_foot
    right_foot_child2.head = Vector((-0.75, -0.25, 0))
    right_foot_child2.tail = Vector((-0.75, -0.5, 0))

    bpy.ops.object.mode_set(mode="OBJECT")
    # return
    setup_bones(context, armature)

    bpy.ops.object.mode_set(mode="EDIT")
    right_lower_leg = armature.data.edit_bones["lower_leg.R"]
    right_foot = armature.data.edit_bones["foot.R"]
    assert_vector3_equals(
        right_lower_leg.vector.normalized(),
        right_foot.vector.normalized(),
        "lower_leg.R and foot.R direction are same direction",
    )

    parent = right_foot.parent
    if not parent:
        message = "foot.R has no parent"
        raise AssertionError(message)

    assert (right_foot.length * 2 - parent.length) < 0.0001, (
        f"foot.R length {right_foot.length} is half as "
        + f"lower_leg.R length {parent.length}"
    )


def test_multiple_children_no_right_fingers(context: Context) -> None:
    clean_scene(context)
    ops.icyp.make_basic_armature()
    armature = context.view_layer.objects.active
    if not armature or not isinstance(armature.data, Armature):
        message = "No armature"
        raise AssertionError(message)

    bpy.ops.object.mode_set(mode="EDIT")
    for name in [
        "thumb_proximal.R",
        "thumb_intermediate.R",
        "thumb_distal.R",
        "index_proximal.R",
        "index_intermediate.R",
        "index_distal.R",
        "middle_proximal.R",
        "middle_intermediate.R",
        "middle_distal.R",
        "ring_proximal.R",
        "ring_intermediate.R",
        "ring_distal.R",
        "little_proximal.R",
        "little_intermediate.R",
        "little_distal.R",
    ]:
        armature.data.edit_bones.remove(armature.data.edit_bones[name])
    right_hand = armature.data.edit_bones["hand.R"]
    right_hand.tail = Vector((-0.5, -0.5, 1))

    right_hand_child1 = armature.data.edit_bones.new("hand_child1.R")
    right_hand_child1.parent = right_hand
    right_hand_child1.head = Vector((-0.5, -0.25, 1.5))
    right_hand_child1.tail = Vector((-0.5, -0.5, 1.5))

    right_hand_child2 = armature.data.edit_bones.new("hand_child2.R")
    right_hand_child2.parent = right_hand
    right_hand_child2.head = Vector((-0.75, -0.25, 1.5))
    right_hand_child2.tail = Vector((-0.75, -0.5, 1.5))

    bpy.ops.object.mode_set(mode="OBJECT")
    # return
    setup_bones(context, armature)

    bpy.ops.object.mode_set(mode="EDIT")
    right_lower_arm = armature.data.edit_bones["lower_arm.R"]
    right_hand = armature.data.edit_bones["hand.R"]
    assert_vector3_equals(
        right_lower_arm.vector.normalized(),
        right_hand.vector.normalized(),
        "lower_hand.R and hand.R direction are same direction",
    )

    parent = right_hand.parent
    if not parent:
        message = "hand.R has no parent"
        raise AssertionError(message)

    assert (right_hand.length * 2 - parent.length) < 0.0001, (
        f"hand.R length {right_hand.length} is half as "
        + f"lower_arm.R length {parent.length}"
    )


def test_left_finger_only_multiple_children_index_intermediate(
    context: Context,
) -> None:
    clean_scene(context)
    ops.icyp.make_basic_armature()
    armature = context.view_layer.objects.active
    if not armature or not isinstance(armature.data, Armature):
        message = "No armature"
        raise AssertionError(message)

    bpy.ops.object.mode_set(mode="EDIT")
    for name in [
        "thumb_proximal.R",
        "thumb_intermediate.R",
        "thumb_distal.R",
        "index_proximal.R",
        "index_distal.R",
        "middle_proximal.R",
        "middle_intermediate.R",
        "middle_distal.R",
        "ring_proximal.R",
        "ring_intermediate.R",
        "ring_distal.R",
        "little_proximal.R",
        "little_intermediate.R",
        "little_distal.R",
    ]:
        armature.data.edit_bones.remove(armature.data.edit_bones[name])
    right_hand = armature.data.edit_bones["hand.R"]
    right_hand.tail = Vector((-0.5, -0.5, 1))
    right_index_intermediate = armature.data.edit_bones["index_intermediate.R"]
    right_index_intermediate.tail = Vector((-1, -0.5, 1))

    right_index_intermediate_child1 = armature.data.edit_bones.new(
        "index_intermediate_child1.R"
    )
    right_index_intermediate_child1.parent = right_index_intermediate
    right_index_intermediate_child1.head = Vector((-0.5, -0.25, 1.5))
    right_index_intermediate_child1.tail = Vector((-0.5, -0.5, 1.5))

    right_index_intermediate_child2 = armature.data.edit_bones.new(
        "index_intermediate_child2.R"
    )
    right_index_intermediate_child2.parent = right_index_intermediate
    right_index_intermediate_child2.head = Vector((-0.75, -0.25, 1.5))
    right_index_intermediate_child2.tail = Vector((-0.75, -0.5, 1.5))

    bpy.ops.object.mode_set(mode="OBJECT")
    # return
    setup_bones(context, armature)

    bpy.ops.object.mode_set(mode="EDIT")
    right_index_intermediate = armature.data.edit_bones["index_intermediate.R"]
    right_hand = armature.data.edit_bones["hand.R"]
    assert_vector3_equals(
        right_index_intermediate.vector.normalized(),
        right_hand.vector.normalized(),
        "index_intermediate.R and hand.R direction are same direction",
    )

    parent = right_index_intermediate.parent
    if not parent:
        message = "hand.R has no parent"
        raise AssertionError(message)

    assert (right_index_intermediate.length * 2 - parent.length) < 0.0001, (
        f"index_intermediate.R length {right_index_intermediate.length} is half as "
        + f"hand.R length {parent.length}"
    )


FUNCTIONS = [
    test_eye_bone_world_minus_y,
    test_head_bone_world_plus_z,
    test_multiple_children_right_toes_direction_is_same_as_foot,
    test_multiple_children_no_left_toes,
    test_multiple_children_no_right_fingers,
    test_left_finger_only_multiple_children_index_intermediate,
]


def test(context: Context, function_name: str) -> None:
    function = next((f for f in FUNCTIONS if f.__name__ == function_name), None)
    if function is None:
        message = f"No function name: {function_name}"
        raise AssertionError(message)
    function(context)


if __name__ == "__main__":
    context = bpy.context
    test_case_args = None
    if "--" in sys.argv and len(sys.argv) == (sys.argv.index("--") + 2):
        test_case_args = sys.argv[slice(sys.argv.index("--") + 1, sys.maxsize)]
    if test_case_args and test_case_args[0]:
        test(context, *test_case_args)
    else:
        for arg in get_test_command_args():
            test(context, *arg)
