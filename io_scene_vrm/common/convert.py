from collections import abc
from typing import Any, List, Optional, Tuple


def vrm_json_vector3_to_tuple(
    value: Any,
) -> Optional[Tuple[float, float, float]]:
    if not isinstance(value, dict):
        return None
    x = value.get("x")
    y = value.get("y")
    z = value.get("z")
    if not isinstance(x, (int, float)):
        x = 0
    if not isinstance(y, (int, float)):
        y = 0
    if not isinstance(z, (int, float)):
        z = 0
    return (float(x), float(y), float(z))


def vrm_json_curve_to_list(curve: Any) -> Optional[List[float]]:
    if not isinstance(curve, abc.Iterable):
        return None
    values = [float(v) if isinstance(v, (int, float)) else 0 for v in curve]
    while len(values) < 8:
        values.append(0)
    while len(values) > 8:
        values.pop()
    return values


def vrm_json_array_to_float_vector(json: Any, defaults: List[float]) -> List[float]:
    if not isinstance(json, abc.Iterable):
        return defaults

    input_values = list(json)
    output_values = []
    for index, default in enumerate(defaults):
        if index < len(input_values) and isinstance(input_values[index], (int, float)):
            output_values.append(float(input_values[index]))
        else:
            output_values.append(float(default))

    return output_values


BPY_TRACK_AXIS_TO_VRM_AIM_AXIS = {
    "TRACK_X": "PositiveX",
    "TRACK_Y": "PositiveY",
    "TRACK_Z": "PositiveZ",
    "TRACK_NEGATIVE_X": "NegativeX",
    "TRACK_NEGATIVE_Y": "NegativeY",
    "TRACK_NEGATIVE_Z": "NegativeZ",
}

VRM_AIM_AXIS_TO_BPY_TRACK_AXIS = {
    v: k for k, v in BPY_TRACK_AXIS_TO_VRM_AIM_AXIS.items()
}
