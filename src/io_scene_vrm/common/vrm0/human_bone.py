# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
# SPDX-FileCopyrightText: 2018 iCyP

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from typing import ClassVar, Final, Optional


# https://github.com/vrm-c/vrm-specification/tree/b5793b4ca250ed3acbde3dd7a47ee9ee1b3d60e9/specification/0.0#vrm-extension-models-bone-mapping-jsonextensionsvrmhumanoid
class HumanBoneName(Enum):
    # Torso
    HIPS = "hips"
    SPINE = "spine"
    CHEST = "chest"
    UPPER_CHEST = "upperChest"
    NECK = "neck"

    # Head
    HEAD = "head"
    LEFT_EYE = "leftEye"
    RIGHT_EYE = "rightEye"
    JAW = "jaw"

    # Leg
    LEFT_UPPER_LEG = "leftUpperLeg"
    LEFT_LOWER_LEG = "leftLowerLeg"
    LEFT_FOOT = "leftFoot"
    LEFT_TOES = "leftToes"
    RIGHT_UPPER_LEG = "rightUpperLeg"
    RIGHT_LOWER_LEG = "rightLowerLeg"
    RIGHT_FOOT = "rightFoot"
    RIGHT_TOES = "rightToes"

    # Arm
    LEFT_SHOULDER = "leftShoulder"
    LEFT_UPPER_ARM = "leftUpperArm"
    LEFT_LOWER_ARM = "leftLowerArm"
    LEFT_HAND = "leftHand"
    RIGHT_SHOULDER = "rightShoulder"
    RIGHT_UPPER_ARM = "rightUpperArm"
    RIGHT_LOWER_ARM = "rightLowerArm"
    RIGHT_HAND = "rightHand"

    # Finger
    LEFT_THUMB_PROXIMAL = "leftThumbProximal"
    LEFT_THUMB_INTERMEDIATE = "leftThumbIntermediate"
    LEFT_THUMB_DISTAL = "leftThumbDistal"
    LEFT_INDEX_PROXIMAL = "leftIndexProximal"
    LEFT_INDEX_INTERMEDIATE = "leftIndexIntermediate"
    LEFT_INDEX_DISTAL = "leftIndexDistal"
    LEFT_MIDDLE_PROXIMAL = "leftMiddleProximal"
    LEFT_MIDDLE_INTERMEDIATE = "leftMiddleIntermediate"
    LEFT_MIDDLE_DISTAL = "leftMiddleDistal"
    LEFT_RING_PROXIMAL = "leftRingProximal"
    LEFT_RING_INTERMEDIATE = "leftRingIntermediate"
    LEFT_RING_DISTAL = "leftRingDistal"
    LEFT_LITTLE_PROXIMAL = "leftLittleProximal"
    LEFT_LITTLE_INTERMEDIATE = "leftLittleIntermediate"
    LEFT_LITTLE_DISTAL = "leftLittleDistal"
    RIGHT_THUMB_PROXIMAL = "rightThumbProximal"
    RIGHT_THUMB_INTERMEDIATE = "rightThumbIntermediate"
    RIGHT_THUMB_DISTAL = "rightThumbDistal"
    RIGHT_INDEX_PROXIMAL = "rightIndexProximal"
    RIGHT_INDEX_INTERMEDIATE = "rightIndexIntermediate"
    RIGHT_INDEX_DISTAL = "rightIndexDistal"
    RIGHT_MIDDLE_PROXIMAL = "rightMiddleProximal"
    RIGHT_MIDDLE_INTERMEDIATE = "rightMiddleIntermediate"
    RIGHT_MIDDLE_DISTAL = "rightMiddleDistal"
    RIGHT_RING_PROXIMAL = "rightRingProximal"
    RIGHT_RING_INTERMEDIATE = "rightRingIntermediate"
    RIGHT_RING_DISTAL = "rightRingDistal"
    RIGHT_LITTLE_PROXIMAL = "rightLittleProximal"
    RIGHT_LITTLE_INTERMEDIATE = "rightLittleIntermediate"
    RIGHT_LITTLE_DISTAL = "rightLittleDistal"

    @staticmethod
    def from_str(human_bone_name_str: str) -> Optional["HumanBoneName"]:
        try:
            return HumanBoneName(human_bone_name_str)
        except ValueError:
            return None


# https://github.com/vrm-c/vrm.dev/blob/cd1d367417c53ba0f1d46588180c17b5e2768e22/docs/univrm/humanoid/humanoid_overview.md?plain=1#L99-L106
HumanBoneStructure = Mapping[HumanBoneName, "HumanBoneStructure"]
HUMAN_BONE_STRUCTURE: Final[HumanBoneStructure] = {
    HumanBoneName.HIPS: {
        HumanBoneName.SPINE: {
            HumanBoneName.CHEST: {
                HumanBoneName.UPPER_CHEST: {
                    HumanBoneName.NECK: {
                        HumanBoneName.HEAD: {
                            HumanBoneName.LEFT_EYE: {},
                            HumanBoneName.RIGHT_EYE: {},
                            HumanBoneName.JAW: {},
                        }
                    },
                    HumanBoneName.LEFT_SHOULDER: {
                        HumanBoneName.LEFT_UPPER_ARM: {
                            HumanBoneName.LEFT_LOWER_ARM: {
                                HumanBoneName.LEFT_HAND: {
                                    HumanBoneName.LEFT_THUMB_PROXIMAL: {
                                        HumanBoneName.LEFT_THUMB_INTERMEDIATE: {
                                            HumanBoneName.LEFT_THUMB_DISTAL: {}
                                        }
                                    },
                                    HumanBoneName.LEFT_INDEX_PROXIMAL: {
                                        HumanBoneName.LEFT_INDEX_INTERMEDIATE: {
                                            HumanBoneName.LEFT_INDEX_DISTAL: {}
                                        }
                                    },
                                    HumanBoneName.LEFT_MIDDLE_PROXIMAL: {
                                        HumanBoneName.LEFT_MIDDLE_INTERMEDIATE: {
                                            HumanBoneName.LEFT_MIDDLE_DISTAL: {}
                                        }
                                    },
                                    HumanBoneName.LEFT_RING_PROXIMAL: {
                                        HumanBoneName.LEFT_RING_INTERMEDIATE: {
                                            HumanBoneName.LEFT_RING_DISTAL: {}
                                        }
                                    },
                                    HumanBoneName.LEFT_LITTLE_PROXIMAL: {
                                        HumanBoneName.LEFT_LITTLE_INTERMEDIATE: {
                                            HumanBoneName.LEFT_LITTLE_DISTAL: {}
                                        }
                                    },
                                }
                            }
                        }
                    },
                    HumanBoneName.RIGHT_SHOULDER: {
                        HumanBoneName.RIGHT_UPPER_ARM: {
                            HumanBoneName.RIGHT_LOWER_ARM: {
                                HumanBoneName.RIGHT_HAND: {
                                    HumanBoneName.RIGHT_THUMB_PROXIMAL: {
                                        HumanBoneName.RIGHT_THUMB_INTERMEDIATE: {
                                            HumanBoneName.RIGHT_THUMB_DISTAL: {}
                                        }
                                    },
                                    HumanBoneName.RIGHT_INDEX_PROXIMAL: {
                                        HumanBoneName.RIGHT_INDEX_INTERMEDIATE: {
                                            HumanBoneName.RIGHT_INDEX_DISTAL: {}
                                        }
                                    },
                                    HumanBoneName.RIGHT_MIDDLE_PROXIMAL: {
                                        HumanBoneName.RIGHT_MIDDLE_INTERMEDIATE: {
                                            HumanBoneName.RIGHT_MIDDLE_DISTAL: {}
                                        }
                                    },
                                    HumanBoneName.RIGHT_RING_PROXIMAL: {
                                        HumanBoneName.RIGHT_RING_INTERMEDIATE: {
                                            HumanBoneName.RIGHT_RING_DISTAL: {}
                                        }
                                    },
                                    HumanBoneName.RIGHT_LITTLE_PROXIMAL: {
                                        HumanBoneName.RIGHT_LITTLE_INTERMEDIATE: {
                                            HumanBoneName.RIGHT_LITTLE_DISTAL: {}
                                        }
                                    },
                                }
                            }
                        }
                    },
                }
            }
        },
        HumanBoneName.LEFT_UPPER_LEG: {
            HumanBoneName.LEFT_LOWER_LEG: {
                HumanBoneName.LEFT_FOOT: {HumanBoneName.LEFT_TOES: {}}
            }
        },
        HumanBoneName.RIGHT_UPPER_LEG: {
            HumanBoneName.RIGHT_LOWER_LEG: {
                HumanBoneName.RIGHT_FOOT: {HumanBoneName.RIGHT_TOES: {}}
            }
        },
    }
}


@dataclass(frozen=True)
class HumanBoneSpecification:
    name: HumanBoneName
    icon: str
    title: str
    label: str
    label_no_left_right: str
    requirement: bool
    parent_name: Optional[HumanBoneName]
    children_names: tuple[HumanBoneName, ...]

    @cached_property
    def parent(self) -> Optional["HumanBoneSpecification"]:
        if self.parent_name is None:
            return None
        return HumanBoneSpecifications.get(self.parent_name)

    @cached_property
    def children(self) -> tuple["HumanBoneSpecification", ...]:
        return tuple(map(HumanBoneSpecifications.get, self.children_names))

    @cached_property
    def descendants(self) -> tuple["HumanBoneSpecification", ...]:
        result: list[HumanBoneSpecification] = []
        searching_children = list(self.children)
        while searching_children:
            child = searching_children.pop()
            result.append(child)
            searching_children.extend(child.children)
        return tuple(result)

    @staticmethod
    def create(
        human_bone_name: HumanBoneName, *, requirement: bool, icon: str
    ) -> "HumanBoneSpecification":
        # https://stackoverflow.com/a/1176023
        words = re.sub(r"(?<!^)(?=[A-Z])", "#", human_bone_name.value).split("#")
        title = " ".join(word.capitalize() for word in words)
        label = title + ":"
        label_no_left_right = re.sub(r"Right ", "", re.sub(r"^Left ", "", label))

        return HumanBoneSpecification(
            name=human_bone_name,
            icon=icon,
            title=title,
            label=label,
            label_no_left_right=label_no_left_right,
            requirement=requirement,
            parent_name=HumanBoneSpecification.find_parent_human_bone_name(
                human_bone_name, None, HUMAN_BONE_STRUCTURE
            ),
            children_names=HumanBoneSpecification.find_children_human_bone_names(
                human_bone_name, HUMAN_BONE_STRUCTURE
            ),
        )

    @staticmethod
    def find_parent_human_bone_name(
        child_human_bone_name: HumanBoneName,
        parent_human_bone_name: Optional[HumanBoneName],
        human_bone_structure: HumanBoneStructure,
    ) -> Optional[HumanBoneName]:
        for (
            next_human_bone_name,
            next_human_bone_structure,
        ) in human_bone_structure.items():
            if child_human_bone_name == next_human_bone_name:
                return parent_human_bone_name

            name = HumanBoneSpecification.find_parent_human_bone_name(
                child_human_bone_name, next_human_bone_name, next_human_bone_structure
            )
            if name:
                return name

        return None

    @staticmethod
    def find_children_human_bone_names(
        human_bone_name: HumanBoneName,
        human_bone_structure: HumanBoneStructure,
    ) -> tuple[HumanBoneName, ...]:
        for (
            next_human_bone_name,
            next_human_bone_structure,
        ) in human_bone_structure.items():
            if human_bone_name == next_human_bone_name:
                return tuple(next_human_bone_structure.keys())

            children = HumanBoneSpecification.find_children_human_bone_names(
                human_bone_name, next_human_bone_structure
            )
            if children:
                return children

        return ()

    def is_ancestor_of(
        self, human_bone_specification: "HumanBoneSpecification"
    ) -> bool:
        parent = human_bone_specification.parent
        while parent:
            if parent == self:
                return True
            parent = parent.parent
        return False


def _create_and_append_human_bone_specification(
    human_bone_specifications: list[HumanBoneSpecification],
    human_bone_name: HumanBoneName,
    *,
    requirement: bool,
    icon: str,
) -> HumanBoneSpecification:
    human_bone_specification = HumanBoneSpecification.create(
        human_bone_name, requirement=requirement, icon=icon
    )
    human_bone_specifications.append(human_bone_specification)
    return human_bone_specification


class HumanBoneSpecifications:
    all_human_bones: ClassVar[list[HumanBoneSpecification]] = []

    # https://github.com/vrm-c/vrm-specification/tree/b5793b4ca250ed3acbde3dd7a47ee9ee1b3d60e9/specification/0.0#vrm-extension-models-bone-mapping-jsonextensionsvrmhumanoid
    # Torso
    HIPS = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.HIPS,
        requirement=True,
        icon="USER",
    )
    SPINE = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.SPINE,
        requirement=True,
        icon="USER",
    )
    CHEST = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.CHEST,
        requirement=True,
        icon="USER",
    )
    UPPER_CHEST = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.UPPER_CHEST,
        requirement=False,
        icon="USER",
    )
    NECK = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.NECK,
        requirement=True,
        icon="USER",
    )

    # Head
    HEAD = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.HEAD,
        requirement=True,
        icon="USER",
    )
    LEFT_EYE = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_EYE,
        requirement=False,
        icon="HIDE_OFF",
    )
    RIGHT_EYE = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_EYE,
        requirement=False,
        icon="HIDE_OFF",
    )
    JAW = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.JAW,
        requirement=False,
        icon="USER",
    )

    # Leg
    LEFT_UPPER_LEG = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_UPPER_LEG,
        requirement=True,
        icon="MOD_DYNAMICPAINT",
    )
    LEFT_LOWER_LEG = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_LOWER_LEG,
        requirement=True,
        icon="MOD_DYNAMICPAINT",
    )
    LEFT_FOOT = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_FOOT,
        requirement=True,
        icon="MOD_DYNAMICPAINT",
    )
    LEFT_TOES = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_TOES,
        requirement=False,
        icon="MOD_DYNAMICPAINT",
    )
    RIGHT_UPPER_LEG = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_UPPER_LEG,
        requirement=True,
        icon="MOD_DYNAMICPAINT",
    )
    RIGHT_LOWER_LEG = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_LOWER_LEG,
        requirement=True,
        icon="MOD_DYNAMICPAINT",
    )
    RIGHT_FOOT = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_FOOT,
        requirement=True,
        icon="MOD_DYNAMICPAINT",
    )
    RIGHT_TOES = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_TOES,
        requirement=False,
        icon="MOD_DYNAMICPAINT",
    )

    # Arm
    LEFT_SHOULDER = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_SHOULDER,
        requirement=False,
        icon="VIEW_PAN",
    )
    LEFT_UPPER_ARM = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_UPPER_ARM,
        requirement=True,
        icon="VIEW_PAN",
    )
    LEFT_LOWER_ARM = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_LOWER_ARM,
        requirement=True,
        icon="VIEW_PAN",
    )
    LEFT_HAND = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_HAND,
        requirement=True,
        icon="VIEW_PAN",
    )
    RIGHT_SHOULDER = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_SHOULDER,
        requirement=False,
        icon="VIEW_PAN",
    )
    RIGHT_UPPER_ARM = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_UPPER_ARM,
        requirement=True,
        icon="VIEW_PAN",
    )
    RIGHT_LOWER_ARM = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_LOWER_ARM,
        requirement=True,
        icon="VIEW_PAN",
    )
    RIGHT_HAND = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_HAND,
        requirement=True,
        icon="VIEW_PAN",
    )

    # Finger
    LEFT_THUMB_PROXIMAL = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_THUMB_PROXIMAL,
        requirement=False,
        icon="VIEW_PAN",
    )
    LEFT_THUMB_INTERMEDIATE = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_THUMB_INTERMEDIATE,
        requirement=False,
        icon="VIEW_PAN",
    )
    LEFT_THUMB_DISTAL = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_THUMB_DISTAL,
        requirement=False,
        icon="VIEW_PAN",
    )
    LEFT_INDEX_PROXIMAL = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_INDEX_PROXIMAL,
        requirement=False,
        icon="VIEW_PAN",
    )
    LEFT_INDEX_INTERMEDIATE = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_INDEX_INTERMEDIATE,
        requirement=False,
        icon="VIEW_PAN",
    )
    LEFT_INDEX_DISTAL = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_INDEX_DISTAL,
        requirement=False,
        icon="VIEW_PAN",
    )
    LEFT_MIDDLE_PROXIMAL = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_MIDDLE_PROXIMAL,
        requirement=False,
        icon="VIEW_PAN",
    )
    LEFT_MIDDLE_INTERMEDIATE = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_MIDDLE_INTERMEDIATE,
        requirement=False,
        icon="VIEW_PAN",
    )
    LEFT_MIDDLE_DISTAL = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_MIDDLE_DISTAL,
        requirement=False,
        icon="VIEW_PAN",
    )
    LEFT_RING_PROXIMAL = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_RING_PROXIMAL,
        requirement=False,
        icon="VIEW_PAN",
    )
    LEFT_RING_INTERMEDIATE = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_RING_INTERMEDIATE,
        requirement=False,
        icon="VIEW_PAN",
    )
    LEFT_RING_DISTAL = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_RING_DISTAL,
        requirement=False,
        icon="VIEW_PAN",
    )
    LEFT_LITTLE_PROXIMAL = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_LITTLE_PROXIMAL,
        requirement=False,
        icon="VIEW_PAN",
    )
    LEFT_LITTLE_INTERMEDIATE = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_LITTLE_INTERMEDIATE,
        requirement=False,
        icon="VIEW_PAN",
    )
    LEFT_LITTLE_DISTAL = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.LEFT_LITTLE_DISTAL,
        requirement=False,
        icon="VIEW_PAN",
    )
    RIGHT_THUMB_PROXIMAL = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_THUMB_PROXIMAL,
        requirement=False,
        icon="VIEW_PAN",
    )
    RIGHT_THUMB_INTERMEDIATE = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_THUMB_INTERMEDIATE,
        requirement=False,
        icon="VIEW_PAN",
    )
    RIGHT_THUMB_DISTAL = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_THUMB_DISTAL,
        requirement=False,
        icon="VIEW_PAN",
    )
    RIGHT_INDEX_PROXIMAL = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_INDEX_PROXIMAL,
        requirement=False,
        icon="VIEW_PAN",
    )
    RIGHT_INDEX_INTERMEDIATE = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_INDEX_INTERMEDIATE,
        requirement=False,
        icon="VIEW_PAN",
    )
    RIGHT_INDEX_DISTAL = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_INDEX_DISTAL,
        requirement=False,
        icon="VIEW_PAN",
    )
    RIGHT_MIDDLE_PROXIMAL = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_MIDDLE_PROXIMAL,
        requirement=False,
        icon="VIEW_PAN",
    )
    RIGHT_MIDDLE_INTERMEDIATE = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_MIDDLE_INTERMEDIATE,
        requirement=False,
        icon="VIEW_PAN",
    )
    RIGHT_MIDDLE_DISTAL = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_MIDDLE_DISTAL,
        requirement=False,
        icon="VIEW_PAN",
    )
    RIGHT_RING_PROXIMAL = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_RING_PROXIMAL,
        requirement=False,
        icon="VIEW_PAN",
    )
    RIGHT_RING_INTERMEDIATE = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_RING_INTERMEDIATE,
        requirement=False,
        icon="VIEW_PAN",
    )
    RIGHT_RING_DISTAL = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_RING_DISTAL,
        requirement=False,
        icon="VIEW_PAN",
    )
    RIGHT_LITTLE_PROXIMAL = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_LITTLE_PROXIMAL,
        requirement=False,
        icon="VIEW_PAN",
    )
    RIGHT_LITTLE_INTERMEDIATE = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_LITTLE_INTERMEDIATE,
        requirement=False,
        icon="VIEW_PAN",
    )
    RIGHT_LITTLE_DISTAL = _create_and_append_human_bone_specification(
        all_human_bones,
        HumanBoneName.RIGHT_LITTLE_DISTAL,
        requirement=False,
        icon="VIEW_PAN",
    )

    human_bone_name_to_human_bone: Mapping[HumanBoneName, HumanBoneSpecification] = {
        human_bone.name: human_bone for human_bone in all_human_bones
    }

    all_names = tuple(b.name.value for b in all_human_bones)

    required_names = tuple(b.name.value for b in all_human_bones if b.requirement)

    optional_names = tuple(b.name.value for b in all_human_bones if not b.requirement)

    @staticmethod
    def get(name: HumanBoneName) -> HumanBoneSpecification:
        return HumanBoneSpecifications.human_bone_name_to_human_bone[name]
