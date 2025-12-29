# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import math
from collections.abc import Iterator, Mapping, Sequence
from sys import float_info
from typing import Optional, Union

from . import convert_any
from .logger import get_logger

logger = get_logger(__name__)

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
    return convert_any.mapping_to_object_mapping(mapping_object)


def vrm_json_vector3_to_tuple(
    value: Json,
) -> Optional[tuple[float, float, float]]:
    if not isinstance(value, dict):
        return None
    x = float_or(value.get("x"), 0.0)
    y = float_or(value.get("y"), 0.0)
    z = float_or(value.get("z"), 0.0)
    return (x, y, z)


def vrm_json_curve_to_list(curve: Json) -> Optional[list[float]]:
    if not isinstance(curve, list):
        return None
    values: list[float] = [float_or(v, 0.0) for v in curve]
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

        input_value = float_or(input_values[index], default)
        output_values.append(input_value)

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
    return max(0, min(1.0, 1.0 - gi_equalization))


# https://github.com/vrm-c/UniVRM/blob/f3479190c330ec6ecd2b40be919285aa93a53aff/Assets/VRMShaders/VRM10/MToon10/Runtime/MToon10Migrator.cs#L10-L19
def mtoon_shading_toony_0_to_1(
    shading_toony_0x: float, shading_shift_0x: float
) -> float:
    (range_min, range_max) = get_shading_range_0x(shading_toony_0x, shading_shift_0x)
    return max(0, min(1.0, (2.0 - (range_max - range_min)) * 0.5))


# https://github.com/vrm-c/UniVRM/blob/f3479190c330ec6ecd2b40be919285aa93a53aff/Assets/VRMShaders/VRM10/MToon10/Runtime/MToon10Migrator.cs#L21-L30
def mtoon_shading_shift_0_to_1(
    shading_toony_0x: float, shading_shift_0x: float
) -> float:
    (range_min, range_max) = get_shading_range_0x(shading_toony_0x, shading_shift_0x)
    return max(-1, min(1.0, ((range_max + range_min) * 0.5 * -1)))


# https://github.com/vrm-c/UniVRM/blob/f3479190c330ec6ecd2b40be919285aa93a53aff/Assets/VRMShaders/VRM10/MToon10/Runtime/MToon10Migrator.cs#L32-L38
def mtoon_intensity_to_gi_equalization(gi_intensity_0x: float) -> float:
    return max(0, min(1.0, 1.0 - gi_intensity_0x))


# https://github.com/vrm-c/UniVRM/blob/f3479190c330ec6ecd2b40be919285aa93a53aff/Assets/VRMShaders/VRM10/MToon10/Runtime/MToon10Migrator.cs#L40-L46
def get_shading_range_0x(
    shading_toony_0x: float, shading_shift_0x: float
) -> tuple[float, float]:
    range_min = shading_shift_0x
    range_max = (1 - shading_toony_0x) + shading_toony_0x * shading_shift_0x
    return (range_min, range_max)


def float_or_none(
    v: object,
    min_value: float = -float_info.max,
    max_value: float = float_info.max,
) -> Optional[float]:
    if isinstance(v, float):
        if math.isnan(v):
            return None
        return max(min_value, min(v, max_value))

    if isinstance(v, bool):
        return 1.0 if v else 0.0

    if isinstance(v, int):
        return max(min_value, min(float(v), max_value))

    return None


def float_or(
    v: object,
    default: float,
    min_value: float = -float_info.max,
    max_value: float = float_info.max,
) -> float:
    float_or_none_value = float_or_none(v, min_value, max_value)
    if float_or_none_value is not None:
        return float_or_none_value

    if min_value <= default <= max_value:
        return default

    logger.warning(
        "Default float value %s is out of range [%s, %s]", default, min_value, max_value
    )

    return max(min_value, min(default, max_value))


def float4_or_none(value4: object) -> Optional[tuple[float, float, float, float]]:
    value4_iterator = iterator_or_none(value4)
    if value4_iterator is None:
        return None

    result: list[float] = []
    for value in value4_iterator:
        if len(result) == 4:
            return None
        float_value = float_or_none(value)
        if float_value is None:
            return None
        result.append(float_value)
    if len(result) != 4:
        return None
    return (result[0], result[1], result[2], result[3])


def float4_or(
    value4: object, default: tuple[float, float, float, float]
) -> tuple[float, float, float, float]:
    float4 = float4_or_none(value4)
    return float4 if float4 is not None else default


def float3_or_none(value3: object) -> Optional[tuple[float, float, float]]:
    value3_iterator = iterator_or_none(value3)
    if value3_iterator is None:
        return None

    result: list[float] = []
    for value in value3_iterator:
        if len(result) == 3:
            return None
        float_value = float_or_none(value)
        if float_value is None:
            return None
        result.append(float_value)
    if len(result) != 3:
        return None
    return (result[0], result[1], result[2])


def float3_or(
    value3: object, default: tuple[float, float, float]
) -> tuple[float, float, float]:
    float3 = float3_or_none(value3)
    return float3 if float3 is not None else default


def float2_or_none(value2: object) -> Optional[tuple[float, float]]:
    value2_iterator = iterator_or_none(value2)
    if value2_iterator is None:
        return None
    result: list[float] = []
    for value in value2_iterator:
        if len(result) == 2:
            return None
        float_value = float_or_none(value)
        if float_value is None:
            return None
        result.append(float_value)
    if len(result) != 2:
        return None
    return (result[0], result[1])


def float2_or(value2: object, default: tuple[float, float]) -> tuple[float, float]:
    float2 = float2_or_none(value2)
    return float2 if float2 is not None else default


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
