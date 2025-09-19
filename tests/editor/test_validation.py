# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import main

import bpy
from bpy.types import Armature

from io_scene_vrm.common import ops
from io_scene_vrm.common.test_helper import AddonTestCase
from io_scene_vrm.editor.extension import get_armature_extension


class TestValidation(AddonTestCase):
    def test_vrm0_bone_order_validation(self) -> None:
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
        humanoid = ext.vrm0.humanoid
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})

        spine_bone = next(b for b in humanoid.human_bones if b.bone == "spine")
        chest_bone = next(b for b in humanoid.human_bones if b.bone == "chest")
        spine_bone.node.bone_name = "chest"
        chest_bone.node.bone_name = "spine"
        self.assertEqual(ops.vrm.model_validate(), {"CANCELLED"})
        spine_bone.node.bone_name = "spine"
        chest_bone.node.bone_name = "chest"
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})

        right_little_distal_bone = next(
            b for b in humanoid.human_bones if b.bone == "rightLittleDistal"
        )
        right_little_distal_bone.node.bone_name = "spine"
        self.assertEqual(ops.vrm.model_validate(), {"CANCELLED"})
        right_little_distal_bone.node.bone_name = "hips"
        self.assertEqual(ops.vrm.model_validate(), {"CANCELLED"})
        right_little_distal_bone.node.bone_name = "little_distal.L"
        self.assertEqual(ops.vrm.model_validate(), {"CANCELLED"})
        right_little_distal_bone.node.bone_name = ""
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})
        right_little_distal_bone.node.bone_name = "little_distal.R"
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})

    def test_vrm1_bone_order_validation(self) -> None:
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
        ext.spec_version = ext.SPEC_VERSION_VRM1
        humanoid = ext.vrm1.humanoid
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})

        spine_bone = humanoid.human_bones.spine
        chest_bone = humanoid.human_bones.chest
        spine_bone.node.bone_name = "chest"
        chest_bone.node.bone_name = "spine"
        self.assertEqual(ops.vrm.model_validate(), {"CANCELLED"})
        spine_bone.node.bone_name = "spine"
        chest_bone.node.bone_name = "chest"
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})

        right_little_distal_bone = humanoid.human_bones.right_little_distal
        right_little_distal_bone.node.bone_name = "spine"
        self.assertEqual(ops.vrm.model_validate(), {"CANCELLED"})
        right_little_distal_bone.node.bone_name = "hips"
        self.assertEqual(ops.vrm.model_validate(), {"CANCELLED"})
        right_little_distal_bone.node.bone_name = "little_distal.L"
        self.assertEqual(ops.vrm.model_validate(), {"CANCELLED"})
        right_little_distal_bone.node.bone_name = ""
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})
        right_little_distal_bone.node.bone_name = "little_distal.R"
        self.assertEqual(ops.vrm.model_validate(), {"FINISHED"})


if __name__ == "__main__":
    main()
