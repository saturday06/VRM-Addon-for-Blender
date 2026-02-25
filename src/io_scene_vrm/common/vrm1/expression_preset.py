# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from dataclasses import dataclass
from typing import Final

VRM0_PRESET_UNKNOWN: Final[str] = "unknown"


@dataclass(frozen=True)
class ExpressionPreset:
    name: str
    icon: str
    mouth: bool
    blink: bool
    look_at: bool
    vrm0_preset: str

    @classmethod
    def create(
        cls,
        expression_preset_generator: list["ExpressionPreset"],
        *,
        name: str,
        icon: str,
        mouth: bool,
        blink: bool,
        look_at: bool,
        vrm0_preset: str,
    ) -> "ExpressionPreset":
        instance = cls(
            name=name,
            icon=icon,
            mouth=mouth,
            blink=blink,
            look_at=look_at,
            vrm0_preset=vrm0_preset,
        )
        expression_preset_generator.append(instance)
        return instance


class ExpressionPresets:
    __expression_preset_generator: Final[list[ExpressionPreset]] = []

    HAPPY: Final[ExpressionPreset] = ExpressionPreset.create(
        __expression_preset_generator,
        name="happy",
        icon="HEART",
        mouth=False,
        blink=False,
        look_at=False,
        vrm0_preset="joy",
    )
    ANGRY: Final[ExpressionPreset] = ExpressionPreset.create(
        __expression_preset_generator,
        name="angry",
        icon="ORPHAN_DATA",
        mouth=False,
        blink=False,
        look_at=False,
        vrm0_preset="angry",
    )
    SAD: Final[ExpressionPreset] = ExpressionPreset.create(
        __expression_preset_generator,
        name="sad",
        icon="MOD_FLUIDSIM",
        mouth=False,
        blink=False,
        look_at=False,
        vrm0_preset="sorrow",
    )
    RELAXED: Final[ExpressionPreset] = ExpressionPreset.create(
        __expression_preset_generator,
        name="relaxed",
        icon="LIGHT_SUN",
        mouth=False,
        blink=False,
        look_at=False,
        vrm0_preset="fun",
    )
    SURPRISED: Final[ExpressionPreset] = ExpressionPreset.create(
        __expression_preset_generator,
        name="surprised",
        icon="LIGHT_SUN",
        mouth=False,
        blink=False,
        look_at=False,
        vrm0_preset=VRM0_PRESET_UNKNOWN,
    )
    NEUTRAL: Final[ExpressionPreset] = ExpressionPreset.create(
        __expression_preset_generator,
        name="neutral",
        icon="VIEW_ORTHO",
        mouth=False,
        blink=False,
        look_at=False,
        vrm0_preset="neutral",
    )
    AA: Final[ExpressionPreset] = ExpressionPreset.create(
        __expression_preset_generator,
        name="aa",
        icon="EVENT_A",
        mouth=True,
        blink=False,
        look_at=False,
        vrm0_preset="a",
    )
    IH: Final[ExpressionPreset] = ExpressionPreset.create(
        __expression_preset_generator,
        name="ih",
        icon="EVENT_I",
        mouth=True,
        blink=False,
        look_at=False,
        vrm0_preset="i",
    )
    OU: Final[ExpressionPreset] = ExpressionPreset.create(
        __expression_preset_generator,
        name="ou",
        icon="EVENT_U",
        mouth=True,
        blink=False,
        look_at=False,
        vrm0_preset="u",
    )
    EE: Final[ExpressionPreset] = ExpressionPreset.create(
        __expression_preset_generator,
        name="ee",
        icon="EVENT_E",
        mouth=True,
        blink=False,
        look_at=False,
        vrm0_preset="e",
    )
    OH: Final[ExpressionPreset] = ExpressionPreset.create(
        __expression_preset_generator,
        name="oh",
        icon="EVENT_O",
        mouth=True,
        blink=False,
        look_at=False,
        vrm0_preset="o",
    )
    BLINK: Final[ExpressionPreset] = ExpressionPreset.create(
        __expression_preset_generator,
        name="blink",
        icon="HIDE_ON",
        mouth=False,
        blink=True,
        look_at=False,
        vrm0_preset="blink",
    )
    BLINK_LEFT: Final[ExpressionPreset] = ExpressionPreset.create(
        __expression_preset_generator,
        name="blinkLeft",
        icon="HIDE_ON",
        mouth=False,
        blink=True,
        look_at=False,
        vrm0_preset="blink_l",
    )
    BLINK_RIGHT: Final[ExpressionPreset] = ExpressionPreset.create(
        __expression_preset_generator,
        name="blinkRight",
        icon="HIDE_ON",
        mouth=False,
        blink=True,
        look_at=False,
        vrm0_preset="blink_r",
    )
    LOOK_UP: Final[ExpressionPreset] = ExpressionPreset.create(
        __expression_preset_generator,
        name="lookUp",
        icon="ANCHOR_TOP",
        mouth=False,
        blink=False,
        look_at=True,
        vrm0_preset="lookup",
    )
    LOOK_DOWN: Final[ExpressionPreset] = ExpressionPreset.create(
        __expression_preset_generator,
        name="lookDown",
        icon="ANCHOR_BOTTOM",
        mouth=False,
        blink=False,
        look_at=True,
        vrm0_preset="lookdown",
    )
    LOOK_LEFT: Final[ExpressionPreset] = ExpressionPreset.create(
        __expression_preset_generator,
        name="lookLeft",
        icon="ANCHOR_RIGHT",
        mouth=False,
        blink=False,
        look_at=True,
        vrm0_preset="lookleft",
    )
    LOOK_RIGHT: Final[ExpressionPreset] = ExpressionPreset.create(
        __expression_preset_generator,
        name="lookRight",
        icon="ANCHOR_LEFT",
        mouth=False,
        blink=False,
        look_at=True,
        vrm0_preset="lookright",
    )

    all: Final[tuple[ExpressionPreset, ...]] = tuple(__expression_preset_generator)
