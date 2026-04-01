# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import main

import bpy
from bpy.types import Armature

from io_scene_vrm.common import ops
from io_scene_vrm.common.vrm1.human_bone import HumanBoneSpecifications
from io_scene_vrm.editor.extension import get_armature_extension
from tests.util import AddonTestCase


class TestVrm1HumanBonesPropertyGroup(AddonTestCase):
    def test_error_messages_report_parent_requirement(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        human_bones = get_armature_extension(armature.data).vrm1.humanoid.human_bones
        human_bone_name_to_human_bone = human_bones.human_bone_name_to_human_bone()

        target_specification = HumanBoneSpecifications.RIGHT_THUMB_DISTAL
        parent_specification = target_specification.parent
        if parent_specification is None:
            raise ValueError

        # Assign only child bone to trigger parent requirement diagnostics.
        human_bone_name_to_human_bone[parent_specification.name].node.bone_name = ""

        expected_parent_requirement_error = (
            f'Please assign "{parent_specification.title}" because '
            + f'"{target_specification.title}" requires it as its child bone.'
        )

        human_bones.filter_by_human_bone_hierarchy = True
        self.assertIn(
            expected_parent_requirement_error,
            human_bones.error_messages(),
        )

        human_bones.filter_by_human_bone_hierarchy = False
        self.assertIn(
            expected_parent_requirement_error,
            human_bones.error_messages(),
        )

    def test_duplicate_assignments_are_errors_in_flexible_mode(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armature = next(
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        )
        if not isinstance(armature.data, Armature):
            raise TypeError

        human_bones = get_armature_extension(armature.data).vrm1.humanoid.human_bones
        human_bones.filter_by_human_bone_hierarchy = False
        human_bones.spine.node.bone_name = human_bones.hips.node.bone_name

        self.assertFalse(human_bones.bones_are_correctly_assigned())
        self.assertTrue(human_bones.human_bone_duplication_error_messages())


if __name__ == "__main__":
    main()
