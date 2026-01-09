# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from collections.abc import Mapping, Sequence
from typing import Final

from ..vrm1.expression_preset import ExpressionPreset, ExpressionPresets

VRM1_PRESET_TO_READY_PLAYER_ME_SHAPE_KEY_MAPPING: Final[
    Mapping[ExpressionPreset, Sequence[Mapping[str, float]]]
] = {
    # https://docs.readyplayer.me/ready-player-me/api-reference/avatars/morph-targets/oculus-ovr-libsync
    ExpressionPresets.AA: [
        {"viseme_aa": 1.0},
    ],
    ExpressionPresets.IH: [
        {"viseme_I": 1.0},
    ],
    ExpressionPresets.OU: [
        {"viseme_U": 1.0},
    ],
    ExpressionPresets.EE: [
        {"viseme_E": 1.0},
    ],
    ExpressionPresets.OH: [
        {"viseme_O": 1.0},
    ],
    # https://docs.readyplayer.me/ready-player-me/api-reference/avatars/morph-targets/apple-arkit
    ExpressionPresets.BLINK: [
        {"eyesClosed": 1.0},
    ],
    ExpressionPresets.BLINK_LEFT: [
        {"eyeBlinkLeft": 1},
    ],
    ExpressionPresets.BLINK_RIGHT: [
        {"eyeBlinkRight": 1},
    ],
    ExpressionPresets.LOOK_UP: [
        {"eyeLookUp": 0.75},
    ],
    ExpressionPresets.LOOK_DOWN: [
        {"eyesLookDown": 0.75},
    ],
    ExpressionPresets.RELAXED: [
        {"browInnerUp": 0.5},
    ],
    ExpressionPresets.HAPPY: [
        {"mouthSmile": 0.5},
    ],
    ExpressionPresets.SAD: [
        {"mouthFrown": 0.5},
    ],
}
