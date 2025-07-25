# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Mapping
from typing import Final

from ..vrm1.human_bone import HumanBoneSpecification, HumanBoneSpecifications

MAPPING: Final[Mapping[str, HumanBoneSpecification]] = {
    "head": HumanBoneSpecifications.HEAD,
    "spine": HumanBoneSpecifications.SPINE,
    "hips": HumanBoneSpecifications.HIPS,
    "upper_arm.R": HumanBoneSpecifications.RIGHT_UPPER_ARM,
    "lower_arm.R": HumanBoneSpecifications.RIGHT_LOWER_ARM,
    "hand.R": HumanBoneSpecifications.RIGHT_HAND,
    "upper_arm.L": HumanBoneSpecifications.LEFT_UPPER_ARM,
    "lower_arm.L": HumanBoneSpecifications.LEFT_LOWER_ARM,
    "hand.L": HumanBoneSpecifications.LEFT_HAND,
    "upper_leg.R": HumanBoneSpecifications.RIGHT_UPPER_LEG,
    "lower_leg.R": HumanBoneSpecifications.RIGHT_LOWER_LEG,
    "foot.R": HumanBoneSpecifications.RIGHT_FOOT,
    "upper_leg.L": HumanBoneSpecifications.LEFT_UPPER_LEG,
    "lower_leg.L": HumanBoneSpecifications.LEFT_LOWER_LEG,
    "foot.L": HumanBoneSpecifications.LEFT_FOOT,
    "eye.R": HumanBoneSpecifications.RIGHT_EYE,
    "eye.L": HumanBoneSpecifications.LEFT_EYE,
    "neck": HumanBoneSpecifications.NECK,
    "shoulder.L": HumanBoneSpecifications.LEFT_SHOULDER,
    "shoulder.R": HumanBoneSpecifications.RIGHT_SHOULDER,
    "upper_chest": HumanBoneSpecifications.UPPER_CHEST,
    "chest": HumanBoneSpecifications.CHEST,
    "toes.R": HumanBoneSpecifications.RIGHT_TOES,
    "toes.L": HumanBoneSpecifications.LEFT_TOES,
    "thumb_metacarpal.L": HumanBoneSpecifications.LEFT_THUMB_METACARPAL,
    "thumb.metacarpal.L": HumanBoneSpecifications.LEFT_THUMB_METACARPAL,
    "thumb_proximal.L": HumanBoneSpecifications.LEFT_THUMB_PROXIMAL,
    "thumb.proximal.L": HumanBoneSpecifications.LEFT_THUMB_PROXIMAL,
    "thumb_distal.L": HumanBoneSpecifications.LEFT_THUMB_DISTAL,
    "thumb.distal.L": HumanBoneSpecifications.LEFT_THUMB_DISTAL,
    "index_proximal.L": HumanBoneSpecifications.LEFT_INDEX_PROXIMAL,
    "index.proximal.L": HumanBoneSpecifications.LEFT_INDEX_PROXIMAL,
    "index_intermediate.L": HumanBoneSpecifications.LEFT_INDEX_INTERMEDIATE,
    "index.intermediate.L": HumanBoneSpecifications.LEFT_INDEX_INTERMEDIATE,
    "index_distal.L": HumanBoneSpecifications.LEFT_INDEX_DISTAL,
    "index.distal.L": HumanBoneSpecifications.LEFT_INDEX_DISTAL,
    "middle_proximal.L": HumanBoneSpecifications.LEFT_MIDDLE_PROXIMAL,
    "middle.proximal.L": HumanBoneSpecifications.LEFT_MIDDLE_PROXIMAL,
    "middle_intermediate.L": HumanBoneSpecifications.LEFT_MIDDLE_INTERMEDIATE,
    "middle.intermediate.L": HumanBoneSpecifications.LEFT_MIDDLE_INTERMEDIATE,
    "middle_distal.L": HumanBoneSpecifications.LEFT_MIDDLE_DISTAL,
    "middle.distal.L": HumanBoneSpecifications.LEFT_MIDDLE_DISTAL,
    "ring_proximal.L": HumanBoneSpecifications.LEFT_RING_PROXIMAL,
    "ring.proximal.L": HumanBoneSpecifications.LEFT_RING_PROXIMAL,
    "ring_intermediate.L": HumanBoneSpecifications.LEFT_RING_INTERMEDIATE,
    "ring.intermediate.L": HumanBoneSpecifications.LEFT_RING_INTERMEDIATE,
    "ring_distal.L": HumanBoneSpecifications.LEFT_RING_DISTAL,
    "ring.distal.L": HumanBoneSpecifications.LEFT_RING_DISTAL,
    "little_proximal.L": HumanBoneSpecifications.LEFT_LITTLE_PROXIMAL,
    "little.proximal.L": HumanBoneSpecifications.LEFT_LITTLE_PROXIMAL,
    "little_intermediate.L": HumanBoneSpecifications.LEFT_LITTLE_INTERMEDIATE,
    "little.intermediate.L": HumanBoneSpecifications.LEFT_LITTLE_INTERMEDIATE,
    "little_distal.L": HumanBoneSpecifications.LEFT_LITTLE_DISTAL,
    "little.distal.L": HumanBoneSpecifications.LEFT_LITTLE_DISTAL,
    "thumb_metacarpal.R": HumanBoneSpecifications.RIGHT_THUMB_METACARPAL,
    "thumb.metacarpal.R": HumanBoneSpecifications.RIGHT_THUMB_METACARPAL,
    "thumb_proximal.R": HumanBoneSpecifications.RIGHT_THUMB_PROXIMAL,
    "thumb.proximal.R": HumanBoneSpecifications.RIGHT_THUMB_PROXIMAL,
    "thumb_distal.R": HumanBoneSpecifications.RIGHT_THUMB_DISTAL,
    "thumb.distal.R": HumanBoneSpecifications.RIGHT_THUMB_DISTAL,
    "index_proximal.R": HumanBoneSpecifications.RIGHT_INDEX_PROXIMAL,
    "index.proximal.R": HumanBoneSpecifications.RIGHT_INDEX_PROXIMAL,
    "index_intermediate.R": HumanBoneSpecifications.RIGHT_INDEX_INTERMEDIATE,
    "index.intermediate.R": HumanBoneSpecifications.RIGHT_INDEX_INTERMEDIATE,
    "index_distal.R": HumanBoneSpecifications.RIGHT_INDEX_DISTAL,
    "index.distal.R": HumanBoneSpecifications.RIGHT_INDEX_DISTAL,
    "middle_proximal.R": HumanBoneSpecifications.RIGHT_MIDDLE_PROXIMAL,
    "middle.proximal.R": HumanBoneSpecifications.RIGHT_MIDDLE_PROXIMAL,
    "middle_intermediate.R": HumanBoneSpecifications.RIGHT_MIDDLE_INTERMEDIATE,
    "middle.intermediate.R": HumanBoneSpecifications.RIGHT_MIDDLE_INTERMEDIATE,
    "middle_distal.R": HumanBoneSpecifications.RIGHT_MIDDLE_DISTAL,
    "middle.distal.R": HumanBoneSpecifications.RIGHT_MIDDLE_DISTAL,
    "ring_proximal.R": HumanBoneSpecifications.RIGHT_RING_PROXIMAL,
    "ring.proximal.R": HumanBoneSpecifications.RIGHT_RING_PROXIMAL,
    "ring_intermediate.R": HumanBoneSpecifications.RIGHT_RING_INTERMEDIATE,
    "ring.intermediate.R": HumanBoneSpecifications.RIGHT_RING_INTERMEDIATE,
    "ring_distal.R": HumanBoneSpecifications.RIGHT_RING_DISTAL,
    "ring.distal.R": HumanBoneSpecifications.RIGHT_RING_DISTAL,
    "little_proximal.R": HumanBoneSpecifications.RIGHT_LITTLE_PROXIMAL,
    "little.proximal.R": HumanBoneSpecifications.RIGHT_LITTLE_PROXIMAL,
    "little_intermediate.R": HumanBoneSpecifications.RIGHT_LITTLE_INTERMEDIATE,
    "little.intermediate.R": HumanBoneSpecifications.RIGHT_LITTLE_INTERMEDIATE,
    "little_distal.R": HumanBoneSpecifications.RIGHT_LITTLE_DISTAL,
    "little.distal.R": HumanBoneSpecifications.RIGHT_LITTLE_DISTAL,
}

CONFIG_VRM1: Final = ("VRM Add-on (VRM1)", MAPPING)
CONFIG_VRM0: Final = (
    "VRM Add-on (VRM0)",
    {
        **MAPPING,
        "thumb_proximal.L": HumanBoneSpecifications.LEFT_THUMB_METACARPAL,
        "thumb.proximal.L": HumanBoneSpecifications.LEFT_THUMB_METACARPAL,
        "thumb_intermediate.L": HumanBoneSpecifications.LEFT_THUMB_PROXIMAL,
        "thumb.intermediate.L": HumanBoneSpecifications.LEFT_THUMB_PROXIMAL,
        "thumb_distal.L": HumanBoneSpecifications.LEFT_THUMB_DISTAL,
        "thumb.distal.L": HumanBoneSpecifications.LEFT_THUMB_DISTAL,
        "thumb_proximal.R": HumanBoneSpecifications.RIGHT_THUMB_METACARPAL,
        "thumb.proximal.R": HumanBoneSpecifications.RIGHT_THUMB_METACARPAL,
        "thumb_intermediate.R": HumanBoneSpecifications.RIGHT_THUMB_PROXIMAL,
        "thumb.intermediate.R": HumanBoneSpecifications.RIGHT_THUMB_PROXIMAL,
        "thumb_distal.R": HumanBoneSpecifications.RIGHT_THUMB_DISTAL,
        "thumb.distal.R": HumanBoneSpecifications.RIGHT_THUMB_DISTAL,
    },
)
