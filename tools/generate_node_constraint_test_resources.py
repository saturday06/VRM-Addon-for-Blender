#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import logging
import math
import shutil
import sys
from enum import Enum
from pathlib import Path

import bpy
from bpy.types import (
    Armature,
    Context,
    CopyRotationConstraint,
    DampedTrackConstraint,
    Object,
)

from io_scene_vrm.common import ops
from io_scene_vrm.common.workspace import save_workspace

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TestConstraint(Enum):
    ROTATION_CONSTRAINT = 1
    AIM_CONSTRAINT_X = 2
    AIM_CONSTRAINT_Y = 3
    AIM_CONSTRAINT_Z = 4
    AIM_CONSTRAINT_NEGATIVE_X = 5
    AIM_CONSTRAINT_NEGATIVE_Y = 6
    AIM_CONSTRAINT_NEGATIVE_Z = 7
    ROLL_CONSTRAINT_X = 8
    ROLL_CONSTRAINT_Y = 9
    ROLL_CONSTRAINT_Z = 10


def generate_constraint_vrm(
    context: Context,
    armature_obj: Object,
    base_bone_name: str,
    roll_degree: float,
    x: float,
    z: float,
    parent_roll_degree: float,
    parent_x: float,
    parent_z: float,
    test_constraint: TestConstraint,
) -> None:
    source_parent_bone_name = f"{base_bone_name}1:constraint_source_parent"
    source_bone_name = f"{base_bone_name}2:constraint_source"
    source_axis_obj = context.blend_data.objects.get("ConstraintSource")
    if not source_axis_obj:
        raise AssertionError

    with save_workspace(context, armature_obj, mode="EDIT"):
        armature_data = armature_obj.data
        if not isinstance(armature_data, Armature):
            raise TypeError

        source_parent_bone = armature_data.edit_bones.get(source_parent_bone_name)
        if not source_parent_bone:
            raise AssertionError

        source_bone = armature_data.edit_bones.get(source_bone_name)
        if not source_bone:
            raise AssertionError

        source_bone.roll += math.radians(roll_degree)
        source_bone.tail = (
            source_bone.tail.x + x,
            source_bone.tail.y,
            source_bone.tail.z + z,
        )

        source_parent_bone.roll += math.radians(parent_roll_degree)
        source_parent_bone.tail = (
            source_parent_bone.tail.x + parent_x,
            source_parent_bone.tail.y,
            source_parent_bone.tail.z + parent_z,
        )

    source_bone = armature_obj.pose.bones.get(source_bone_name)
    if not source_bone:
        raise AssertionError

    target_bone = armature_obj.pose.bones.get("spine:constraint_target")
    if not target_bone:
        raise AssertionError

    source_axis_obj.parent = armature_obj
    source_axis_obj.parent_type = "BONE"
    source_axis_obj.parent_bone = source_bone_name
    source_axis_obj.location = (0, -source_bone.bone.length, 0)

    if test_constraint in [
        TestConstraint.AIM_CONSTRAINT_X,
        TestConstraint.AIM_CONSTRAINT_Y,
        TestConstraint.AIM_CONSTRAINT_Z,
        TestConstraint.AIM_CONSTRAINT_NEGATIVE_X,
        TestConstraint.AIM_CONSTRAINT_NEGATIVE_Y,
        TestConstraint.AIM_CONSTRAINT_NEGATIVE_Z,
    ]:
        constraint = source_bone.constraints.new(type="DAMPED_TRACK")
        if not isinstance(constraint, DampedTrackConstraint):
            raise TypeError

        constraint.influence = 1

        if test_constraint == TestConstraint.AIM_CONSTRAINT_X:
            constraint.track_axis = "TRACK_X"
        elif test_constraint == TestConstraint.AIM_CONSTRAINT_Y:
            constraint.track_axis = "TRACK_Y"
        elif test_constraint == TestConstraint.AIM_CONSTRAINT_Z:
            constraint.track_axis = "TRACK_Z"
        elif test_constraint == TestConstraint.AIM_CONSTRAINT_NEGATIVE_X:
            constraint.track_axis = "TRACK_NEGATIVE_X"
        elif test_constraint == TestConstraint.AIM_CONSTRAINT_NEGATIVE_Y:
            constraint.track_axis = "TRACK_NEGATIVE_Y"
        elif test_constraint == TestConstraint.AIM_CONSTRAINT_NEGATIVE_Z:
            constraint.track_axis = "TRACK_NEGATIVE_Z"
        else:
            raise AssertionError
    elif test_constraint in [
        TestConstraint.ROTATION_CONSTRAINT,
        TestConstraint.ROLL_CONSTRAINT_X,
        TestConstraint.ROLL_CONSTRAINT_Y,
        TestConstraint.ROLL_CONSTRAINT_Z,
    ]:
        constraint = source_bone.constraints.new(type="COPY_ROTATION")
        if not isinstance(constraint, CopyRotationConstraint):
            raise TypeError

        constraint.mix_mode = "ADD"
        constraint.owner_space = "LOCAL"
        constraint.target_space = "LOCAL"
        constraint.influence = 1
        constraint.use_x = False
        constraint.use_y = False
        constraint.use_z = False

        if test_constraint == TestConstraint.ROTATION_CONSTRAINT:
            constraint.use_x = True
            constraint.use_y = True
            constraint.use_z = True
        elif test_constraint == TestConstraint.ROLL_CONSTRAINT_X:
            constraint.use_x = True
        elif test_constraint == TestConstraint.ROLL_CONSTRAINT_Y:
            constraint.use_y = True
        elif test_constraint == TestConstraint.ROLL_CONSTRAINT_Z:
            constraint.use_z = True
        else:
            raise AssertionError
    else:
        raise AssertionError

    constraint.target = armature_obj
    constraint.subtarget = target_bone.name

    vrm_path = (
        Path(__file__).parent.parent
        / "tests"
        / "resources"
        / "vrma"
        / (
            "temp_"
            + f"{str(test_constraint.name).replace('.', '_').lower()}_{base_bone_name}_"
            + f"roll{roll_degree}_x{x}_z{z}_"
            + f"proll{parent_roll_degree}_px{parent_x}_pz{parent_z}"
            + ".vrm"
        )
    )
    vrm_path.parent.mkdir(parents=True, exist_ok=True)
    result = ops.export_scene.vrm(
        filepath=str(vrm_path), armature_object_name=armature_obj.name
    )
    if result != {"FINISHED"}:
        message = f"Export error {vrm_path} {result}"
        raise AssertionError(message)
    vrma_path = vrm_path.with_suffix(".vrma")
    default_vrma_path = (
        Path(__file__).parent.parent
        / "tests"
        / "resources"
        / "node_constraint"
        / "hips_spine_twisting.vrma"
    )
    shutil.copy(src=default_vrma_path, dst=vrma_path)

    blend_path = vrm_path.with_suffix(".blend")
    result = bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    if result != {"FINISHED"}:
        message = f"Export error {blend_path} {result}"
        raise AssertionError(message)


def main() -> int:
    context = bpy.context

    bpy.ops.preferences.addon_enable(module="io_scene_vrm")

    for (
        base_bone_name,
        roll,
        x,
        z,
        parent_roll,
        parent_x,
        parent_z,
        test_constraint,
    ) in (
        (
            base_bone_name,
            roll,
            x,
            z,
            parent_roll,
            parent_x,
            parent_z,
            test_constraint,
        )
        for base_bone_name in [
            # "parent",
            "child",
            "sibling",
        ]
        for roll in [0, 45]
        for x in [0, 0.25]
        for z in [0, 0.25]
        for parent_roll in [0, 45]
        for parent_x in [0, 0.25]
        for parent_z in [0, 0.25]
        for test_constraint in TestConstraint
    ):
        bpy.ops.wm.read_homefile(use_empty=True)
        bpy.ops.wm.open_mainfile(
            filepath=str(
                Path(__file__).parent.parent
                / "tests"
                / "resources"
                / "node_constraint"
                / "node_constraint_template.blend"
            )
        )

        armature_obj = next(
            (obj for obj in context.blend_data.objects if obj.type == "ARMATURE"),
            None,
        )
        if not armature_obj:
            raise AssertionError

        with save_workspace(context, armature_obj):
            generate_constraint_vrm(
                context,
                armature_obj,
                base_bone_name,
                roll,
                x,
                z,
                parent_roll,
                parent_x,
                parent_z,
                test_constraint,
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
