# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Mapping
from typing import Optional

from bpy.types import Armature, Object

from ..logger import get_logger
from ..vrm1.human_bone import HumanBoneSpecification
from . import (
    biped_mapping,
    cats_blender_plugin_fix_model_mapping,
    microsoft_rocketbox_mapping,
    mixamo_mapping,
    mmd_mapping,
    ready_player_me_mapping,
    rigify_meta_rig_mapping,
    unreal_mapping,
    vrm_addon_mapping,
    vroid_mapping,
)

logger = get_logger(__name__)


def match_count(
    armature: Armature, mapping: Mapping[str, HumanBoneSpecification]
) -> int:
    count = 0

    mapping = {
        bpy_name: specification
        for bpy_name, specification in mapping.items()
        if bpy_name in armature.bones
    }

    # Validate bone ordering
    for bpy_name, specification in mapping.items():
        bone = armature.bones.get(bpy_name)
        if not bone:
            continue

        parent_specification: Optional[HumanBoneSpecification] = None
        search_parent_specification = specification.parent()
        while search_parent_specification:
            if search_parent_specification in mapping.values():
                parent_specification = search_parent_specification
                break
            search_parent_specification = search_parent_specification.parent()

        found = False
        bone = bone.parent
        while bone:
            search_specification = mapping.get(bone.name)
            if search_specification:
                found = search_specification == parent_specification
                break
            bone = bone.parent

        if found or not parent_specification:
            count += 1
            continue

    return count


def match_counts(
    armature: object, mapping: Mapping[str, HumanBoneSpecification]
) -> tuple[int, int]:
    if not isinstance(armature, Armature):
        message = f"{type(armature)} is not an Armature"
        raise TypeError(message)
    required_mapping = {
        bpy_name: required_specification
        for bpy_name, required_specification in mapping.items()
        if required_specification.requirement
    }
    return (match_count(armature, required_mapping), match_count(armature, mapping))


def sorted_required_first(
    mapping: Mapping[str, HumanBoneSpecification],
) -> dict[str, HumanBoneSpecification]:
    sorted_mapping: dict[str, HumanBoneSpecification] = {}
    sorted_mapping.update(
        {
            bpy_name: specification
            for bpy_name, specification in mapping.items()
            if specification.requirement
        }
    )
    sorted_mapping.update(
        {
            bpy_name: specification
            for bpy_name, specification in mapping.items()
            if not specification.requirement
        }
    )
    return sorted_mapping


def create_human_bone_mapping(
    armature: Object,
) -> dict[str, HumanBoneSpecification]:
    ((required_count, _all_count), name, mapping) = sorted(
        [
            (match_counts(armature.data, mapping), name, mapping)
            for name, mapping in [
                mmd_mapping.create_config(armature),
                biped_mapping.create_config(armature),
                mixamo_mapping.CONFIG,
                unreal_mapping.CONFIG,
                ready_player_me_mapping.CONFIG,
                cats_blender_plugin_fix_model_mapping.CONFIG,
                microsoft_rocketbox_mapping.CONFIG_BIP01,
                microsoft_rocketbox_mapping.CONFIG_BIP02,
                rigify_meta_rig_mapping.CONFIG,
                vroid_mapping.CONFIG,
                vroid_mapping.CONFIG_SYMMETRICAL,
                vrm_addon_mapping.CONFIG_VRM1,
                vrm_addon_mapping.CONFIG_VRM0,
            ]
        ]
    )[-1]
    if required_count:
        logger.debug('Treat as "%s" bone mappings', name)
        return sorted_required_first(mapping)
    return {}
