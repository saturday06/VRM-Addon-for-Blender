# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Mapping
from typing import Optional
from unittest import TestCase, main

import bpy
from bpy.types import Armature, EditBone, Object
from mathutils import Vector

from io_scene_vrm.common import ops
from io_scene_vrm.common.debug import clean_scene
from io_scene_vrm.common.vrm0.human_bone import (
    HumanBoneSpecification,
    HumanBoneSpecifications,
)
from io_scene_vrm.editor.property_group import BonePropertyGroup

Tree = dict[str, "Tree"]


class TestBonePropertyGroup(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        bpy.ops.preferences.addon_enable(module="io_scene_vrm")

    def setUp(self) -> None:
        clean_scene(bpy.context)

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

        got = BonePropertyGroup.find_bone_candidates(
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

        if context.view_layer.objects.active:
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete()
        while context.blend_data.collections:
            context.blend_data.collections.remove(context.blend_data.collections[0])

        ops.icyp.make_basic_armature()
        armatures = [
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        ]
        self.assertEqual(len(armatures), 1)
        armature = armatures[0]

        for props, _vrm0, _vrm1 in BonePropertyGroup.get_all_bone_property_groups(
            armature
        ):
            self.assertTrue(
                (props.__class__.__module__ + "." + props.__class__.__name__).endswith(
                    ".editor.property_group.BonePropertyGroup"
                )
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


if __name__ == "__main__":
    main()
