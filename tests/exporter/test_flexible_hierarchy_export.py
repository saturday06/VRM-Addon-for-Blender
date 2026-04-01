# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import main

import bpy
from bpy.types import Armature, Object
from mathutils import Vector

from io_scene_vrm.common import ops
from io_scene_vrm.editor import search
from io_scene_vrm.editor.extension import get_armature_extension
from io_scene_vrm.exporter.vrm0_exporter import Vrm0Exporter
from io_scene_vrm.exporter.vrm1_exporter import Vrm1Exporter
from tests.util import AddonTestCase


class TestFlexibleHierarchyExport(AddonTestCase):
    def create_or_reparent_bone(
        self,
        armature: Object,
        bone_name: str,
        parent_name: str,
    ) -> None:
        if not isinstance(armature.data, Armature):
            raise TypeError
        armature_data = armature.data

        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode="EDIT")

        bone = armature_data.edit_bones.get(bone_name)
        if bone is None:
            bone = armature_data.edit_bones.new(bone_name)
            bone.head = Vector((0, 0, 1))
            bone.tail = Vector((0, 0.1, 1))

        parent = armature_data.edit_bones.get(parent_name)
        if parent is None:
            parent = armature_data.edit_bones.new(parent_name)
            parent.head = Vector((0, 0, 0))
            parent.tail = Vector((0, 0.1, 0))

        bone.parent = parent
        bpy.ops.object.mode_set(mode="OBJECT")

    def set_edit_bone_parent(
        self,
        armature: Object,
        bone_name: str,
        parent_name: str,
    ) -> None:
        if not isinstance(armature.data, Armature):
            raise TypeError

        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode="EDIT")
        edit_bone = armature.data.edit_bones.get(bone_name)
        if edit_bone is None:
            bpy.ops.object.mode_set(mode="OBJECT")
            message = f"Missing edit bone: {bone_name}"
            raise ValueError(message)

        edit_parent = armature.data.edit_bones.get(parent_name)
        edit_bone.parent = edit_parent
        bpy.ops.object.mode_set(mode="OBJECT")

    def assert_bone_parent_name(
        self, armature: Object, bone_name: str, parent_name: str
    ) -> None:
        if not isinstance(armature.data, Armature):
            raise TypeError

        parent = armature.data.bones[bone_name].parent
        self.assertIsNotNone(parent)
        if parent is None:
            raise ValueError
        self.assertEqual(parent.name, parent_name)

    def export_objects(self, armature: Object) -> list[Object]:
        return search.export_objects(
            bpy.context,
            armature.name,
            export_invisibles=True,
            export_only_selections=False,
            export_lights=False,
        )

    def test_vrm1_flexible_hierarchy_reparent_and_restore(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        self.create_or_reparent_bone(armature, "hips", "root")
        self.create_or_reparent_bone(armature, "spine", "root")
        self.set_edit_bone_parent(armature, "spine", "root")

        human_bones = get_armature_extension(armature.data).vrm1.humanoid.human_bones
        human_bones.filter_by_human_bone_hierarchy = False
        human_bones.hips.node.bone_name = "hips"
        human_bones.spine.node.bone_name = "spine"

        original_parent_name = (
            armature.data.bones["spine"].parent.name
            if armature.data.bones["spine"].parent
            else None
        )
        self.assertEqual(original_parent_name, "root")

        with Vrm1Exporter.setup_flexible_hierarchy_bones(
            context,
            armature,
            self.export_objects(armature),
        ):
            spine_parent = armature.data.bones["spine"].parent
            self.assertIsNotNone(spine_parent)
            if spine_parent is None:
                raise ValueError
            self.assertEqual(spine_parent.name, "hips")

        restored_parent_name = (
            armature.data.bones["spine"].parent.name
            if armature.data.bones["spine"].parent
            else None
        )
        self.assertEqual(restored_parent_name, "root")

    def test_vrm0_flexible_hierarchy_reparent_and_restore(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        self.create_or_reparent_bone(armature, "hips", "root")
        self.create_or_reparent_bone(armature, "spine", "root")
        self.set_edit_bone_parent(armature, "spine", "root")

        humanoid = get_armature_extension(armature.data).vrm0.humanoid
        humanoid.filter_by_human_bone_hierarchy = False
        hips_human_bone = next(
            human_bone
            for human_bone in humanoid.human_bones
            if human_bone.bone == "hips"
        )
        spine_human_bone = next(
            human_bone
            for human_bone in humanoid.human_bones
            if human_bone.bone == "spine"
        )
        hips_human_bone.node.bone_name = "hips"
        spine_human_bone.node.bone_name = "spine"

        original_parent_name = (
            armature.data.bones["spine"].parent.name
            if armature.data.bones["spine"].parent
            else None
        )
        self.assertEqual(original_parent_name, "root")

        with Vrm0Exporter.setup_flexible_hierarchy_bones(
            context,
            armature,
            self.export_objects(armature),
        ):
            spine_parent = armature.data.bones["spine"].parent
            self.assertIsNotNone(spine_parent)
            if spine_parent is None:
                raise ValueError
            self.assertEqual(spine_parent.name, "hips")

        restored_parent_name = (
            armature.data.bones["spine"].parent.name
            if armature.data.bones["spine"].parent
            else None
        )
        self.assertEqual(restored_parent_name, "root")

    def test_vrm1_flexible_hierarchy_keeps_unassigned_intermediate_bones(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        self.create_or_reparent_bone(armature, "hips", "root")
        self.create_or_reparent_bone(armature, "spine_helper_1", "hips")
        self.create_or_reparent_bone(armature, "spine_helper_2", "spine_helper_1")
        self.create_or_reparent_bone(armature, "spine", "spine_helper_2")

        human_bones = get_armature_extension(armature.data).vrm1.humanoid.human_bones
        human_bones.filter_by_human_bone_hierarchy = False
        human_bones.hips.node.bone_name = "hips"
        human_bones.spine.node.bone_name = "spine"

        with Vrm1Exporter.setup_flexible_hierarchy_bones(
            context,
            armature,
            self.export_objects(armature),
        ):
            spine_parent = armature.data.bones["spine"].parent
            self.assertIsNotNone(spine_parent)
            if spine_parent is None:
                raise ValueError
            self.assertEqual(spine_parent.name, "spine_helper_2")
            self.assert_bone_parent_name(armature, "spine_helper_2", "spine_helper_1")
            self.assert_bone_parent_name(armature, "spine_helper_1", "hips")

        self.assert_bone_parent_name(armature, "spine", "spine_helper_2")

    def test_vrm1_flexible_hierarchy_keeps_unassigned_optional_human_bone(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        self.set_edit_bone_parent(armature, "neck", "root")

        human_bones = get_armature_extension(armature.data).vrm1.humanoid.human_bones
        human_bones.filter_by_human_bone_hierarchy = False
        human_bones.upper_chest.node.bone_name = ""
        human_bones.chest.node.bone_name = ""

        with Vrm1Exporter.setup_flexible_hierarchy_bones(
            context,
            armature,
            self.export_objects(armature),
        ):
            neck_parent = armature.data.bones["neck"].parent
            self.assertIsNotNone(neck_parent)
            if neck_parent is None:
                raise ValueError
            self.assertEqual(neck_parent.name, "spine")

        self.assert_bone_parent_name(armature, "neck", "root")

    def test_vrm1_flexible_hierarchy_keeps_unassigned_hips_ancestors(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        self.create_or_reparent_bone(armature, "hips_root_1", "root")
        self.create_or_reparent_bone(armature, "hips_root_2", "hips_root_1")
        self.create_or_reparent_bone(armature, "hips", "hips_root_2")

        human_bones = get_armature_extension(armature.data).vrm1.humanoid.human_bones
        human_bones.filter_by_human_bone_hierarchy = False
        human_bones.hips.node.bone_name = "hips"

        with Vrm1Exporter.setup_flexible_hierarchy_bones(
            context,
            armature,
            self.export_objects(armature),
        ):
            hips_parent = armature.data.bones["hips"].parent
            self.assertIsNotNone(hips_parent)
            if hips_parent is None:
                raise ValueError
            self.assertEqual(hips_parent.name, "hips_root_2")
            self.assert_bone_parent_name(armature, "hips_root_2", "hips_root_1")

        self.assert_bone_parent_name(armature, "hips", "hips_root_2")

    def test_vrm1_dummy_human_bones_when_non_humanoid_missing_required(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        human_bones = get_armature_extension(armature.data).vrm1.humanoid.human_bones
        human_bones.allow_non_humanoid_rig = True
        human_bones.hips.node.bone_name = ""

        with Vrm1Exporter.setup_dummy_human_bones(context, armature):
            self.assertNotEqual(human_bones.hips.node.bone_name, "")

        self.assertEqual(human_bones.hips.node.bone_name, "")

    def test_vrm0_flexible_hierarchy_keeps_unassigned_intermediate_bones(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        self.create_or_reparent_bone(armature, "hips", "root")
        self.create_or_reparent_bone(armature, "spine_helper_1", "hips")
        self.create_or_reparent_bone(armature, "spine_helper_2", "spine_helper_1")
        self.create_or_reparent_bone(armature, "spine", "spine_helper_2")

        humanoid = get_armature_extension(armature.data).vrm0.humanoid
        humanoid.filter_by_human_bone_hierarchy = False
        hips_human_bone = next(
            human_bone
            for human_bone in humanoid.human_bones
            if human_bone.bone == "hips"
        )
        spine_human_bone = next(
            human_bone
            for human_bone in humanoid.human_bones
            if human_bone.bone == "spine"
        )
        hips_human_bone.node.bone_name = "hips"
        spine_human_bone.node.bone_name = "spine"

        with Vrm0Exporter.setup_flexible_hierarchy_bones(
            context,
            armature,
            self.export_objects(armature),
        ):
            self.assert_bone_parent_name(armature, "spine", "spine_helper_2")
            self.assert_bone_parent_name(armature, "spine_helper_2", "spine_helper_1")
            self.assert_bone_parent_name(armature, "spine_helper_1", "hips")

        self.assert_bone_parent_name(armature, "spine", "spine_helper_2")

    def test_vrm0_flexible_hierarchy_keeps_unassigned_optional_human_bone(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        self.set_edit_bone_parent(armature, "neck", "root")

        humanoid = get_armature_extension(armature.data).vrm0.humanoid
        humanoid.filter_by_human_bone_hierarchy = False
        upper_chest_human_bone = next(
            human_bone
            for human_bone in humanoid.human_bones
            if human_bone.bone == "upperChest"
        )
        upper_chest_human_bone.node.bone_name = ""

        with Vrm0Exporter.setup_flexible_hierarchy_bones(
            context,
            armature,
            self.export_objects(armature),
        ):
            self.assert_bone_parent_name(armature, "neck", "chest")

        self.assert_bone_parent_name(armature, "neck", "root")

    def test_vrm0_flexible_hierarchy_keeps_unassigned_hips_ancestors(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        self.create_or_reparent_bone(armature, "hips_root_1", "root")
        self.create_or_reparent_bone(armature, "hips_root_2", "hips_root_1")
        self.create_or_reparent_bone(armature, "hips", "hips_root_2")

        humanoid = get_armature_extension(armature.data).vrm0.humanoid
        humanoid.filter_by_human_bone_hierarchy = False
        hips_human_bone = next(
            human_bone
            for human_bone in humanoid.human_bones
            if human_bone.bone == "hips"
        )
        hips_human_bone.node.bone_name = "hips"

        with Vrm0Exporter.setup_flexible_hierarchy_bones(
            context,
            armature,
            self.export_objects(armature),
        ):
            self.assert_bone_parent_name(armature, "hips", "hips_root_2")
            self.assert_bone_parent_name(armature, "hips_root_2", "hips_root_1")

        self.assert_bone_parent_name(armature, "hips", "hips_root_2")

    def test_vrm0_flexible_hierarchy_mutes_and_restores_constraints(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        self.create_or_reparent_bone(armature, "hips", "root")
        self.create_or_reparent_bone(armature, "spine", "root")

        humanoid = get_armature_extension(armature.data).vrm0.humanoid
        humanoid.filter_by_human_bone_hierarchy = False
        hips_human_bone = next(
            human_bone
            for human_bone in humanoid.human_bones
            if human_bone.bone == "hips"
        )
        spine_human_bone = next(
            human_bone
            for human_bone in humanoid.human_bones
            if human_bone.bone == "spine"
        )
        hips_human_bone.node.bone_name = "hips"
        spine_human_bone.node.bone_name = "spine"

        constraint = armature.pose.bones["spine"].constraints.new("LIMIT_ROTATION")
        self.assertFalse(constraint.mute)

        with Vrm0Exporter.setup_flexible_hierarchy_bones(
            context,
            armature,
            self.export_objects(armature),
        ):
            self.assertTrue(constraint.mute)

        self.assertFalse(constraint.mute)


if __name__ == "__main__":
    main()
