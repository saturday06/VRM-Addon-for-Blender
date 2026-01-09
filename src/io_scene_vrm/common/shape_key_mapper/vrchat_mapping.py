# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from collections.abc import Mapping, Sequence
from typing import Final

from ..vrm1.expression_preset import ExpressionPreset, ExpressionPresets

VRM1_PRESET_TO_VRCHAT_SHAPE_KEY_MAPPING: Final[
    Mapping[ExpressionPreset, Sequence[Mapping[str, float]]]
] = {
    ExpressionPresets.AA: [{"vrc.v_aa": 1.0}],
    ExpressionPresets.EE: [{"vrc.v_e": 1.0}],
    ExpressionPresets.IH: [{"vrc.v_ih": 1.0}],
    ExpressionPresets.OH: [{"vrc.v_oh": 1.0}],
    ExpressionPresets.OU: [{"vrc.v_ou": 1.0}],
    ExpressionPresets.BLINK: [{"Blink": 1.0}],
}
