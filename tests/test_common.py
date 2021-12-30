from typing import Any, Dict, List
from unittest import TestCase

from io_scene_vrm.common import deep, human_bone
from io_scene_vrm.common.human_bone import HumanBoneName, HumanBones


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
            sorted(map(lambda b: b.name.value, HumanBones.all_human_bones)),
        )
        self.assertEqual(
            all_human_bone_names,
            sorted(human_bone.HumanBones.all_names),
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
        self.assertEqual(HumanBones.HIPS.parent_name, None)
        self.assertEqual(HumanBones.HIPS.parent(), None)

        self.assertEqual(HumanBones.RIGHT_TOES.parent_name, HumanBoneName.RIGHT_FOOT)
        self.assertEqual(HumanBones.RIGHT_TOES.parent(), HumanBones.RIGHT_FOOT)

        self.assertEqual(
            HumanBones.LEFT_SHOULDER.parent_name, HumanBoneName.UPPER_CHEST
        )
        self.assertEqual(HumanBones.LEFT_SHOULDER.parent(), HumanBones.UPPER_CHEST)

        self.assertEqual(HumanBones.NECK.parent_name, HumanBoneName.UPPER_CHEST)
        self.assertEqual(HumanBones.NECK.parent(), HumanBones.UPPER_CHEST)

    def test_children(self) -> None:
        self.assertEqual(
            HumanBones.HIPS.children_names,
            [
                HumanBoneName.SPINE,
                HumanBoneName.LEFT_UPPER_LEG,
                HumanBoneName.RIGHT_UPPER_LEG,
            ],
        )
        self.assertEqual(
            HumanBones.HIPS.children(),
            [HumanBones.SPINE, HumanBones.LEFT_UPPER_LEG, HumanBones.RIGHT_UPPER_LEG],
        )

        self.assertEqual(HumanBones.RIGHT_TOES.children_names, [])
        self.assertEqual(HumanBones.RIGHT_TOES.children(), [])

        self.assertEqual(
            HumanBones.LEFT_SHOULDER.children_names, [HumanBoneName.LEFT_UPPER_ARM]
        )
        self.assertEqual(
            HumanBones.LEFT_SHOULDER.children(), [HumanBones.LEFT_UPPER_ARM]
        )

        self.assertEqual(
            HumanBones.UPPER_CHEST.children_names,
            [
                HumanBoneName.NECK,
                HumanBoneName.LEFT_SHOULDER,
                HumanBoneName.RIGHT_SHOULDER,
            ],
        )
        self.assertEqual(
            HumanBones.UPPER_CHEST.children(),
            [
                HumanBones.NECK,
                HumanBones.LEFT_SHOULDER,
                HumanBones.RIGHT_SHOULDER,
            ],
        )
