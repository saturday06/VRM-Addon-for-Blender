# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from collections.abc import Mapping, Sequence
from typing import Final

from ..vrm1.expression_preset import ExpressionPreset, ExpressionPresets

VRM1_PRESET_TO_MMD_SHAPE_KEY_MAPPING: Final[
    Mapping[ExpressionPreset, Sequence[Mapping[str, float]]]
] = {
    ExpressionPresets.AA: [
        {"あ": 1.0},
    ],
    ExpressionPresets.IH: [
        {"い": 1.0},
    ],
    ExpressionPresets.OU: [
        {"う": 1.0},
    ],
    ExpressionPresets.EE: [
        {"え": 1.0},
        {"えー": 0.5},
    ],
    ExpressionPresets.OH: [
        {"お": 1.0},
    ],
    ExpressionPresets.BLINK: [
        {"まばたき": 1.0},
    ],
    ExpressionPresets.BLINK_RIGHT: [
        {"ウィンク右": 1.0},
        {"ウィンク２右": 1.0},
        {"ｳｨﾝｸ２右": 1.0},
    ],
    ExpressionPresets.BLINK_LEFT: [
        {"ウィンク": 1.0},
        {"ウィンク２": 1.0},
        {"ｳｨﾝｸ２": 1.0},
    ],
    ExpressionPresets.HAPPY: [
        {"笑い": 1.0},
        {"にこり": 1.0},
    ],
    ExpressionPresets.RELAXED: [
        {"なごみ": 1.0},
    ],
    ExpressionPresets.ANGRY: [
        {"怒り": 1.0},
    ],
    ExpressionPresets.SAD: [
        {"困る": 1.0},
    ],
    ExpressionPresets.SURPRISED: [
        {"びっくり": 1.0},
    ],
    ExpressionPresets.LOOK_UP: [
        {"上": 1.0},
    ],
    ExpressionPresets.LOOK_DOWN: [
        {"下": 1.0},
    ],
}
