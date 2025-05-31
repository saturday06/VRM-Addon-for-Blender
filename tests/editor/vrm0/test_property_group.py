# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import TestCase, main

import bpy
from bpy.types import Armature

from io_scene_vrm.common import ops
from io_scene_vrm.common.debug import clean_scene
from io_scene_vrm.common.vrm0.human_bone import HumanBoneName
from io_scene_vrm.editor.extension import get_armature_extension
from io_scene_vrm.editor.vrm0.property_group import Vrm0HumanoidPropertyGroup


class TestVrm0HumanoidPropertyGroup(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        bpy.ops.preferences.addon_enable(module="io_scene_vrm")

    def setUp(self) -> None:
        clean_scene(bpy.context)

    def test_fixup_human_bones(self) -> None:
        context = bpy.context

        ops.icyp.make_basic_armature()
        armatures = [
            obj for obj in context.blend_data.objects if obj.type == "ARMATURE"
        ]
        self.assertEqual(len(armatures), 1)
        armature = armatures[0]
        if not isinstance(armature.data, Armature):
            raise TypeError

        human_bones = get_armature_extension(armature.data).vrm0.humanoid.human_bones

        original = [(str(b.node.bone_name), str(b.bone)) for b in human_bones]

        human_bone1 = human_bones.add()
        human_bone1.bone = "NoHumanBone"
        Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
        self.assertEqual(
            original, [(str(b.node.bone_name), str(b.bone)) for b in human_bones]
        )

        human_bone2 = human_bones.add()
        human_bone2.bone = HumanBoneName.CHEST.value
        Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
        self.assertEqual(
            original, [(str(b.node.bone_name), str(b.bone)) for b in human_bones]
        )

        human_bones.add()
        human_bones.add()
        human_bones.add()
        Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
        self.assertEqual(
            original, [(str(b.node.bone_name), str(b.bone)) for b in human_bones]
        )

        chest_bone = next(b for b in human_bones if b.bone == HumanBoneName.CHEST.value)
        spine_bone = next(b for b in human_bones if b.bone == HumanBoneName.SPINE.value)
        chest_bone.node.bone_name = HumanBoneName.SPINE.value
        self.assertEqual(spine_bone.node.bone_name, HumanBoneName.SPINE.value)
        self.assertEqual(chest_bone.node.bone_name, HumanBoneName.SPINE.value)
        Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
        self.assertEqual(spine_bone.node.bone_name, HumanBoneName.SPINE.value)
        self.assertTrue(not chest_bone.node.bone_name)
        chest_bone.node.bone_name = HumanBoneName.CHEST.value
        self.assertEqual(
            original, [(str(b.node.bone_name), str(b.bone)) for b in human_bones]
        )

        hips_index = next(
            i for i, b in enumerate(human_bones) if b.bone == HumanBoneName.HIPS.value
        )
        human_bones.remove(hips_index)
        Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
        hips_bone = next(b for b in human_bones if b.bone == HumanBoneName.HIPS.value)
        self.assertTrue(not hips_bone.node.bone_name)
        hips_bone.node.bone_name = "hips"
        self.assertEqual(
            set(original), {(str(b.node.bone_name), str(b.bone)) for b in human_bones}
        )


if __name__ == "__main__":
    main()
