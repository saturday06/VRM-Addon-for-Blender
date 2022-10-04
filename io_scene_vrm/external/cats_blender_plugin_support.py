from typing import Dict, Tuple

import bpy

from ..common.logging import get_logger
from ..common.vrm0.human_bone import HumanBoneName as Vrm0HumanBoneName
from ..common.vrm1.human_bone import HumanBoneName as Vrm1HumanBoneName
from .cats_blender_plugin.tools.armature import FixArmature
from .cats_blender_plugin_armature import CatsArmature

logger = get_logger(__name__)

__cats_bone_name_to_human_bone_name = {
    # Order by priority
    # Required bones
    "Hips": (Vrm0HumanBoneName.HIPS, Vrm1HumanBoneName.HIPS),
    "Spine": (Vrm0HumanBoneName.SPINE, Vrm1HumanBoneName.SPINE),
    "Chest": (Vrm0HumanBoneName.CHEST, Vrm1HumanBoneName.CHEST),
    "Neck": (Vrm0HumanBoneName.NECK, Vrm1HumanBoneName.NECK),
    "Head": (Vrm0HumanBoneName.HEAD, Vrm1HumanBoneName.HEAD),
    "Right arm": (Vrm0HumanBoneName.RIGHT_UPPER_ARM, Vrm1HumanBoneName.RIGHT_UPPER_ARM),
    "Right elbow": (
        Vrm0HumanBoneName.RIGHT_LOWER_ARM,
        Vrm1HumanBoneName.RIGHT_LOWER_ARM,
    ),
    "Right wrist": (Vrm0HumanBoneName.RIGHT_HAND, Vrm1HumanBoneName.RIGHT_HAND),
    "Left arm": (Vrm0HumanBoneName.LEFT_UPPER_ARM, Vrm1HumanBoneName.LEFT_UPPER_ARM),
    "Left elbow": (Vrm0HumanBoneName.LEFT_LOWER_ARM, Vrm1HumanBoneName.LEFT_LOWER_ARM),
    "Left wrist": (Vrm0HumanBoneName.LEFT_HAND, Vrm1HumanBoneName.LEFT_HAND),
    "Right leg": (Vrm0HumanBoneName.RIGHT_UPPER_LEG, Vrm1HumanBoneName.RIGHT_UPPER_LEG),
    "Right knee": (
        Vrm0HumanBoneName.RIGHT_LOWER_LEG,
        Vrm1HumanBoneName.RIGHT_LOWER_LEG,
    ),
    "Right ankle": (Vrm0HumanBoneName.RIGHT_FOOT, Vrm1HumanBoneName.RIGHT_FOOT),
    "Left leg": (Vrm0HumanBoneName.LEFT_UPPER_LEG, Vrm1HumanBoneName.LEFT_UPPER_LEG),
    "Left knee": (Vrm0HumanBoneName.LEFT_LOWER_LEG, Vrm1HumanBoneName.LEFT_LOWER_LEG),
    "Left ankle": (Vrm0HumanBoneName.LEFT_FOOT, Vrm1HumanBoneName.LEFT_FOOT),
    # Optional bones
    "Eye_R": (Vrm0HumanBoneName.RIGHT_EYE, Vrm1HumanBoneName.RIGHT_EYE),
    "Eye_L": (Vrm0HumanBoneName.LEFT_EYE, Vrm1HumanBoneName.LEFT_EYE),
    "Right shoulder": (
        Vrm0HumanBoneName.RIGHT_SHOULDER,
        Vrm1HumanBoneName.RIGHT_SHOULDER,
    ),
    "Left shoulder": (Vrm0HumanBoneName.LEFT_SHOULDER, Vrm1HumanBoneName.LEFT_SHOULDER),
    "Thumb0_R": (
        Vrm0HumanBoneName.RIGHT_THUMB_PROXIMAL,
        Vrm1HumanBoneName.RIGHT_THUMB_METACARPAL,
    ),
    "Thumb1_R": (
        Vrm0HumanBoneName.RIGHT_THUMB_INTERMEDIATE,
        Vrm1HumanBoneName.RIGHT_THUMB_PROXIMAL,
    ),
    "Thumb2_R": (
        Vrm0HumanBoneName.RIGHT_THUMB_DISTAL,
        Vrm1HumanBoneName.RIGHT_THUMB_DISTAL,
    ),
    "Thumb0_L": (
        Vrm0HumanBoneName.LEFT_THUMB_PROXIMAL,
        Vrm1HumanBoneName.LEFT_THUMB_METACARPAL,
    ),
    "Thumb1_L": (
        Vrm0HumanBoneName.LEFT_THUMB_INTERMEDIATE,
        Vrm1HumanBoneName.LEFT_THUMB_PROXIMAL,
    ),
    "Thumb2_L": (
        Vrm0HumanBoneName.LEFT_THUMB_DISTAL,
        Vrm1HumanBoneName.LEFT_THUMB_DISTAL,
    ),
    "IndexFinger1_R": (
        Vrm0HumanBoneName.RIGHT_INDEX_PROXIMAL,
        Vrm1HumanBoneName.RIGHT_INDEX_PROXIMAL,
    ),
    "IndexFinger2_R": (
        Vrm0HumanBoneName.RIGHT_INDEX_INTERMEDIATE,
        Vrm1HumanBoneName.RIGHT_INDEX_INTERMEDIATE,
    ),
    "IndexFinger3_R": (
        Vrm0HumanBoneName.RIGHT_INDEX_DISTAL,
        Vrm1HumanBoneName.RIGHT_INDEX_DISTAL,
    ),
    "IndexFinger1_L": (
        Vrm0HumanBoneName.LEFT_INDEX_PROXIMAL,
        Vrm1HumanBoneName.LEFT_INDEX_PROXIMAL,
    ),
    "IndexFinger2_L": (
        Vrm0HumanBoneName.LEFT_INDEX_INTERMEDIATE,
        Vrm1HumanBoneName.LEFT_INDEX_INTERMEDIATE,
    ),
    "IndexFinger3_L": (
        Vrm0HumanBoneName.LEFT_INDEX_DISTAL,
        Vrm1HumanBoneName.LEFT_INDEX_DISTAL,
    ),
    "MiddleFinger1_R": (
        Vrm0HumanBoneName.RIGHT_MIDDLE_PROXIMAL,
        Vrm1HumanBoneName.RIGHT_MIDDLE_PROXIMAL,
    ),
    "MiddleFinger2_R": (
        Vrm0HumanBoneName.RIGHT_MIDDLE_INTERMEDIATE,
        Vrm1HumanBoneName.RIGHT_MIDDLE_INTERMEDIATE,
    ),
    "MiddleFinger3_R": (
        Vrm0HumanBoneName.RIGHT_MIDDLE_DISTAL,
        Vrm1HumanBoneName.RIGHT_MIDDLE_DISTAL,
    ),
    "MiddleFinger1_L": (
        Vrm0HumanBoneName.LEFT_MIDDLE_PROXIMAL,
        Vrm1HumanBoneName.LEFT_MIDDLE_PROXIMAL,
    ),
    "MiddleFinger2_L": (
        Vrm0HumanBoneName.LEFT_MIDDLE_INTERMEDIATE,
        Vrm1HumanBoneName.LEFT_MIDDLE_INTERMEDIATE,
    ),
    "MiddleFinger3_L": (
        Vrm0HumanBoneName.LEFT_MIDDLE_DISTAL,
        Vrm1HumanBoneName.LEFT_MIDDLE_DISTAL,
    ),
    "RingFinger1_R": (
        Vrm0HumanBoneName.RIGHT_RING_PROXIMAL,
        Vrm1HumanBoneName.RIGHT_RING_PROXIMAL,
    ),
    "RingFinger2_R": (
        Vrm0HumanBoneName.RIGHT_RING_INTERMEDIATE,
        Vrm1HumanBoneName.RIGHT_RING_INTERMEDIATE,
    ),
    "RingFinger3_R": (
        Vrm0HumanBoneName.RIGHT_RING_DISTAL,
        Vrm1HumanBoneName.RIGHT_RING_DISTAL,
    ),
    "RingFinger1_L": (
        Vrm0HumanBoneName.LEFT_RING_PROXIMAL,
        Vrm1HumanBoneName.LEFT_RING_PROXIMAL,
    ),
    "RingFinger2_L": (
        Vrm0HumanBoneName.LEFT_RING_INTERMEDIATE,
        Vrm1HumanBoneName.LEFT_RING_INTERMEDIATE,
    ),
    "RingFinger3_L": (
        Vrm0HumanBoneName.LEFT_RING_DISTAL,
        Vrm1HumanBoneName.LEFT_RING_DISTAL,
    ),
    "LittleFinger1_R": (
        Vrm0HumanBoneName.RIGHT_LITTLE_PROXIMAL,
        Vrm1HumanBoneName.RIGHT_LITTLE_PROXIMAL,
    ),
    "LittleFinger2_R": (
        Vrm0HumanBoneName.RIGHT_LITTLE_INTERMEDIATE,
        Vrm1HumanBoneName.RIGHT_LITTLE_INTERMEDIATE,
    ),
    "LittleFinger3_R": (
        Vrm0HumanBoneName.RIGHT_LITTLE_DISTAL,
        Vrm1HumanBoneName.RIGHT_LITTLE_DISTAL,
    ),
    "LittleFinger1_L": (
        Vrm0HumanBoneName.LEFT_LITTLE_PROXIMAL,
        Vrm1HumanBoneName.LEFT_LITTLE_PROXIMAL,
    ),
    "LittleFinger2_L": (
        Vrm0HumanBoneName.LEFT_LITTLE_INTERMEDIATE,
        Vrm1HumanBoneName.LEFT_LITTLE_INTERMEDIATE,
    ),
    "LittleFinger3_L": (
        Vrm0HumanBoneName.LEFT_LITTLE_DISTAL,
        Vrm1HumanBoneName.LEFT_LITTLE_DISTAL,
    ),
    "Right toe": (Vrm0HumanBoneName.RIGHT_TOES, Vrm1HumanBoneName.RIGHT_TOES),
    "Left toe": (Vrm0HumanBoneName.LEFT_TOES, Vrm1HumanBoneName.LEFT_TOES),
}


def create_human_bone_mapping(
    armature: bpy.types.Armature,
) -> Dict[str, Tuple[Vrm0HumanBoneName, Vrm1HumanBoneName]]:
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
