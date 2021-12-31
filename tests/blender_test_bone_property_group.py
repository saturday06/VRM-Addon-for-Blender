import sys
from os.path import dirname
from typing import Any, Dict, List, Optional, Set, Tuple

import bpy

sys.path.insert(0, dirname(dirname(__file__)))

# pylint: disable=wrong-import-position;
from io_scene_vrm.common.human_bone import HumanBone, HumanBones  # noqa: E402
from io_scene_vrm.editor.property_group import BonePropertyGroup  # noqa: E402

# pylint: enable=wrong-import-position;


def assert_bone_candidates(
    armature: bpy.types.Object,
    target_human_bone: HumanBone,
    blender_bone_name_to_human_bone_dict: Dict[str, HumanBone],
    expected: Set[str],
    tree: Dict[str, Any],
) -> None:
    bpy.ops.object.mode_set(mode="EDIT")
    for bone in list(armature.data.edit_bones):
        armature.data.edit_bones.remove(bone)
    parent_and_trees: List[Tuple[Optional[bpy.types.Bone], Dict[str, Any]]] = [
        (None, tree)
    ]
    while parent_and_trees:
        (parent, tree) = parent_and_trees.pop()
        for child_name, child_tree in tree.items():
            child = armature.data.edit_bones.new(child_name)
            child.head = (0, 0, 1)
            if parent:
                child.parent = parent
            parent_and_trees.append((child, child_tree))
    bpy.ops.object.mode_set(mode="OBJECT")

    got = BonePropertyGroup.find_bone_candidates(
        armature.data,
        target_human_bone,
        blender_bone_name_to_human_bone_dict,
    )
    diffs = got.symmetric_difference(expected)
    if diffs:
        raise AssertionError("Unexpected diff:\n" + ",".join(diffs))


def test() -> None:
    bpy.ops.icyp.make_basic_armature()
    armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    assert len(armatures) == 1
    armature = armatures[0]

    for props in BonePropertyGroup.get_all_bone_property_groups(armature):
        assert (props.__class__.__module__ + "." + props.__class__.__name__).endswith(
            ".io_scene_vrm.editor.property_group.BonePropertyGroup"
        )

    assert_bone_candidates(armature, HumanBones.HIPS, {}, set(), {})
    assert_bone_candidates(armature, HumanBones.HIPS, {}, {"hips"}, {"hips": {}})
    assert_bone_candidates(
        armature, HumanBones.HIPS, {"hips": HumanBones.HIPS}, {"hips"}, {"hips": {}}
    )
    assert_bone_candidates(
        armature, HumanBones.HIPS, {}, {"hips", "spine"}, {"hips": {"spine": {}}}
    )
    assert_bone_candidates(
        armature,
        HumanBones.SPINE,
        {"hips": HumanBones.HIPS},
        {"spine"},
        {"hips": {"spine": {}}},
    )
    assert_bone_candidates(
        armature,
        HumanBones.SPINE,
        {
            "hips": HumanBones.HIPS,
            "head": HumanBones.HEAD,
        },
        {"spine"},
        {"hips": {"spine": {"head": {}}}},
    )
    assert_bone_candidates(
        armature,
        HumanBones.SPINE,
        {
            "hips": HumanBones.HIPS,
        },
        {"spine", "head"},
        {"hips": {"spine": {"head": {}}}},
    )


if __name__ == "__main__":
    test()
