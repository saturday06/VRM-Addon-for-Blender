"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


# https://github.com/vrm-c/vrm-specification/blob/6a996eb151770149ea4534b1edb70d913bb4014e/specification/VRMC_vrm-1.0-beta/humanoid.md#list-of-humanoid-bones
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
    LEFT_THUMB_METACARPAL = "leftThumbMetacarpal"
    LEFT_THUMB_PROXIMAL = "leftThumbProximal"
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
    RIGHT_THUMB_METACARPAL = "rightThumbMetacarpal"
    RIGHT_THUMB_PROXIMAL = "rightThumbProximal"
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
        for human_bone_name in HumanBoneName:
            if human_bone_name.value == human_bone_name_str:
                return human_bone_name
        return None


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/humanoid.md#humanoid-bone-parent-child-relationship
HUMAN_BONE_STRUCTURE: Dict[
    HumanBoneName,
    Dict[
        HumanBoneName,
        Dict[
            HumanBoneName,
            Dict[
                HumanBoneName,
                Dict[
                    HumanBoneName,
                    Dict[
                        HumanBoneName,
                        Dict[
                            HumanBoneName,
                            Dict[
                                HumanBoneName,
                                Dict[
                                    HumanBoneName,
                                    Dict[
                                        HumanBoneName,
                                        Dict[
                                            HumanBoneName,
                                            Dict[HumanBoneName, None],
                                        ],
                                    ],
                                ],
                            ],
                        ],
                    ],
                ],
            ],
        ],
    ],
] = {
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
                                    HumanBoneName.LEFT_THUMB_METACARPAL: {
                                        HumanBoneName.LEFT_THUMB_PROXIMAL: {
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
                                    HumanBoneName.RIGHT_THUMB_METACARPAL: {
                                        HumanBoneName.RIGHT_THUMB_PROXIMAL: {
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
    title: str
    label: str
    label_no_left_right: str
    requirement: bool
    parent_requirement: bool
    parent_name: Optional[HumanBoneName]
    children_names: List[HumanBoneName]

    def parent(self) -> Optional["HumanBoneSpecification"]:
        if self.parent_name is None:
            return None
        return HumanBoneSpecifications.get(self.parent_name)

    def children(self) -> List["HumanBoneSpecification"]:
        return list(map(HumanBoneSpecifications.get, self.children_names))

    def connected(self) -> List["HumanBoneSpecification"]:
        children = self.children()
        parent = self.parent()
        if parent is None:
            return children
        return children + [parent]

    @staticmethod
    def create(
        human_bone_name: HumanBoneName, requirement: bool, parent_requirement: bool
    ) -> "HumanBoneSpecification":
        # https://stackoverflow.com/a/1176023
        words = re.sub(r"(?<!^)(?=[A-Z])", "#", human_bone_name.value).split("#")
        title = " ".join(map(str.capitalize, words))
        label = title + ":"
        label_no_left_right = re.sub(r"Right ", "", re.sub(r"^Left ", "", label))

        return HumanBoneSpecification(
            name=human_bone_name,
            title=title,
            label=label,
            label_no_left_right=label_no_left_right,
            requirement=requirement,
            parent_requirement=parent_requirement,
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
        human_bone_structure: Dict[HumanBoneName, Any],
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
        human_bone_structure: Dict[HumanBoneName, Dict[HumanBoneName, Any]],
    ) -> List[HumanBoneName]:
        for (
            next_human_bone_name,
            next_human_bone_structure,
        ) in human_bone_structure.items():
            if human_bone_name == next_human_bone_name:
                return list(next_human_bone_structure.keys())

            children = HumanBoneSpecification.find_children_human_bone_names(
                human_bone_name, next_human_bone_structure
            )
            if children:
                return children

        return []

    def is_ancestor_of(
        self, human_bone_specification: "HumanBoneSpecification"
    ) -> bool:
        parent = human_bone_specification.parent()
        while parent:
            if parent == self:
                return True
            parent = parent.parent()
        return False


def create_and_append_human_bone_specification(
    human_bone_specifications: List[HumanBoneSpecification],
    human_bone_name: HumanBoneName,
    requirement: bool,
    parent_requirement: bool,
) -> HumanBoneSpecification:
    human_bone_specification = HumanBoneSpecification.create(
        human_bone_name, requirement, parent_requirement
    )
    human_bone_specifications.append(human_bone_specification)
    return human_bone_specification


class HumanBoneSpecifications:
    all_human_bones: List[HumanBoneSpecification] = []

    # https://github.com/vrm-c/vrm-specification/blob/6a996eb151770149ea4534b1edb70d913bb4014e/specification/VRMC_vrm-1.0-beta/humanoid.md#list-of-humanoid-bones
    # Torso
    HIPS = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.HIPS, True, False
    )
    SPINE = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.SPINE, True, False
    )
    CHEST = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.CHEST, False, False
    )
    UPPER_CHEST = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.UPPER_CHEST, False, True
    )
    NECK = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.NECK, False, False
    )

    # Head
    HEAD = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.HEAD, True, False
    )
    LEFT_EYE = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_EYE, False, False
    )
    RIGHT_EYE = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_EYE, False, False
    )
    JAW = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.JAW, False, False
    )

    # Leg
    LEFT_UPPER_LEG = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_UPPER_LEG, True, False
    )
    LEFT_LOWER_LEG = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_LOWER_LEG, True, False
    )
    LEFT_FOOT = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_FOOT, True, False
    )
    LEFT_TOES = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_TOES, False, False
    )
    RIGHT_UPPER_LEG = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_UPPER_LEG, True, False
    )
    RIGHT_LOWER_LEG = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_LOWER_LEG, True, False
    )
    RIGHT_FOOT = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_FOOT, True, False
    )
    RIGHT_TOES = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_TOES, False, False
    )

    # Arm
    LEFT_SHOULDER = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_SHOULDER, False, False
    )
    LEFT_UPPER_ARM = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_UPPER_ARM, True, False
    )
    LEFT_LOWER_ARM = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_LOWER_ARM, True, False
    )
    LEFT_HAND = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_HAND, True, False
    )
    RIGHT_SHOULDER = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_SHOULDER, False, False
    )
    RIGHT_UPPER_ARM = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_UPPER_ARM, True, False
    )
    RIGHT_LOWER_ARM = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_LOWER_ARM, True, False
    )
    RIGHT_HAND = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_HAND, True, False
    )

    # Finger
    LEFT_THUMB_METACARPAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_THUMB_METACARPAL, False, False
    )
    LEFT_THUMB_PROXIMAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_THUMB_PROXIMAL, False, True
    )
    LEFT_THUMB_DISTAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_THUMB_DISTAL, False, True
    )
    LEFT_INDEX_PROXIMAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_INDEX_PROXIMAL, False, False
    )
    LEFT_INDEX_INTERMEDIATE = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_INDEX_INTERMEDIATE, False, True
    )
    LEFT_INDEX_DISTAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_INDEX_DISTAL, False, True
    )
    LEFT_MIDDLE_PROXIMAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_MIDDLE_PROXIMAL, False, False
    )
    LEFT_MIDDLE_INTERMEDIATE = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_MIDDLE_INTERMEDIATE, False, True
    )
    LEFT_MIDDLE_DISTAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_MIDDLE_DISTAL, False, True
    )
    LEFT_RING_PROXIMAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_RING_PROXIMAL, False, False
    )
    LEFT_RING_INTERMEDIATE = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_RING_INTERMEDIATE, False, True
    )
    LEFT_RING_DISTAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_RING_DISTAL, False, True
    )
    LEFT_LITTLE_PROXIMAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_LITTLE_PROXIMAL, False, False
    )
    LEFT_LITTLE_INTERMEDIATE = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_LITTLE_INTERMEDIATE, False, True
    )
    LEFT_LITTLE_DISTAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.LEFT_LITTLE_DISTAL, False, True
    )
    RIGHT_THUMB_METACARPAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_THUMB_METACARPAL, False, False
    )
    RIGHT_THUMB_PROXIMAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_THUMB_PROXIMAL, False, True
    )
    RIGHT_THUMB_DISTAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_THUMB_DISTAL, False, True
    )
    RIGHT_INDEX_PROXIMAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_INDEX_PROXIMAL, False, False
    )
    RIGHT_INDEX_INTERMEDIATE = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_INDEX_INTERMEDIATE, False, True
    )
    RIGHT_INDEX_DISTAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_INDEX_DISTAL, False, True
    )
    RIGHT_MIDDLE_PROXIMAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_MIDDLE_PROXIMAL, False, False
    )
    RIGHT_MIDDLE_INTERMEDIATE = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_MIDDLE_INTERMEDIATE, False, True
    )
    RIGHT_MIDDLE_DISTAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_MIDDLE_DISTAL, False, True
    )
    RIGHT_RING_PROXIMAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_RING_PROXIMAL, False, False
    )
    RIGHT_RING_INTERMEDIATE = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_RING_INTERMEDIATE, False, True
    )
    RIGHT_RING_DISTAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_RING_DISTAL, False, True
    )
    RIGHT_LITTLE_PROXIMAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_LITTLE_PROXIMAL, False, False
    )
    RIGHT_LITTLE_INTERMEDIATE = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_LITTLE_INTERMEDIATE, False, True
    )
    RIGHT_LITTLE_DISTAL = create_and_append_human_bone_specification(
        all_human_bones, HumanBoneName.RIGHT_LITTLE_DISTAL, False, True
    )

    human_bone_name_to_human_bone: Dict[HumanBoneName, HumanBoneSpecification] = {
        human_bone.name: human_bone for human_bone in all_human_bones
    }

    all_names: List[str] = [b.name.value for b in all_human_bones]

    @staticmethod
    def get(name: HumanBoneName) -> HumanBoneSpecification:
        return HumanBoneSpecifications.human_bone_name_to_human_bone[name]
