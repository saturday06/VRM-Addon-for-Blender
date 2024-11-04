# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from ..vrm1.human_bone import HumanBoneSpecification, HumanBoneSpecifications

mapping_template: dict[str, HumanBoneSpecification] = {
    "Head": HumanBoneSpecifications.HEAD,
    "REye": HumanBoneSpecifications.RIGHT_EYE,
    "LEye": HumanBoneSpecifications.LEFT_EYE,
    "MJaw": HumanBoneSpecifications.JAW,
    "Spine2": HumanBoneSpecifications.CHEST,
    "Spine1": HumanBoneSpecifications.SPINE,
    "Pelvis": HumanBoneSpecifications.HIPS,
    "R Clavicle": HumanBoneSpecifications.RIGHT_SHOULDER,
    "R UpperArm": HumanBoneSpecifications.RIGHT_UPPER_ARM,
    "R Forearm": HumanBoneSpecifications.RIGHT_LOWER_ARM,
    "R Hand": HumanBoneSpecifications.RIGHT_HAND,
    "L Clavicle": HumanBoneSpecifications.LEFT_SHOULDER,
    "L UpperArm": HumanBoneSpecifications.LEFT_UPPER_ARM,
    "L Forearm": HumanBoneSpecifications.LEFT_LOWER_ARM,
    "L Hand": HumanBoneSpecifications.LEFT_HAND,
    "R Thigh": HumanBoneSpecifications.RIGHT_UPPER_LEG,
    "R Calf": HumanBoneSpecifications.RIGHT_LOWER_LEG,
    "R Foot": HumanBoneSpecifications.RIGHT_FOOT,
    "R Toe0": HumanBoneSpecifications.RIGHT_TOES,
    "L Thigh": HumanBoneSpecifications.LEFT_UPPER_LEG,
    "L Calf": HumanBoneSpecifications.LEFT_LOWER_LEG,
    "L Foot": HumanBoneSpecifications.LEFT_FOOT,
    "L Toe0": HumanBoneSpecifications.LEFT_TOES,
    "R Finger0": HumanBoneSpecifications.RIGHT_THUMB_METACARPAL,
    "R Finger01": HumanBoneSpecifications.RIGHT_THUMB_PROXIMAL,
    "R Finger02": HumanBoneSpecifications.RIGHT_THUMB_DISTAL,
    "R Finger1": HumanBoneSpecifications.RIGHT_INDEX_PROXIMAL,
    "R Finger11": HumanBoneSpecifications.RIGHT_INDEX_INTERMEDIATE,
    "R Finger12": HumanBoneSpecifications.RIGHT_INDEX_DISTAL,
    "R Finger2": HumanBoneSpecifications.RIGHT_MIDDLE_PROXIMAL,
    "R Finger21": HumanBoneSpecifications.RIGHT_MIDDLE_INTERMEDIATE,
    "R Finger22": HumanBoneSpecifications.RIGHT_MIDDLE_DISTAL,
    "R Finger3": HumanBoneSpecifications.RIGHT_RING_PROXIMAL,
    "R Finger31": HumanBoneSpecifications.RIGHT_RING_INTERMEDIATE,
    "R Finger32": HumanBoneSpecifications.RIGHT_RING_DISTAL,
    "R Finger4": HumanBoneSpecifications.RIGHT_LITTLE_PROXIMAL,
    "R Finger41": HumanBoneSpecifications.RIGHT_LITTLE_INTERMEDIATE,
    "R Finger42": HumanBoneSpecifications.RIGHT_LITTLE_DISTAL,
    "L Finger0": HumanBoneSpecifications.LEFT_THUMB_METACARPAL,
    "L Finger01": HumanBoneSpecifications.LEFT_THUMB_PROXIMAL,
    "L Finger02": HumanBoneSpecifications.LEFT_THUMB_DISTAL,
    "L Finger1": HumanBoneSpecifications.LEFT_INDEX_PROXIMAL,
    "L Finger11": HumanBoneSpecifications.LEFT_INDEX_INTERMEDIATE,
    "L Finger12": HumanBoneSpecifications.LEFT_INDEX_DISTAL,
    "L Finger2": HumanBoneSpecifications.LEFT_MIDDLE_PROXIMAL,
    "L Finger21": HumanBoneSpecifications.LEFT_MIDDLE_INTERMEDIATE,
    "L Finger22": HumanBoneSpecifications.LEFT_MIDDLE_DISTAL,
    "L Finger3": HumanBoneSpecifications.LEFT_RING_PROXIMAL,
    "L Finger31": HumanBoneSpecifications.LEFT_RING_INTERMEDIATE,
    "L Finger32": HumanBoneSpecifications.LEFT_RING_DISTAL,
    "L Finger4": HumanBoneSpecifications.LEFT_LITTLE_PROXIMAL,
    "L Finger41": HumanBoneSpecifications.LEFT_LITTLE_INTERMEDIATE,
    "L Finger42": HumanBoneSpecifications.LEFT_LITTLE_DISTAL,
}


def prefixed_mapping(key_prefix: str) -> dict[str, HumanBoneSpecification]:
    return {key_prefix + k: v for k, v in mapping_template.items()}


config_bip01 = ("Microsoft Rocketbox (Bip01)", prefixed_mapping("Bip01 "))
config_bip02 = ("Microsoft Rocketbox (Bip02)", prefixed_mapping("Bip02 "))
