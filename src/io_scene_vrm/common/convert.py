# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import math
from collections.abc import Iterator, Mapping, Sequence
from sys import float_info
from typing import Optional, Union

from . import convert_any

Json = Union[
    None,
    bool,
    int,
    float,
    str,
    list["Json"],
    dict[str, "Json"],
]


def iterator_or_none(v: object) -> Optional[Iterator[object]]:
    try:
        # "isinstance(v, Iterable)" doesn't work.
        # https://github.com/python/cpython/blob/3.9/Doc/library/collections.abc.rst?plain=1#L126-L127
        iterator = iter(v)  # type: ignore[call-overload]
    except TypeError:
        return None
    return convert_any.iterator_to_object_iterator(iterator)


def sequence_or_none(
    sequence_object: object,
) -> Optional[Sequence[object]]:
    sequence = sequence_object
    if not isinstance(sequence, Sequence):
        return None
    iterator = iterator_or_none(sequence_object)
    if iterator is None:
        return None
    return list(iterator)


def mapping_or_none(
    mapping_object: object,
) -> Optional[Mapping[object, object]]:
    mapping = mapping_object
    if not isinstance(mapping, Mapping):
        return None
    key_iterator = iterator_or_none(mapping_object)
    if key_iterator is None:
        return None
    return {key: convert_any.to_object(mapping[key]) for key in key_iterator}


def vrm_json_vector3_to_tuple(
    value: Json,
) -> Optional[tuple[float, float, float]]:
    if not isinstance(value, Mapping):
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


def vrm_json_curve_to_list(curve: Json) -> Optional[list[float]]:
    if not isinstance(curve, list):
        return None
    values = [float(v) if isinstance(v, (int, float)) else 0 for v in curve]
    while len(values) < 8:
        values.append(0)
    while len(values) > 8:
        values.pop()
    return values


def vrm_json_array_to_float_vector(
    input_values: Json, defaults: list[float]
) -> list[float]:
    if not isinstance(input_values, list):
        return defaults

    output_values: list[float] = []
    for index, default in enumerate(defaults):
        if index >= len(input_values):
            output_values.append(default)
            continue

        input_value = input_values[index]
        if not isinstance(input_value, (int, float)):
            output_values.append(default)
            continue

        output_values.append(float(input_value))

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


def mtoon_shading_toony_1_to_0(shading_toony: float, shading_shift: float) -> float:
    base = 2 - shading_toony + shading_shift
    if abs(base) < float_info.epsilon:
        # https://github.com/Santarh/MToon/blob/43f02fe8c9b19c3cf9f3238003b7d8b332933833/MToon/Resources/Shaders/MToon.shader#L17
        return 0.9
    return max(0, min((shading_toony + shading_shift) / base, 1))


def mtoon_shading_shift_1_to_0(shading_toony: float, shading_shift: float) -> float:
    return max(-1, min(shading_toony - shading_shift - 1, 1))


def mtoon_gi_equalization_to_intensity(gi_equalization: float) -> float:
    return max(0, min(1, 1 - gi_equalization))


# https://github.com/vrm-c/UniVRM/blob/f3479190c330ec6ecd2b40be919285aa93a53aff/Assets/VRMShaders/VRM10/MToon10/Runtime/MToon10Migrator.cs#L10-L19
def mtoon_shading_toony_0_to_1(
    shading_toony_0x: float, shading_shift_0x: float
) -> float:
    (range_min, range_max) = get_shading_range_0x(shading_toony_0x, shading_shift_0x)
    return max(0, min(1, (2 - (range_max - range_min)) * 0.5))


# https://github.com/vrm-c/UniVRM/blob/f3479190c330ec6ecd2b40be919285aa93a53aff/Assets/VRMShaders/VRM10/MToon10/Runtime/MToon10Migrator.cs#L21-L30
def mtoon_shading_shift_0_to_1(
    shading_toony_0x: float, shading_shift_0x: float
) -> float:
    (range_min, range_max) = get_shading_range_0x(shading_toony_0x, shading_shift_0x)
    return max(-1, min(1, ((range_max + range_min) * 0.5 * -1)))


# https://github.com/vrm-c/UniVRM/blob/f3479190c330ec6ecd2b40be919285aa93a53aff/Assets/VRMShaders/VRM10/MToon10/Runtime/MToon10Migrator.cs#L32-L38
def mtoon_intensity_to_gi_equalization(gi_intensity_0x: float) -> float:
    return max(0, min(1, 1 - gi_intensity_0x))


# https://github.com/vrm-c/UniVRM/blob/f3479190c330ec6ecd2b40be919285aa93a53aff/Assets/VRMShaders/VRM10/MToon10/Runtime/MToon10Migrator.cs#L40-L46
def get_shading_range_0x(
    shading_toony_0x: float, shading_shift_0x: float
) -> tuple[float, float]:
    range_min = shading_shift_0x
    range_max = (1 - shading_toony_0x) + shading_toony_0x * shading_shift_0x
    return (range_min, range_max)


def float_or_none(v: object) -> Optional[float]:
    if isinstance(v, int):
        return float(v)
    if isinstance(v, float):
        return v
    return None


def float_or(v: object, default: float) -> float:
    if isinstance(v, int):
        return float(v)
    if isinstance(v, float):
        return v
    return default


def float4_or_none(v: object) -> Optional[tuple[float, float, float, float]]:
    iterator = iterator_or_none(v)
    if iterator is None:
        return None

    result: list[float] = []
    for x in iterator:
        if len(result) == 4:
            return None
        if isinstance(x, float):
            result.append(x)
        elif isinstance(x, int):
            result.append(float(x))
        else:
            return None
    if len(result) != 4:
        return None
    return (result[0], result[1], result[2], result[3])


def float4_or(
    v: object, default: tuple[float, float, float, float]
) -> tuple[float, float, float, float]:
    return float4_or_none(v) or default


def float3_or_none(v: object) -> Optional[tuple[float, float, float]]:
    iterator = iterator_or_none(v)
    if iterator is None:
        return None

    result: list[float] = []
    for x in iterator:
        if len(result) == 3:
            return None
        if isinstance(x, float):
            result.append(x)
        elif isinstance(x, int):
            result.append(float(x))
        else:
            return None
    if len(result) != 3:
        return None
    return (result[0], result[1], result[2])


def float3_or(
    v: object, default: tuple[float, float, float]
) -> tuple[float, float, float]:
    return float3_or_none(v) or default


def float2_or_none(v: object) -> Optional[tuple[float, float]]:
    iterator = iterator_or_none(v)
    if iterator is None:
        return None
    result: list[float] = []
    for x in iterator:
        if len(result) == 2:
            return None
        if isinstance(x, float):
            result.append(x)
        elif isinstance(x, int):
            result.append(float(x))
        else:
            return None
    if len(result) != 2:
        return None
    return (result[0], result[1])


def float2_or(v: object, default: tuple[float, float]) -> tuple[float, float]:
    return float2_or_none(v) or default


def str_or(v: object, default: str) -> str:
    if isinstance(v, str):
        return v
    return default


def axis_blender_to_gltf(vector3: Sequence[float]) -> tuple[float, float, float]:
    return (
        -vector3[0],
        vector3[2],
        vector3[1],
    )


def linear_to_srgb(
    non_color: Sequence[float],
) -> Sequence[float]:
    return [
        math.pow(channel_value, 1.0 / 2.2) if channel_index < 3 else channel_value
        for channel_index, channel_value in enumerate(non_color)
    ]


def srgb_to_linear(
    srgb_color: Sequence[float],
) -> Sequence[float]:
    return [
        math.pow(channel_value, 2.2) if channel_index < 3 else channel_value
        for channel_index, channel_value in enumerate(srgb_color)
    ]
