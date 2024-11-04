# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from typing import Optional

import bpy
from bpy.types import Armature, Context, EditBone, Object
from mathutils import Vector

from io_scene_vrm.common import ops
from io_scene_vrm.common.vrm0.human_bone import (
    HumanBoneSpecification,
    HumanBoneSpecifications,
)
from io_scene_vrm.editor.property_group import BonePropertyGroup

Tree = dict[str, "Tree"]


def assert_bone_candidates(
    armature: Object,
    target_human_bone_specification: HumanBoneSpecification,
    bpy_bone_name_to_human_bone_specification: dict[str, HumanBoneSpecification],
    expected: set[str],
    tree: dict[str, Tree],
) -> None:
    bpy.ops.object.mode_set(mode="EDIT")
    if not isinstance(armature.data, Armature):
        raise TypeError
    for bone in list(armature.data.edit_bones):
        armature.data.edit_bones.remove(bone)
    parent_and_trees: list[tuple[Optional[EditBone], dict[str, Tree]]] = [(None, tree)]
    while parent_and_trees:
        (parent, tree) = parent_and_trees.pop()
        for child_name, child_tree in tree.items():
            child = armature.data.edit_bones.new(child_name)
            child.head = Vector((0, 0, 1))
            if parent:
                child.parent = parent
            parent_and_trees.append((child, child_tree))

    bpy.ops.object.mode_set(mode="OBJECT")

    got = BonePropertyGroup.find_bone_candidates(
        armature.data,
        target_human_bone_specification,
        bpy_bone_name_to_human_bone_specification,
    )
    diffs = got.symmetric_difference(expected)
    if diffs:
        raise AssertionError("Unexpected diff:\n" + ",".join(diffs))


def test(context: Context) -> None:
    if context.view_layer.objects.active:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    while context.blend_data.collections:
        context.blend_data.collections.remove(context.blend_data.collections[0])

    ops.icyp.make_basic_armature()
    armatures = [obj for obj in context.blend_data.objects if obj.type == "ARMATURE"]
    assert len(armatures) == 1
    armature = armatures[0]

    for props in BonePropertyGroup.get_all_bone_property_groups(armature):
        assert (props.__class__.__module__ + "." + props.__class__.__name__).endswith(
            ".editor.property_group.BonePropertyGroup"
        )

    assert_bone_candidates(armature, HumanBoneSpecifications.HIPS, {}, set(), {})
    assert_bone_candidates(
        armature, HumanBoneSpecifications.HIPS, {}, {"hips"}, {"hips": {}}
    )
    assert_bone_candidates(
        armature,
        HumanBoneSpecifications.HIPS,
        {"hips": HumanBoneSpecifications.HIPS},
        {"hips"},
        {"hips": {}},
    )
    assert_bone_candidates(
        armature,
        HumanBoneSpecifications.HIPS,
        {},
        {"hips", "spine"},
        {"hips": {"spine": {}}},
    )
    assert_bone_candidates(
        armature,
        HumanBoneSpecifications.SPINE,
        {"hips": HumanBoneSpecifications.HIPS},
        {"spine"},
        {"hips": {"spine": {}}},
    )
    assert_bone_candidates(
        armature,
        HumanBoneSpecifications.SPINE,
        {
            "hips": HumanBoneSpecifications.HIPS,
            "head": HumanBoneSpecifications.HEAD,
        },
        {"spine"},
        {"hips": {"spine": {"head": {}}}},
    )
    assert_bone_candidates(
        armature,
        HumanBoneSpecifications.SPINE,
        {
            "hips": HumanBoneSpecifications.HIPS,
        },
        {"spine", "head"},
        {"hips": {"spine": {"head": {}}}},
    )


if __name__ == "__main__":
    test(bpy.context)
