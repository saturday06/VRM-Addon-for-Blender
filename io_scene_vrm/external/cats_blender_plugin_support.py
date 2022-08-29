from typing import Dict

import bpy

from ..common.logging import get_logger
from ..common.vrm0.human_bone import HumanBoneName
from .cats_blender_plugin.tools.armature import FixArmature
from .cats_blender_plugin_armature import CatsArmature

logger = get_logger(__name__)

__cats_bone_name_to_human_bone_name = {
    # Order by priority
    # Required bones
    "Hips": HumanBoneName.HIPS,
    "Spine": HumanBoneName.SPINE,
    "Chest": HumanBoneName.CHEST,
    "Neck": HumanBoneName.NECK,
    "Head": HumanBoneName.HEAD,
    "Right arm": HumanBoneName.RIGHT_UPPER_ARM,
    "Right elbow": HumanBoneName.RIGHT_LOWER_ARM,
    "Right wrist": HumanBoneName.RIGHT_HAND,
    "Left arm": HumanBoneName.LEFT_UPPER_ARM,
    "Left elbow": HumanBoneName.LEFT_LOWER_ARM,
    "Left wrist": HumanBoneName.LEFT_HAND,
    "Right leg": HumanBoneName.RIGHT_UPPER_LEG,
    "Right knee": HumanBoneName.RIGHT_LOWER_LEG,
    "Right ankle": HumanBoneName.RIGHT_FOOT,
    "Left leg": HumanBoneName.LEFT_UPPER_LEG,
    "Left knee": HumanBoneName.LEFT_LOWER_LEG,
    "Left ankle": HumanBoneName.LEFT_FOOT,
    # Optional bones
    "Eye_R": HumanBoneName.RIGHT_EYE,
    "Eye_L": HumanBoneName.LEFT_EYE,
    "Right shoulder": HumanBoneName.RIGHT_SHOULDER,
    "Left shoulder": HumanBoneName.LEFT_SHOULDER,
    "Thumb0_R": HumanBoneName.RIGHT_THUMB_PROXIMAL,
    "Thumb1_R": HumanBoneName.RIGHT_THUMB_INTERMEDIATE,
    "Thumb2_R": HumanBoneName.RIGHT_THUMB_DISTAL,
    "Thumb0_L": HumanBoneName.LEFT_THUMB_PROXIMAL,
    "Thumb1_L": HumanBoneName.LEFT_THUMB_INTERMEDIATE,
    "Thumb2_L": HumanBoneName.LEFT_THUMB_DISTAL,
    "IndexFinger1_R": HumanBoneName.RIGHT_INDEX_PROXIMAL,
    "IndexFinger2_R": HumanBoneName.RIGHT_INDEX_INTERMEDIATE,
    "IndexFinger3_R": HumanBoneName.RIGHT_INDEX_DISTAL,
    "IndexFinger1_L": HumanBoneName.LEFT_INDEX_PROXIMAL,
    "IndexFinger2_L": HumanBoneName.LEFT_INDEX_INTERMEDIATE,
    "IndexFinger3_L": HumanBoneName.LEFT_INDEX_DISTAL,
    "MiddleFinger1_R": HumanBoneName.RIGHT_MIDDLE_PROXIMAL,
    "MiddleFinger2_R": HumanBoneName.RIGHT_MIDDLE_INTERMEDIATE,
    "MiddleFinger3_R": HumanBoneName.RIGHT_MIDDLE_DISTAL,
    "MiddleFinger1_L": HumanBoneName.LEFT_MIDDLE_PROXIMAL,
    "MiddleFinger2_L": HumanBoneName.LEFT_MIDDLE_INTERMEDIATE,
    "MiddleFinger3_L": HumanBoneName.LEFT_MIDDLE_DISTAL,
    "RingFinger1_R": HumanBoneName.RIGHT_RING_PROXIMAL,
    "RingFinger2_R": HumanBoneName.RIGHT_RING_INTERMEDIATE,
    "RingFinger3_R": HumanBoneName.RIGHT_RING_DISTAL,
    "RingFinger1_L": HumanBoneName.LEFT_RING_PROXIMAL,
    "RingFinger2_L": HumanBoneName.LEFT_RING_INTERMEDIATE,
    "RingFinger3_L": HumanBoneName.LEFT_RING_DISTAL,
    "LittleFinger1_R": HumanBoneName.RIGHT_LITTLE_PROXIMAL,
    "LittleFinger2_R": HumanBoneName.RIGHT_LITTLE_INTERMEDIATE,
    "LittleFinger3_R": HumanBoneName.RIGHT_LITTLE_DISTAL,
    "LittleFinger1_L": HumanBoneName.LEFT_LITTLE_PROXIMAL,
    "LittleFinger2_L": HumanBoneName.LEFT_LITTLE_INTERMEDIATE,
    "LittleFinger3_L": HumanBoneName.LEFT_LITTLE_DISTAL,
    "Right toe": HumanBoneName.RIGHT_TOES,
    "Left toe": HumanBoneName.LEFT_TOES,
}


def create_human_bone_mapping(armature: bpy.types.Armature) -> Dict[str, HumanBoneName]:
    cats_armature = CatsArmature.create(armature)
    try:
        FixArmature.create_cats_bone_name_mapping(cats_armature)
    except Exception:
        logger.exception("Human Bone Name Auto Detection Failure")

    mapping = {}
    cats_name_to_original_name = cats_armature.cats_name_to_original_name()
    for cats_name, human_name in __cats_bone_name_to_human_bone_name.items():
        original_name = cats_name_to_original_name.get(cats_name)
        if not original_name:
            continue
        mapping[original_name] = human_name

    return mapping
