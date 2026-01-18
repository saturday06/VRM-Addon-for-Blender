# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import difflib
from collections.abc import Mapping
from typing import Optional, Union

import bpy
from bpy.types import Armature, Context, EditBone, Object
from mathutils import Vector

from io_scene_vrm.common.human_bone_mapper.structure_based_mapping import (
    DEFAULT_MAX_SEARCH_COUNT,
    create_structure_based_mapping,
)
from io_scene_vrm.common.test_helper import AddonTestCase
from io_scene_vrm.common.vrm1.human_bone import (
    HumanBoneName,
    HumanBoneSpecification,
    HumanBoneSpecifications,
)

Tree = Mapping[
    tuple[
        Union[str, HumanBoneName, tuple[str, HumanBoneName]], tuple[float, float, float]
    ],
    "Tree",
]


def create_armature(
    context: Context, tree_root: Tree
) -> tuple[Object, Mapping[str, HumanBoneSpecification]]:
    bpy.ops.object.add(type="ARMATURE", enter_editmode=True, location=(0, 0, 0))
    armature_object = context.object
    if not armature_object:
        raise AssertionError
    armature_data = armature_object.data
    if not isinstance(armature_data, Armature):
        raise TypeError

    context.view_layer.objects.active = armature_object

    bpy.ops.object.mode_set(mode="EDIT")

    edit_bones = armature_data.edit_bones
    mapping: dict[str, HumanBoneSpecification] = {}

    parent_and_trees: list[tuple[Optional[EditBone], Tree]] = [(None, tree_root)]
    while parent_and_trees:
        (parent, tree) = parent_and_trees.pop()
        for (child_key, child_head), child_tree in tree.items():
            if isinstance(child_key, HumanBoneName):
                child_bone_name = "humanoid-" + child_key.value
                mapping[child_bone_name] = HumanBoneSpecifications.get(child_key)
            elif isinstance(child_key, str):
                child_bone_name = "x-" + child_key
            else:
                bone_name, human_bone_name = child_key
                child_bone_name = "x-" + bone_name
                mapping[child_bone_name] = HumanBoneSpecifications.get(human_bone_name)
            child = edit_bones.new(str(child_bone_name))
            child.head = Vector(child_head)
            child.tail = child.head + Vector((0, 0, 0.2))
            if parent:
                child.parent = parent
            parent_and_trees.append((child, child_tree))

    for bone in edit_bones:
        parent = bone.parent
        if bone.children:
            bone.tail = sum(
                (Vector(child.head) for child in bone.children), Vector((0, 0, 0))
            ) / len(bone.children)
        elif parent:
            direction = (bone.head - parent.head).normalized()
            bone.tail = bone.head + direction * 0.2

    bpy.ops.object.mode_set(mode="OBJECT")

    return armature_object, mapping


class TestStructureBasedMapper(AddonTestCase):
    def assert_tree(
        self,
        tree: Tree,
        _what: str,
        human_bone_name: HumanBoneName,
        max_search_count: int = DEFAULT_MAX_SEARCH_COUNT,
    ) -> None:
        context = bpy.context
        armature, expected_mapping = create_armature(context, tree)
        if not isinstance(armature_data := armature.data, Armature):
            raise TypeError

        # bpy.ops.wm.save_as_mainfile(
        #     filepath=str(
        #         Path(__file__).parent.parent.parent
        #         / "temp"
        #         / f"structure_based_mapper_{what}.blend"
        #     )
        # )

        root_bones = [bone for bone in armature_data.bones if bone.parent is None]
        if not root_bones:
            message = "No root bones found in armature."
            raise AssertionError(message)
        human_bone_specification = HumanBoneSpecifications.get(human_bone_name)
        actual_mapping = create_structure_based_mapping(
            armature, human_bone_specification, max_search_count=max_search_count
        )
        if expected_mapping == actual_mapping:
            return

        diff = difflib.unified_diff(
            [f"{k}: {v.name}\n" for k, v in sorted(expected_mapping.items())],
            [f"{k}: {v.name}\n" for k, v in sorted(actual_mapping.items())],
            fromfile="expected",
            tofile="actual",
            n=1,
        )
        message = "".join(diff)
        raise AssertionError("Mappings differ:\n" + message)

    def test_spine(self) -> None:
        tree: Tree = {
            (HumanBoneName.SPINE, (0, 0, 2)): {
                (HumanBoneName.HEAD, (0, 0, 4)): {},
                (HumanBoneName.LEFT_UPPER_ARM, (1, 0, 3)): {
                    (HumanBoneName.LEFT_LOWER_ARM, (2, 0, 3)): {
                        (HumanBoneName.LEFT_HAND, (3, 0, 3)): {}
                    }
                },
                (HumanBoneName.RIGHT_UPPER_ARM, (-1, 0, 3)): {
                    (HumanBoneName.RIGHT_LOWER_ARM, (-2, 0, 3)): {
                        (HumanBoneName.RIGHT_HAND, (-3, 0, 3)): {}
                    }
                },
            },
        }

        self.assert_tree(tree, "basic", HumanBoneName.SPINE)

    def test_simple(self) -> None:
        tree: Tree = {
            (HumanBoneName.HIPS, (0, 0, 1)): {
                (HumanBoneName.SPINE, (0, 0, 2)): {
                    (HumanBoneName.HEAD, (0, 0, 4)): {},
                    (HumanBoneName.LEFT_UPPER_ARM, (1, 0, 3)): {
                        (HumanBoneName.LEFT_LOWER_ARM, (2, 0, 3)): {
                            (HumanBoneName.LEFT_HAND, (3, 0, 3)): {}
                        }
                    },
                    (HumanBoneName.RIGHT_UPPER_ARM, (-1, 0, 3)): {
                        (HumanBoneName.RIGHT_LOWER_ARM, (-2, 0, 3)): {
                            (HumanBoneName.RIGHT_HAND, (-3, 0, 3)): {}
                        }
                    },
                },
                (HumanBoneName.LEFT_UPPER_LEG, (1, 0, 2)): {
                    (HumanBoneName.LEFT_LOWER_LEG, (1, 0, 1)): {
                        (HumanBoneName.LEFT_FOOT, (1, 0, 0)): {}
                    }
                },
                (HumanBoneName.RIGHT_UPPER_LEG, (-1, 0, 2)): {
                    (HumanBoneName.RIGHT_LOWER_LEG, (-1, 0, 1)): {
                        (HumanBoneName.RIGHT_FOOT, (-1, 0, 0)): {}
                    }
                },
            }
        }

        self.assert_tree(tree, "basic", HumanBoneName.HIPS)

    def test_leg_branch(self) -> None:
        tree: Tree = {
            ("root", (0, 0, 0)): {
                (HumanBoneName.HIPS, (0, 0, 1)): {
                    (HumanBoneName.SPINE, (0, 0, 2)): {
                        (HumanBoneName.CHEST, (0, 0, 3)): {
                            (HumanBoneName.HEAD, (0, 0, 4)): {},
                            (HumanBoneName.LEFT_UPPER_ARM, (1, 0, 3)): {
                                (HumanBoneName.LEFT_LOWER_ARM, (2, 0, 3)): {
                                    (HumanBoneName.LEFT_HAND, (3, 0, 3)): {}
                                }
                            },
                            (HumanBoneName.RIGHT_UPPER_ARM, (-1, 0, 3)): {
                                (HumanBoneName.RIGHT_LOWER_ARM, (-2, 0, 3)): {
                                    (HumanBoneName.RIGHT_HAND, (-3, 0, 3)): {}
                                }
                            },
                        },
                    },
                    ("leg-branch", (0, 0, 1.5)): {
                        (HumanBoneName.LEFT_UPPER_LEG, (1, 0, 2)): {
                            (HumanBoneName.LEFT_LOWER_LEG, (1, 0, 1)): {
                                (HumanBoneName.LEFT_FOOT, (1, 0, 0)): {}
                            }
                        },
                        (HumanBoneName.RIGHT_UPPER_LEG, (-1, 0, 2)): {
                            (HumanBoneName.RIGHT_LOWER_LEG, (-1, 0, 1)): {
                                (HumanBoneName.RIGHT_FOOT, (-1, 0, 0)): {}
                            }
                        },
                    },
                },
            },
        }

        self.assert_tree(tree, "leg-branch", HumanBoneName.HIPS)
