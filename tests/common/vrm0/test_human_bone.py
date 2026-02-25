# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from unittest import TestCase

from io_scene_vrm.common.vrm0 import human_bone as vrm0_human_bone


class TestVrm0HumanBone(TestCase):
    def test_all(self) -> None:
        all_human_bone_names = sorted(n.value for n in vrm0_human_bone.HumanBoneName)
        self.assertEqual(
            all_human_bone_names,
            sorted(
                b.name.value
                for b in vrm0_human_bone.HumanBoneSpecifications.all_human_bones
            ),
        )
        self.assertEqual(
            all_human_bone_names,
            sorted(vrm0_human_bone.HumanBoneSpecifications.all_names),
        )

        structure_human_bone_names: list[str] = []
        children: list[vrm0_human_bone.HumanBoneStructure] = [
            vrm0_human_bone.HUMAN_BONE_STRUCTURE
        ]
        while children:
            current = children.pop()
            for human_bone_name, child in current.items():
                children.append(child)
                structure_human_bone_names.append(human_bone_name.value)

        self.assertEqual(all_human_bone_names, sorted(structure_human_bone_names))

    def test_parent(self) -> None:
        self.assertEqual(vrm0_human_bone.HumanBoneSpecifications.HIPS.parent_name, None)
        self.assertEqual(vrm0_human_bone.HumanBoneSpecifications.HIPS.parent, None)

        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.RIGHT_TOES.parent_name,
            vrm0_human_bone.HumanBoneName.RIGHT_FOOT,
        )
        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.RIGHT_TOES.parent,
            vrm0_human_bone.HumanBoneSpecifications.RIGHT_FOOT,
        )

        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.LEFT_SHOULDER.parent_name,
            vrm0_human_bone.HumanBoneName.UPPER_CHEST,
        )
        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.LEFT_SHOULDER.parent,
            vrm0_human_bone.HumanBoneSpecifications.UPPER_CHEST,
        )

        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.NECK.parent_name,
            vrm0_human_bone.HumanBoneName.UPPER_CHEST,
        )
        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.NECK.parent,
            vrm0_human_bone.HumanBoneSpecifications.UPPER_CHEST,
        )

    def test_children(self) -> None:
        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.HIPS.children_names,
            (
                vrm0_human_bone.HumanBoneName.SPINE,
                vrm0_human_bone.HumanBoneName.LEFT_UPPER_LEG,
                vrm0_human_bone.HumanBoneName.RIGHT_UPPER_LEG,
            ),
        )
        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.HIPS.children,
            (
                vrm0_human_bone.HumanBoneSpecifications.SPINE,
                vrm0_human_bone.HumanBoneSpecifications.LEFT_UPPER_LEG,
                vrm0_human_bone.HumanBoneSpecifications.RIGHT_UPPER_LEG,
            ),
        )

        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.RIGHT_TOES.children_names, ()
        )
        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.RIGHT_TOES.children, ()
        )

        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.LEFT_SHOULDER.children_names,
            (vrm0_human_bone.HumanBoneName.LEFT_UPPER_ARM,),
        )
        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.LEFT_SHOULDER.children,
            (vrm0_human_bone.HumanBoneSpecifications.LEFT_UPPER_ARM,),
        )

        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.UPPER_CHEST.children_names,
            (
                vrm0_human_bone.HumanBoneName.NECK,
                vrm0_human_bone.HumanBoneName.LEFT_SHOULDER,
                vrm0_human_bone.HumanBoneName.RIGHT_SHOULDER,
            ),
        )
        self.assertEqual(
            vrm0_human_bone.HumanBoneSpecifications.UPPER_CHEST.children,
            (
                vrm0_human_bone.HumanBoneSpecifications.NECK,
                vrm0_human_bone.HumanBoneSpecifications.LEFT_SHOULDER,
                vrm0_human_bone.HumanBoneSpecifications.RIGHT_SHOULDER,
            ),
        )
