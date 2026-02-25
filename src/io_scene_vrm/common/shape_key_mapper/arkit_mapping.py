# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from collections.abc import Mapping, Sequence
from typing import Final

from ..vrm1.expression_preset import (
    ExpressionPreset,
    ExpressionPresets,
)

ARKIT_SHAPE_KEYS: Final[tuple[str, ...]] = (
    # https://developer.apple.com/documentation/arkit/arfaceanchor/blendshapelocation
    "eyeBlinkLeft",
    "eyeLookDownLeft",
    "eyeLookInLeft",
    "eyeLookOutLeft",
    "eyeLookUpLeft",
    "eyeSquintLeft",
    "eyeWideLeft",
    "eyeBlinkRight",
    "eyeLookDownRight",
    "eyeLookInRight",
    "eyeLookOutRight",
    "eyeLookUpRight",
    "eyeSquintRight",
    "eyeWideRight",
    "jawForward",
    "jawLeft",
    "jawRight",
    "jawOpen",
    "mouthClose",
    "mouthFunnel",
    "mouthPucker",
    "mouthLeft",
    "mouthRight",
    "mouthSmileLeft",
    "mouthSmileRight",
    "mouthFrownLeft",
    "mouthFrownRight",
    "mouthDimpleLeft",
    "mouthDimpleRight",
    "mouthStretchLeft",
    "mouthStretchRight",
    "mouthRollLower",
    "mouthRollUpper",
    "mouthShrugLower",
    "mouthShrugUpper",
    "mouthPressLeft",
    "mouthPressRight",
    "mouthLowerDownLeft",
    "mouthLowerDownRight",
    "mouthUpperUpLeft",
    "mouthUpperUpRight",
    "browDownLeft",
    "browDownRight",
    "browInnerUp",
    "browOuterUpLeft",
    "browOuterUpRight",
    "cheekPuff",
    "cheekSquintLeft",
    "cheekSquintRight",
    "noseSneerLeft",
    "noseSneerRight",
    "tongueOut",
)


VRM1_PRESET_TO_ARKIT_SHAPE_KEY_MAPPING: Final[
    Mapping[ExpressionPreset, Sequence[Mapping[str, float]]]
] = {
    ExpressionPresets.HAPPY: [
        {
            "mouthSmileLeft": 0.5,
            "mouthSmileRight": 0.5,
        }
    ],
    ExpressionPresets.ANGRY: [
        {
            "mouthFrownLeft": 0.5,
            "mouthFrownRight": 0.5,
        }
    ],
    ExpressionPresets.SAD: [
        {
            "browDownLeft": 0.25,
            "browDownRight": 0.25,
        }
    ],
    ExpressionPresets.SURPRISED: [
        {
            "browInnerUp": 0.25,
            "browOuterUpLeft": 0.25,
            "browOuterUpRight": 0.25,
            "jawOpen": 0.25,
        }
    ],
    ExpressionPresets.AA: [
        {
            "jawOpen": 0.5,
        }
    ],
    ExpressionPresets.IH: [
        {
            "jawOpen": 0.2,
            "mouthStretchLeft": 0.2,
            "mouthStretchRight": 0.2,
        }
    ],
    ExpressionPresets.OU: [
        {
            "jawOpen": 0.2,
            "mouthPucker": 0.2,
        }
    ],
    ExpressionPresets.EE: [
        {
            "jawOpen": 0.3,
            "mouthStretchLeft": 0.3,
            "mouthStretchRight": 0.3,
        }
    ],
    ExpressionPresets.OH: [
        {
            "jawOpen": 0.3,
            "mouthPucker": 0.3,
        }
    ],
    ExpressionPresets.BLINK: [
        {
            "eyeBlinkLeft": 1.0,
            "eyeBlinkRight": 1.0,
        }
    ],
    ExpressionPresets.BLINK_LEFT: [
        {
            "eyeBlinkLeft": 1.0,
        }
    ],
    ExpressionPresets.BLINK_RIGHT: [
        {
            "eyeBlinkRight": 1.0,
        }
    ],
    ExpressionPresets.LOOK_UP: [
        {
            "eyeLookUpLeft": 1.0,
            "eyeLookUpRight": 1.0,
        }
    ],
    ExpressionPresets.LOOK_DOWN: [
        {
            "eyeLookDownLeft": 1.0,
            "eyeLookDownRight": 1.0,
        }
    ],
    ExpressionPresets.LOOK_LEFT: [
        {
            "eyeLookOutLeft": 1.0,
            "eyeLookInRight": 1.0,
        }
    ],
    ExpressionPresets.LOOK_RIGHT: [
        {
            "eyeLookInLeft": 1.0,
            "eyeLookOutRight": 1.0,
        }
    ],
}
