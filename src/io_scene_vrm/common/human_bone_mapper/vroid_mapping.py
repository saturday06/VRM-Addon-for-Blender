# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import re
from collections.abc import Mapping
from typing import Final

from ..vrm1.human_bone import HumanBoneSpecification, HumanBoneSpecifications

LEFT__PATTERN: Final = re.compile("^J_(Adj|Bip|Opt|Sec)_L_")
RIGHT_PATTERN: Final = re.compile("^J_(Adj|Bip|Opt|Sec)_R_")
FULL__PATTERN: Final = re.compile("^J_(Adj|Bip|Opt|Sec)_([CLR]_)?")


def symmetrise_vroid_bone_name(bone_name: str) -> str:
    left = LEFT__PATTERN.sub("", bone_name)
    if left != bone_name:
        return left + "_L"

    right = RIGHT_PATTERN.sub("", bone_name)
    if right != bone_name:
        return right + "_R"

    return FULL__PATTERN.sub("", bone_name)


MAPPING: Final[Mapping[str, HumanBoneSpecification]] = {
    "J_Bip_C_Hips": HumanBoneSpecifications.HIPS,
    "J_Bip_C_Spine": HumanBoneSpecifications.SPINE,
    "J_Bip_C_Chest": HumanBoneSpecifications.CHEST,
    "J_Bip_C_UpperChest": HumanBoneSpecifications.UPPER_CHEST,
    "J_Bip_C_Neck": HumanBoneSpecifications.NECK,
    "J_Bip_C_Head": HumanBoneSpecifications.HEAD,
    "J_Adj_L_FaceEye": HumanBoneSpecifications.LEFT_EYE,
    "J_Adj_R_FaceEye": HumanBoneSpecifications.RIGHT_EYE,
    "J_Bip_L_UpperLeg": HumanBoneSpecifications.LEFT_UPPER_LEG,
    "J_Bip_L_LowerLeg": HumanBoneSpecifications.LEFT_LOWER_LEG,
    "J_Bip_L_Foot": HumanBoneSpecifications.LEFT_FOOT,
    "J_Bip_L_ToeBase": HumanBoneSpecifications.LEFT_TOES,
    "J_Bip_R_UpperLeg": HumanBoneSpecifications.RIGHT_UPPER_LEG,
    "J_Bip_R_LowerLeg": HumanBoneSpecifications.RIGHT_LOWER_LEG,
    "J_Bip_R_Foot": HumanBoneSpecifications.RIGHT_FOOT,
    "J_Bip_R_ToeBase": HumanBoneSpecifications.RIGHT_TOES,
    "J_Bip_L_Shoulder": HumanBoneSpecifications.LEFT_SHOULDER,
    "J_Bip_L_UpperArm": HumanBoneSpecifications.LEFT_UPPER_ARM,
    "J_Bip_L_LowerArm": HumanBoneSpecifications.LEFT_LOWER_ARM,
    "J_Bip_L_Hand": HumanBoneSpecifications.LEFT_HAND,
    "J_Bip_R_Shoulder": HumanBoneSpecifications.RIGHT_SHOULDER,
    "J_Bip_R_UpperArm": HumanBoneSpecifications.RIGHT_UPPER_ARM,
    "J_Bip_R_LowerArm": HumanBoneSpecifications.RIGHT_LOWER_ARM,
    "J_Bip_R_Hand": HumanBoneSpecifications.RIGHT_HAND,
    "J_Bip_L_Thumb1": HumanBoneSpecifications.LEFT_THUMB_METACARPAL,
    "J_Bip_L_Thumb2": HumanBoneSpecifications.LEFT_THUMB_PROXIMAL,
    "J_Bip_L_Thumb3": HumanBoneSpecifications.LEFT_THUMB_DISTAL,
    "J_Bip_L_Index1": HumanBoneSpecifications.LEFT_INDEX_PROXIMAL,
    "J_Bip_L_Index2": HumanBoneSpecifications.LEFT_INDEX_INTERMEDIATE,
    "J_Bip_L_Index3": HumanBoneSpecifications.LEFT_INDEX_DISTAL,
    "J_Bip_L_Middle1": HumanBoneSpecifications.LEFT_MIDDLE_PROXIMAL,
    "J_Bip_L_Middle2": HumanBoneSpecifications.LEFT_MIDDLE_INTERMEDIATE,
    "J_Bip_L_Middle3": HumanBoneSpecifications.LEFT_MIDDLE_DISTAL,
    "J_Bip_L_Ring1": HumanBoneSpecifications.LEFT_RING_PROXIMAL,
    "J_Bip_L_Ring2": HumanBoneSpecifications.LEFT_RING_INTERMEDIATE,
    "J_Bip_L_Ring3": HumanBoneSpecifications.LEFT_RING_DISTAL,
    "J_Bip_L_Little1": HumanBoneSpecifications.LEFT_LITTLE_PROXIMAL,
    "J_Bip_L_Little2": HumanBoneSpecifications.LEFT_LITTLE_INTERMEDIATE,
    "J_Bip_L_Little3": HumanBoneSpecifications.LEFT_LITTLE_DISTAL,
    "J_Bip_R_Thumb1": HumanBoneSpecifications.RIGHT_THUMB_METACARPAL,
    "J_Bip_R_Thumb2": HumanBoneSpecifications.RIGHT_THUMB_PROXIMAL,
    "J_Bip_R_Thumb3": HumanBoneSpecifications.RIGHT_THUMB_DISTAL,
    "J_Bip_R_Index1": HumanBoneSpecifications.RIGHT_INDEX_PROXIMAL,
    "J_Bip_R_Index2": HumanBoneSpecifications.RIGHT_INDEX_INTERMEDIATE,
    "J_Bip_R_Index3": HumanBoneSpecifications.RIGHT_INDEX_DISTAL,
    "J_Bip_R_Middle1": HumanBoneSpecifications.RIGHT_MIDDLE_PROXIMAL,
    "J_Bip_R_Middle2": HumanBoneSpecifications.RIGHT_MIDDLE_INTERMEDIATE,
    "J_Bip_R_Middle3": HumanBoneSpecifications.RIGHT_MIDDLE_DISTAL,
    "J_Bip_R_Ring1": HumanBoneSpecifications.RIGHT_RING_PROXIMAL,
    "J_Bip_R_Ring2": HumanBoneSpecifications.RIGHT_RING_INTERMEDIATE,
    "J_Bip_R_Ring3": HumanBoneSpecifications.RIGHT_RING_DISTAL,
    "J_Bip_R_Little1": HumanBoneSpecifications.RIGHT_LITTLE_PROXIMAL,
    "J_Bip_R_Little2": HumanBoneSpecifications.RIGHT_LITTLE_INTERMEDIATE,
    "J_Bip_R_Little3": HumanBoneSpecifications.RIGHT_LITTLE_DISTAL,
}


CONFIG: Final = ("VRoid", MAPPING)
CONFIG_SYMMETRICAL: Final = (
    "VRoid (Symmetrised)",
    {symmetrise_vroid_bone_name(k): v for k, v in MAPPING.items()},
)
