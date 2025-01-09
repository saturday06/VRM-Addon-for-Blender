# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from bpy.types import Object

from ..logger import get_logger
from ..vrm1.human_bone import HumanBoneSpecification, HumanBoneSpecifications

logger = get_logger(__name__)

mmd_bone_name_and_human_bone_specification_pairs: list[
    tuple[str, HumanBoneSpecification]
] = [
    ("頭", HumanBoneSpecifications.HEAD),
    ("右目", HumanBoneSpecifications.RIGHT_EYE),
    ("左目", HumanBoneSpecifications.LEFT_EYE),
    ("首", HumanBoneSpecifications.NECK),
    ("上半身2", HumanBoneSpecifications.CHEST),
    ("上半身", HumanBoneSpecifications.SPINE),
    ("センター", HumanBoneSpecifications.HIPS),
    ("右肩", HumanBoneSpecifications.RIGHT_SHOULDER),
    ("右腕", HumanBoneSpecifications.RIGHT_UPPER_ARM),
    ("右ひじ", HumanBoneSpecifications.RIGHT_LOWER_ARM),
    ("右手首", HumanBoneSpecifications.RIGHT_HAND),
    ("右足", HumanBoneSpecifications.RIGHT_UPPER_LEG),
    ("右ひざ", HumanBoneSpecifications.RIGHT_LOWER_LEG),
    ("右足首", HumanBoneSpecifications.RIGHT_FOOT),
    ("右つま先", HumanBoneSpecifications.RIGHT_TOES),
    ("右足先EX", HumanBoneSpecifications.RIGHT_TOES),
    ("左肩", HumanBoneSpecifications.LEFT_SHOULDER),
    ("左腕", HumanBoneSpecifications.LEFT_UPPER_ARM),
    ("左ひじ", HumanBoneSpecifications.LEFT_LOWER_ARM),
    ("左手首", HumanBoneSpecifications.LEFT_HAND),
    ("左足", HumanBoneSpecifications.LEFT_UPPER_LEG),
    ("左ひざ", HumanBoneSpecifications.LEFT_LOWER_LEG),
    ("左足首", HumanBoneSpecifications.LEFT_FOOT),
    ("左つま先", HumanBoneSpecifications.LEFT_TOES),
    ("左足先EX", HumanBoneSpecifications.LEFT_TOES),
    ("右親指０", HumanBoneSpecifications.RIGHT_THUMB_METACARPAL),
    ("右親指１", HumanBoneSpecifications.RIGHT_THUMB_METACARPAL),
    ("右親指１", HumanBoneSpecifications.RIGHT_THUMB_PROXIMAL),
    ("右親指２", HumanBoneSpecifications.RIGHT_THUMB_PROXIMAL),
    ("右親指２", HumanBoneSpecifications.RIGHT_THUMB_DISTAL),
    ("右人指１", HumanBoneSpecifications.RIGHT_INDEX_PROXIMAL),
    ("右人指２", HumanBoneSpecifications.RIGHT_INDEX_INTERMEDIATE),
    ("右人指３", HumanBoneSpecifications.RIGHT_INDEX_DISTAL),
    ("右中指１", HumanBoneSpecifications.RIGHT_MIDDLE_PROXIMAL),
    ("右中指２", HumanBoneSpecifications.RIGHT_MIDDLE_INTERMEDIATE),
    ("右中指３", HumanBoneSpecifications.RIGHT_MIDDLE_DISTAL),
    ("右薬指１", HumanBoneSpecifications.RIGHT_RING_PROXIMAL),
    ("右薬指２", HumanBoneSpecifications.RIGHT_RING_INTERMEDIATE),
    ("右薬指３", HumanBoneSpecifications.RIGHT_RING_DISTAL),
    ("右小指１", HumanBoneSpecifications.RIGHT_LITTLE_PROXIMAL),
    ("右小指２", HumanBoneSpecifications.RIGHT_LITTLE_INTERMEDIATE),
    ("右小指３", HumanBoneSpecifications.RIGHT_LITTLE_DISTAL),
    ("左親指０", HumanBoneSpecifications.LEFT_THUMB_METACARPAL),
    ("左親指１", HumanBoneSpecifications.LEFT_THUMB_METACARPAL),
    ("左親指１", HumanBoneSpecifications.LEFT_THUMB_PROXIMAL),
    ("左親指２", HumanBoneSpecifications.LEFT_THUMB_PROXIMAL),
    ("左親指２", HumanBoneSpecifications.LEFT_THUMB_DISTAL),
    ("左人指１", HumanBoneSpecifications.LEFT_INDEX_PROXIMAL),
    ("左人指２", HumanBoneSpecifications.LEFT_INDEX_INTERMEDIATE),
    ("左人指３", HumanBoneSpecifications.LEFT_INDEX_DISTAL),
    ("左中指１", HumanBoneSpecifications.LEFT_MIDDLE_PROXIMAL),
    ("左中指２", HumanBoneSpecifications.LEFT_MIDDLE_INTERMEDIATE),
    ("左中指３", HumanBoneSpecifications.LEFT_MIDDLE_DISTAL),
    ("左薬指１", HumanBoneSpecifications.LEFT_RING_PROXIMAL),
    ("左薬指２", HumanBoneSpecifications.LEFT_RING_INTERMEDIATE),
    ("左薬指３", HumanBoneSpecifications.LEFT_RING_DISTAL),
    ("左小指１", HumanBoneSpecifications.LEFT_LITTLE_PROXIMAL),
    ("左小指２", HumanBoneSpecifications.LEFT_LITTLE_INTERMEDIATE),
    ("左小指３", HumanBoneSpecifications.LEFT_LITTLE_DISTAL),
]


def create_config(
    armature: Object,
) -> tuple[str, dict[str, HumanBoneSpecification]]:
    mmd_bone_name_to_bpy_bone_name: dict[str, str] = {}
    for bone in armature.pose.bones:
        # https://github.com/UuuNyaa/blender_mmd_tools/blob/97861e3c32ba423833b6c5fc3432127b1ec1182a/mmd_tools/properties/__init__.py#L45-L46
        mmd_bone = getattr(bone, "mmd_bone", None)
        if not mmd_bone:
            continue

        # https://github.com/UuuNyaa/blender_mmd_tools/blob/97861e3c32ba423833b6c5fc3432127b1ec1182a/mmd_tools/properties/bone.py#L43-L48
        name_j = getattr(mmd_bone, "name_j", None)
        if not isinstance(name_j, str):
            continue

        mmd_bone_name_to_bpy_bone_name[name_j] = bone.name

    mapping: dict[str, HumanBoneSpecification] = {}
    for (
        mmd_bone_name,
        human_bone_specification,
    ) in mmd_bone_name_and_human_bone_specification_pairs:
        bpy_bone_name = mmd_bone_name_to_bpy_bone_name.get(mmd_bone_name)
        if not bpy_bone_name:
            continue
        if bpy_bone_name in mapping or human_bone_specification in mapping.values():
            continue
        mapping[bpy_bone_name] = human_bone_specification

    name = "MikuMikuDance"
    for specification in HumanBoneSpecifications.all_human_bones:
        if specification.requirement and specification not in mapping.values():
            return (name, {})

    return (name, mapping)
