from typing import Dict, Optional

import bpy

from ..logging import get_logger
from ..vrm1.human_bone import HumanBoneSpecification
from . import (
    cats_blender_plugin_fix_model_mapping,
    microsoft_rocketbox_mapping,
    mmd_mapping,
    ready_player_me_mapping,
    rigify_meta_rig_mapping,
    vrm_addon_mapping,
)

logger = get_logger(__name__)


def match_mapping(
    armature: bpy.types.Armature, mapping: Dict[str, HumanBoneSpecification]
) -> bool:
    required_mappings: Dict[str, HumanBoneSpecification] = {}
    for bpy_name, required_specification in mapping.items():
        if required_specification.requirement:
            required_mappings[bpy_name] = required_specification

    if not required_mappings:
        return False

    # Validate required bone ordering
    for bpy_name, specification in required_mappings.items():
        bone = armature.bones.get(bpy_name)
        if not bone:
            return False

        required_parent_specification: Optional[HumanBoneSpecification] = None
        search_specification = specification.parent()
        while search_specification:
            if search_specification.requirement:
                required_parent_specification = search_specification
                break
            search_specification = search_specification.parent()

        found = False
        bone = bone.parent
        while bone:
            search_required_specification = required_mappings.get(bone.name)
            if search_required_specification:
                if search_required_specification != required_parent_specification:
                    return False
                found = True
                break
            bone = bone.parent

        if found:
            continue

        if not required_parent_specification:
            continue

        return False

    return True


def sorted_required_first(
    mapping: Dict[str, HumanBoneSpecification]
) -> Dict[str, HumanBoneSpecification]:
    sorted_mapping: Dict[str, HumanBoneSpecification] = {}
    for bpy_name, specification in mapping.items():
        if specification.requirement:
            sorted_mapping[bpy_name] = specification
    for bpy_name, specification in mapping.items():
        if not specification.requirement:
            sorted_mapping[bpy_name] = specification
    return sorted_mapping


def create_human_bone_mapping(
    armature: bpy.types.Object,
) -> Dict[str, HumanBoneSpecification]:
    for name, mapping in [
        mmd_mapping.create_config(armature),
        ready_player_me_mapping.config,
        cats_blender_plugin_fix_model_mapping.config,
        microsoft_rocketbox_mapping.config_bip01,
        microsoft_rocketbox_mapping.config_bip02,
        rigify_meta_rig_mapping.config,
        vrm_addon_mapping.config_vrm1,
        vrm_addon_mapping.config_vrm0,
    ]:
        if match_mapping(armature.data, mapping):
            logger.warning(f'Treat as "{name}" bone mappings')
            return sorted_required_first(mapping)

    return {}
