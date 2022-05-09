from typing import Any, Dict, List
from unittest import TestCase

from io_scene_vrm.common import deep, human_bone
from io_scene_vrm.common.human_bone import HumanBoneName, HumanBoneSpecifications


class TestDeep(TestCase):
    def test_nested_json_value_getter(self) -> None:
        self.assertEqual(
            123,
            deep.get({"foo": [{"bar": 123}]}, ["foo", 0, "bar"]),
        )


class TestHumanBone(TestCase):
    def test_all(self) -> None:
        all_human_bone_names = sorted(map(lambda n: n.value, HumanBoneName))
        self.assertEqual(
            all_human_bone_names,
            sorted(
                map(lambda b: b.name.value, HumanBoneSpecifications.all_human_bones)
            ),
        )
        self.assertEqual(
            all_human_bone_names,
            sorted(human_bone.HumanBoneSpecifications.all_names),
        )

        structure_human_bone_names = []
        children: List[Dict[HumanBoneName, Any]] = [human_bone.HUMAN_BONE_STRUCTURE]
        while children:
            current = children.pop()
            for human_bone_name, child in current.items():
                children.append(child)
                structure_human_bone_names.append(human_bone_name.value)

        self.assertEqual(all_human_bone_names, sorted(structure_human_bone_names))

    def test_parent(self) -> None:
        self.assertEqual(HumanBoneSpecifications.HIPS.parent_name, None)
        self.assertEqual(HumanBoneSpecifications.HIPS.parent(), None)

        self.assertEqual(
            HumanBoneSpecifications.RIGHT_TOES.parent_name, HumanBoneName.RIGHT_FOOT
        )
        self.assertEqual(
            HumanBoneSpecifications.RIGHT_TOES.parent(),
            HumanBoneSpecifications.RIGHT_FOOT,
        )

        self.assertEqual(
            HumanBoneSpecifications.LEFT_SHOULDER.parent_name, HumanBoneName.UPPER_CHEST
        )
        self.assertEqual(
            HumanBoneSpecifications.LEFT_SHOULDER.parent(),
            HumanBoneSpecifications.UPPER_CHEST,
        )

        self.assertEqual(
            HumanBoneSpecifications.NECK.parent_name, HumanBoneName.UPPER_CHEST
        )
        self.assertEqual(
            HumanBoneSpecifications.NECK.parent(), HumanBoneSpecifications.UPPER_CHEST
        )

    def test_children(self) -> None:
        self.assertEqual(
            HumanBoneSpecifications.HIPS.children_names,
            [
                HumanBoneName.SPINE,
                HumanBoneName.LEFT_UPPER_LEG,
                HumanBoneName.RIGHT_UPPER_LEG,
            ],
        )
        self.assertEqual(
            HumanBoneSpecifications.HIPS.children(),
            [
                HumanBoneSpecifications.SPINE,
                HumanBoneSpecifications.LEFT_UPPER_LEG,
                HumanBoneSpecifications.RIGHT_UPPER_LEG,
            ],
        )

        self.assertEqual(HumanBoneSpecifications.RIGHT_TOES.children_names, [])
        self.assertEqual(HumanBoneSpecifications.RIGHT_TOES.children(), [])

        self.assertEqual(
            HumanBoneSpecifications.LEFT_SHOULDER.children_names,
            [HumanBoneName.LEFT_UPPER_ARM],
        )
        self.assertEqual(
            HumanBoneSpecifications.LEFT_SHOULDER.children(),
            [HumanBoneSpecifications.LEFT_UPPER_ARM],
        )

        self.assertEqual(
            HumanBoneSpecifications.UPPER_CHEST.children_names,
            [
                HumanBoneName.NECK,
                HumanBoneName.LEFT_SHOULDER,
                HumanBoneName.RIGHT_SHOULDER,
            ],
        )
        self.assertEqual(
            HumanBoneSpecifications.UPPER_CHEST.children(),
            [
                HumanBoneSpecifications.NECK,
                HumanBoneSpecifications.LEFT_SHOULDER,
                HumanBoneSpecifications.RIGHT_SHOULDER,
            ],
        )
