# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Mapping

from bpy.types import Object

from ..logger import get_logger
from ..vrm1.human_bone import HumanBoneSpecification, HumanBoneSpecifications

logger = get_logger(__name__)

biped_mapping = {  # type:ignore
    ("Bip001", "Pelvis"): HumanBoneSpecifications.HIPS,
    ("Bip001", "Spine"): HumanBoneSpecifications.SPINE,
    ("Bip001", "Spine2"): HumanBoneSpecifications.CHEST,
    ("Bip001", "Neck"): HumanBoneSpecifications.NECK,
    ("Bip001", "Head"): HumanBoneSpecifications.HEAD,
    ("Bip001", "R", "Clavicle"): HumanBoneSpecifications.RIGHT_SHOULDER,
    ("Bip001", "R", "UpperArm"): HumanBoneSpecifications.RIGHT_UPPER_ARM,
    ("Bip001", "R", "Forearm"): HumanBoneSpecifications.RIGHT_LOWER_ARM,
    ("Bip001", "R", "Hand"): HumanBoneSpecifications.RIGHT_HAND,
    ("Bip001", "L", "Clavicle"): HumanBoneSpecifications.LEFT_SHOULDER,
    ("Bip001", "L", "UpperArm"): HumanBoneSpecifications.LEFT_UPPER_ARM,
    ("Bip001", "L", "Forearm"): HumanBoneSpecifications.LEFT_LOWER_ARM,
    ("Bip001", "L", "Hand"): HumanBoneSpecifications.LEFT_HAND,
    ("Bip001", "R", "Thigh"): HumanBoneSpecifications.RIGHT_UPPER_LEG,
    ("Bip001", "R", "Calf"): HumanBoneSpecifications.RIGHT_LOWER_LEG,
    ("Bip001", "R", "Foot"): HumanBoneSpecifications.RIGHT_FOOT,
    ("Bip001", "R", "Toe0"): HumanBoneSpecifications.RIGHT_TOES,
    ("Bip001", "L", "Thigh"): HumanBoneSpecifications.LEFT_UPPER_LEG,
    ("Bip001", "L", "Calf"): HumanBoneSpecifications.LEFT_LOWER_LEG,
    ("Bip001", "L", "Foot"): HumanBoneSpecifications.LEFT_FOOT,
    ("Bip001", "L", "Toe0"): HumanBoneSpecifications.LEFT_TOES,
    ("Bip001", "R", "Finger0"): HumanBoneSpecifications.RIGHT_THUMB_METACARPAL,
    ("Bip001", "R", "Finger01"): HumanBoneSpecifications.RIGHT_THUMB_PROXIMAL,
    ("Bip001", "R", "Finger02"): HumanBoneSpecifications.RIGHT_THUMB_DISTAL,
    ("Bip001", "L", "Finger0"): HumanBoneSpecifications.LEFT_THUMB_METACARPAL,
    ("Bip001", "L", "Finger01"): HumanBoneSpecifications.LEFT_THUMB_PROXIMAL,
    ("Bip001", "L", "Finger02"): HumanBoneSpecifications.LEFT_THUMB_DISTAL,
    ("Bip001", "R", "Finger1"): HumanBoneSpecifications.RIGHT_INDEX_PROXIMAL,
    ("Bip001", "R", "Finger11"): HumanBoneSpecifications.RIGHT_INDEX_INTERMEDIATE,
    ("Bip001", "R", "Finger12"): HumanBoneSpecifications.RIGHT_INDEX_DISTAL,
    ("Bip001", "L", "Finger1"): HumanBoneSpecifications.LEFT_INDEX_PROXIMAL,
    ("Bip001", "L", "Finger11"): HumanBoneSpecifications.LEFT_INDEX_INTERMEDIATE,
    ("Bip001", "L", "Finger12"): HumanBoneSpecifications.LEFT_INDEX_DISTAL,
    ("Bip001", "R", "Finger2"): HumanBoneSpecifications.RIGHT_MIDDLE_PROXIMAL,
    ("Bip001", "R", "Finger21"): HumanBoneSpecifications.RIGHT_MIDDLE_INTERMEDIATE,
    ("Bip001", "R", "Finger22"): HumanBoneSpecifications.RIGHT_MIDDLE_DISTAL,
    ("Bip001", "L", "Finger2"): HumanBoneSpecifications.LEFT_MIDDLE_PROXIMAL,
    ("Bip001", "L", "Finger21"): HumanBoneSpecifications.LEFT_MIDDLE_INTERMEDIATE,
    ("Bip001", "L", "Finger22"): HumanBoneSpecifications.LEFT_MIDDLE_DISTAL,
    ("Bip001", "R", "Finger3"): HumanBoneSpecifications.RIGHT_RING_PROXIMAL,
    ("Bip001", "R", "Finger31"): HumanBoneSpecifications.RIGHT_RING_INTERMEDIATE,
    ("Bip001", "R", "Finger32"): HumanBoneSpecifications.RIGHT_RING_DISTAL,
    ("Bip001", "L", "Finger3"): HumanBoneSpecifications.LEFT_RING_PROXIMAL,
    ("Bip001", "L", "Finger31"): HumanBoneSpecifications.LEFT_RING_INTERMEDIATE,
    ("Bip001", "L", "Finger32"): HumanBoneSpecifications.LEFT_RING_DISTAL,
    ("Bip001", "R", "Finger4"): HumanBoneSpecifications.RIGHT_LITTLE_PROXIMAL,
    ("Bip001", "R", "Finger41"): HumanBoneSpecifications.RIGHT_LITTLE_INTERMEDIATE,
    ("Bip001", "R", "Finger42"): HumanBoneSpecifications.RIGHT_LITTLE_DISTAL,
    ("Bip001", "L", "Finger4"): HumanBoneSpecifications.LEFT_LITTLE_PROXIMAL,
    ("Bip001", "L", "Finger41"): HumanBoneSpecifications.LEFT_LITTLE_INTERMEDIATE,
    ("Bip001", "L", "Finger42"): HumanBoneSpecifications.LEFT_LITTLE_DISTAL,
}


def create_config(
    armature: Object,
) -> tuple[str, Mapping[str, HumanBoneSpecification]]:
    mapping: dict[str, HumanBoneSpecification] = {}
    for bone in armature.pose.bones:
        for biped_bone in biped_mapping.keys():
            if (
                bone.name.startswith(biped_bone[0])
                and bone.name.endswith(biped_bone[-1])
                and biped_bone[1] in bone.name
            ):
                mapping[bone.name] = biped_mapping[biped_bone]

    name = "Bip001"
    for specification in HumanBoneSpecifications.all_human_bones:
        if specification.requirement and specification not in mapping.values():
            return (name, {})

    return (name, mapping)
