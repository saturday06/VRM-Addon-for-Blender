# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import bpy
import pytest
from bpy.types import Armature
from mathutils import Vector
from pytest_codspeed.plugin import BenchmarkFixture

from io_scene_vrm.common import ops
from io_scene_vrm.editor.extension import (
    get_armature_extension,
)


def generate_many_spring_bones() -> None:
    context = bpy.context
    bpy.ops.wm.read_homefile(use_empty=True)
    ops.icyp.make_basic_armature()

    if (
        not (armature_object := context.active_object)
        or not (armature_data := armature_object.data)
        or not isinstance(armature_data, Armature)
    ):
        raise TypeError

    ext = get_armature_extension(armature_data)
    ext.spec_version = ext.SPEC_VERSION_VRM1
    spring_bone1 = ext.spring_bone1

    bpy.ops.object.mode_set(mode="EDIT")

    edit_bones = armature_data.edit_bones
    root_bone_name = "hand.R"
    root_bone = edit_bones.get(root_bone_name)
    if not root_bone:
        raise AssertionError

    for bone_x in range(16):
        for bone_y in range(4):
            parent_bone_name = root_bone.name
            for bone_z in range(4):
                parent_bone = edit_bones[parent_bone_name]
                child_bone_name = f"mop_strand_x{bone_x}_y{bone_y}_z{bone_z}"
                child_bone = edit_bones.new(child_bone_name)

                # for cleanup, assign parent before error check
                child_bone.parent = parent_bone

                if child_bone.name != child_bone_name:
                    raise ValueError(child_bone_name)

                if parent_bone_name == root_bone.name:
                    child_bone.head = Vector((bone_x / 8.0, bone_y / 8.0, 0.0))
                else:
                    child_bone.head = parent_bone.tail.copy()
                child_bone.tail = Vector(
                    (bone_x / 8.0 + 1 * bone_z / 4, bone_y / 8.0, 0.0)
                )
                child_bone.use_connect = False
                parent_bone_name = child_bone_name

    bpy.ops.object.mode_set(mode="OBJECT")

    for root_mop_strand_bone in [
        b
        for b in armature_object.pose.bones
        if (p := b.parent) and p.name == root_bone_name
    ]:
        spring_index = len(spring_bone1.springs)

        r = ops.vrm.add_spring_bone1_spring(armature_object_name=armature_object.name)
        if r != {"FINISHED"}:
            raise ValueError(r)

        spring = spring_bone1.springs[spring_index]
        spring.vrm_name = root_mop_strand_bone.name

        mop_strand_bone = root_mop_strand_bone
        while mop_strand_bone:
            ops.vrm.add_spring_bone1_spring_joint(
                armature_object_name=armature_object.name,
                spring_index=spring_index,
            )
            joint = spring.joints[-1]
            joint.gravity_power = 1
            joint.drag_force = 1 / 512
            joint.stiffness = 1 / 1024
            joint.node.bone_name = mop_strand_bone.name

            if not mop_strand_bone.children:
                break
            mop_strand_bone = mop_strand_bone.children[0]


def test_spring_bone_assignment(benchmark: BenchmarkFixture) -> None:
    bpy.ops.preferences.addon_enable(module="io_scene_vrm")

    @benchmark
    def _() -> None:
        generate_many_spring_bones()


if __name__ == "__main__":
    pytest.main()
