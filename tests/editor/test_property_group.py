# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import re
from collections.abc import Mapping
from typing import Optional
from unittest import main

import bpy
from bpy.types import Armature, EditBone, Object
from mathutils import Vector

from io_scene_vrm.common import ops
from io_scene_vrm.common.vrm0.human_bone import (
    HumanBoneName as Vrm0HumanBoneName,
)
from io_scene_vrm.common.vrm0.human_bone import (
    HumanBoneSpecification,
    HumanBoneSpecifications,
)
from io_scene_vrm.editor.extension import get_armature_extension
from io_scene_vrm.editor.property_group import (
    BonePropertyGroup,
    HumanoidStructureBonePropertyGroup,
)
from io_scene_vrm.editor.vrm0.property_group import Vrm0HumanoidPropertyGroup
from io_scene_vrm.editor.vrm1.property_group import Vrm1HumanBonesPropertyGroup
from tests.util import AddonTestCase

Tree = Mapping[str, "Tree"]


class TestBonePropertyGroup(AddonTestCase):
    def assert_bone_candidates(
        self,
        armature: Object,
        *,
        tree: Mapping[str, Tree],
        mapping: Mapping[str, HumanBoneSpecification],
        target: HumanBoneSpecification,
        expected: set[str],
    ) -> None:
        bpy.ops.object.mode_set(mode="EDIT")
        if not isinstance(armature.data, Armature):
            raise TypeError
        for bone in list(armature.data.edit_bones):
            armature.data.edit_bones.remove(bone)
        parent_and_trees: list[tuple[Optional[EditBone], Mapping[str, Tree]]] = [
            (None, tree)
        ]
        while parent_and_trees:
            (parent, tree) = parent_and_trees.pop()
            for child_name, child_tree in tree.items():
                child = armature.data.edit_bones.new(child_name)
                child.head = Vector((0, 0, 1))
                if parent:
                    child.parent = parent
                parent_and_trees.append((child, child_tree))

        bpy.ops.object.mode_set(mode="OBJECT")

        got = HumanoidStructureBonePropertyGroup.find_bone_candidates(
            armature.data,
            target,
            mapping,
            [],
        )
        diffs = got.symmetric_difference(expected)
        if diffs:
            raise AssertionError("Unexpected diff:\n" + ",".join(diffs))

    def test_bone_filter(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armatures = [
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        ]
        self.assertEqual(len(armatures), 1)
        armature = armatures[0]

        for props, _props_type in BonePropertyGroup.get_all_bone_property_groups(
            armature
        ):
            class_name = props.__class__.__module__ + "." + props.__class__.__name__
            self.assertRegex(
                class_name,
                ".*("
                + re.escape(".editor.property_group.BonePropertyGroup")
                + "|"
                + re.escape(".editor.property_group.HumanoidStructureBonePropertyGroup")
                + "|"
                + re.escape(
                    ".editor.vrm0.property_group.Vrm0HumanoidBoneNodePropertyGroup"
                )
                + "|"
                + re.escape(
                    ".editor.vrm1.property_group.Vrm1HumanBoneNodePropertyGroup"
                )
                + ")$",
            )

        self.assert_bone_candidates(
            armature,
            tree={},
            mapping={},
            target=HumanBoneSpecifications.HIPS,
            expected=set(),
        )

        self.assert_bone_candidates(
            armature,
            tree={"hips": {}},
            mapping={},
            target=HumanBoneSpecifications.HIPS,
            expected={"hips"},
        )

        self.assert_bone_candidates(
            armature,
            tree={"hips": {}},
            mapping={"hips": HumanBoneSpecifications.HIPS},
            target=HumanBoneSpecifications.HIPS,
            expected={"hips"},
        )

        self.assert_bone_candidates(
            armature,
            tree={"hips": {"spine": {}}},
            mapping={},
            target=HumanBoneSpecifications.HIPS,
            expected={"hips", "spine"},
        )

        self.assert_bone_candidates(
            armature,
            tree={"hips": {"spine": {}}},
            mapping={"hips": HumanBoneSpecifications.HIPS},
            target=HumanBoneSpecifications.SPINE,
            expected={"spine"},
        )

        self.assert_bone_candidates(
            armature,
            tree={"hips": {"spine": {"head": {}}}},
            mapping={
                "hips": HumanBoneSpecifications.HIPS,
                "head": HumanBoneSpecifications.HEAD,
            },
            target=HumanBoneSpecifications.SPINE,
            expected={"spine"},
        )

        self.assert_bone_candidates(
            armature,
            tree={"hips": {"spine": {"head": {}}}},
            mapping={
                "hips": HumanBoneSpecifications.HIPS,
            },
            target=HumanBoneSpecifications.SPINE,
            expected={"spine", "head"},
        )

        self.assert_bone_candidates(
            armature,
            tree={
                "hips": {
                    "spine": {"chest": {"head": {"jaw": {}}}},
                    "tail": {},
                }
            },
            mapping={
                "hips": HumanBoneSpecifications.HIPS,
                "head": HumanBoneSpecifications.HEAD,
            },
            target=HumanBoneSpecifications.SPINE,
            expected={"spine", "chest"},
        )

    def test_vrm0_flexible_hierarchy_candidates(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        armature_data = armature.data
        ext = get_armature_extension(armature_data)
        humanoid = ext.vrm0.humanoid
        humanoid.filter_by_human_bone_hierarchy = False
        humanoid_hips = next(
            human_bone
            for human_bone in humanoid.human_bones
            if human_bone.bone == Vrm0HumanBoneName.HIPS.value
        )

        Vrm0HumanoidPropertyGroup.update_all_bone_name_candidates(
            context,
            armature_data.name,
            force=True,
        )

        self.assertEqual(
            {"root", "hips"},
            set(humanoid_hips.node.bone_name_candidates),
        )

    def test_vrm1_flexible_hierarchy_candidates(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        armature_data = armature.data
        ext = get_armature_extension(armature_data)
        human_bones = ext.vrm1.humanoid.human_bones
        human_bones.filter_by_human_bone_hierarchy = False

        Vrm1HumanBonesPropertyGroup.update_all_bone_name_candidates(
            context,
            armature_data.name,
            force=True,
        )

        self.assertEqual(
            {"head"},
            set(human_bones.head.node.bone_name_candidates),
        )


if __name__ == "__main__":
    main()
