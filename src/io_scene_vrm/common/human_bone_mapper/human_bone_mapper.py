# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import re
from collections.abc import Mapping
from typing import Optional

from bpy.types import Armature, Object

from ..char import FULLWIDTH_ASCII_TO_ASCII_MAP
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


def canonicalize_bone_name(bone_name: str) -> str:
    bone_name = "".join(FULLWIDTH_ASCII_TO_ASCII_MAP.get(c, c) for c in bone_name)
    bone_name = re.sub(r"([a-z])([A-Z])", r"\1.\2", bone_name)
    bone_name = bone_name.lower()
    bone_name = "".join(" " if c.isspace() else c for c in bone_name)
    bone_name = re.sub(r"(\d+)", r".\1.", bone_name).strip(".")
    bone_name_components = re.split(r"[-._: (){}[\]<>]+", bone_name)
    for patterns, replacement in {
        ("l", "左"): "left",
        ("r", "右"): "right",
    }.items():
        bone_name_components = [
            replacement if bone_name_component in patterns else bone_name_component
            for bone_name_component in bone_name_components
        ]
    return ".".join(bone_name_components)


def match_bone_name(bone_name1: str, bone_name2: str) -> bool:
    return canonicalize_bone_name(bone_name1) == canonicalize_bone_name(bone_name2)


def match_count(
    armature: Armature, mapping: Mapping[str, HumanBoneSpecification]
) -> int:
    count = 0

    mapping = {
        bpy_name: specification
        for bpy_name, specification in mapping.items()
        if any(match_bone_name(bpy_name, bone.name) for bone in armature.bones)
    }

    # Validate bone ordering
    for bpy_name, specification in mapping.items():
        bone = next(
            (bone for bone in armature.bones if match_bone_name(bpy_name, bone.name)),
            None,
        )
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
            search_specification = next(
                (
                    search_specification
                    for bpy_name, search_specification in mapping.items()
                    if match_bone_name(bpy_name, bone.name)
                ),
                None,
            )
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
    armature: Armature,
    mapping: Mapping[str, HumanBoneSpecification],
) -> dict[str, HumanBoneSpecification]:
    bpy_bone_name_mapping: dict[str, HumanBoneSpecification] = {
        bpy_bone_name: specification
        for original_bone_name, specification in mapping.items()
        if (
            bpy_bone_name := next(
                (
                    bone.name
                    for bone in armature.bones
                    if match_bone_name(original_bone_name, bone.name)
                ),
                None,
            )
        )
    }
    sorted_mapping: dict[str, HumanBoneSpecification] = {}
    sorted_mapping.update(
        {
            bpy_name: specification
            for bpy_name, specification in bpy_bone_name_mapping.items()
            if specification.requirement
        }
    )
    sorted_mapping.update(
        {
            bpy_name: specification
            for bpy_name, specification in bpy_bone_name_mapping.items()
            if not specification.requirement
        }
    )
    return sorted_mapping


def create_human_bone_mapping(
    armature: Object,
) -> dict[str, HumanBoneSpecification]:
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        raise TypeError
    ((required_count, _all_count), name, mapping) = sorted(
        [
            (match_counts(armature_data, mapping), name, mapping)
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
        return sorted_required_first(armature_data, mapping)
    return {}
