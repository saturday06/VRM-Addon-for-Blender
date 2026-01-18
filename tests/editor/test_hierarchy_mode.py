# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import main

import bpy
from bpy.types import Armature

from io_scene_vrm.common import ops
from io_scene_vrm.common.test_helper import AddonTestCase
from io_scene_vrm.editor.extension import get_armature_extension


class TestHierarchyMode(AddonTestCase):
    def test_vrm0_strict_mode_validation(self) -> None:
        """Test that Strict mode enforces hierarchy validation for VRM 0.x."""
        context = bpy.context

        ops.icyp.make_basic_armature()
        armatures = [
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        ]
        self.assertEqual(len(armatures), 1)
        armature = armatures[0]
        if not isinstance(armature.data, Armature):
            raise TypeError

        ext = get_armature_extension(armature.data)
        ext.spec_version = ext.SPEC_VERSION_VRM0
        humanoid = ext.vrm0.humanoid

        # Ensure Strict mode is set
        humanoid.hierarchy_mode = humanoid.HIERARCHY_MODE_STRICT

        # Valid hierarchy should pass
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})

        # Invalid hierarchy should fail
        spine_bone = next(b for b in humanoid.human_bones if b.bone == "spine")
        chest_bone = next(b for b in humanoid.human_bones if b.bone == "chest")
        spine_bone.node.bone_name = "chest"
        chest_bone.node.bone_name = "spine"
        self.assertEqual(ops.vrm.model_validate(), {"CANCELLED"})

    def test_vrm0_flexible_mode_validation(self) -> None:
        """Test that Flexible mode skips hierarchy validation for VRM 0.x."""
        context = bpy.context

        ops.icyp.make_basic_armature()
        armatures = [
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        ]
        self.assertEqual(len(armatures), 1)
        armature = armatures[0]
        if not isinstance(armature.data, Armature):
            raise TypeError

        ext = get_armature_extension(armature.data)
        ext.spec_version = ext.SPEC_VERSION_VRM0
        humanoid = ext.vrm0.humanoid

        # Set to Flexible mode
        humanoid.hierarchy_mode = humanoid.HIERARCHY_MODE_FLEXIBLE

        # Valid hierarchy should pass
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})

        # Invalid hierarchy should also pass in Flexible mode
        spine_bone = next(b for b in humanoid.human_bones if b.bone == "spine")
        chest_bone = next(b for b in humanoid.human_bones if b.bone == "chest")
        original_spine = spine_bone.node.bone_name
        original_chest = chest_bone.node.bone_name
        spine_bone.node.bone_name = original_chest
        chest_bone.node.bone_name = original_spine

        # Should pass despite invalid hierarchy
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})

    def test_vrm1_strict_mode_validation(self) -> None:
        """Test that Strict mode enforces hierarchy validation for VRM 1.0."""
        context = bpy.context

        ops.icyp.make_basic_armature()
        armatures = [
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        ]
        self.assertEqual(len(armatures), 1)
        armature = armatures[0]
        if not isinstance(armature.data, Armature):
            raise TypeError

        ext = get_armature_extension(armature.data)
        human_bones = ext.vrm1.humanoid.human_bones

        # Ensure Strict mode is set
        human_bones.hierarchy_mode = human_bones.HIERARCHY_MODE_STRICT

        # Valid hierarchy should pass
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})

        # Invalid hierarchy should fail
        spine_bone = human_bones.spine
        chest_bone = human_bones.chest
        spine_bone.node.bone_name = "chest"
        chest_bone.node.bone_name = "spine"
        self.assertEqual(ops.vrm.model_validate(), {"CANCELLED"})

    def test_vrm1_flexible_mode_validation(self) -> None:
        """Test that Flexible mode skips hierarchy validation for VRM 1.0."""
        context = bpy.context

        ops.icyp.make_basic_armature()
        armatures = [
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        ]
        self.assertEqual(len(armatures), 1)
        armature = armatures[0]
        if not isinstance(armature.data, Armature):
            raise TypeError

        ext = get_armature_extension(armature.data)
        human_bones = ext.vrm1.humanoid.human_bones

        # Set to Flexible mode
        human_bones.hierarchy_mode = human_bones.HIERARCHY_MODE_FLEXIBLE

        # Valid hierarchy should pass
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})

        # Invalid hierarchy should also pass in Flexible mode
        spine_bone = human_bones.spine
        chest_bone = human_bones.chest
        original_spine = spine_bone.node.bone_name
        original_chest = chest_bone.node.bone_name
        spine_bone.node.bone_name = original_chest
        chest_bone.node.bone_name = original_spine

        # Should pass despite invalid hierarchy
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})


if __name__ == "__main__":
    main()
