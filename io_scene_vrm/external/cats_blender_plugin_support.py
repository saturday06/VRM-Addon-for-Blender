from typing import Dict

import bpy

from ..common.human_bone_mapper import cats_blender_plugin_fix_model_mapping
from ..common.logging import get_logger
from ..common.vrm1.human_bone import HumanBoneSpecification
from .cats_blender_plugin.tools.armature import FixArmature
from .cats_blender_plugin_armature import CatsArmature

logger = get_logger(__name__)


def create_human_bone_mapping(
    armature: bpy.types.Armature,
) -> Dict[str, HumanBoneSpecification]:
    cats_armature = CatsArmature.create(armature)
    try:
        FixArmature.create_cats_bone_name_mapping(cats_armature)
    except Exception:
        logger.exception("Human Bone Name Auto Detection Failure")
        return {}

    mapping = {}
    cats_name_to_original_name = cats_armature.cats_name_to_original_name()
    for (
        cats_name,
        specification,
    ) in cats_blender_plugin_fix_model_mapping.mapping.items():
        original_name = cats_name_to_original_name.get(cats_name)
        if not original_name:
            continue
        mapping[original_name] = specification

    return mapping
