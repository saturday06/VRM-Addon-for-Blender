# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import difflib
import math
from json import dumps as json_dumps

from . import convert
from .convert import Json
from .logger import get_logger

logger = get_logger(__name__)


def make_json(v: object) -> Json:
    if v is None:
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return v
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v

    mapping = convert.mapping_or_none(v)
    if mapping is not None:
        dict_result: dict[str, Json] = {}
        for key, value in mapping.items():
            if isinstance(key, str):
                dict_result[key] = make_json(value)
                continue
            logger.warning("%s %s is unrecognized type for dict key", key, type(key))
        return dict_result

    iterator = convert.iterator_or_none(v)
    if iterator is not None:
        return [make_json(x) for x in iterator]

    logger.warning("%s %s is unrecognized type", v, type(v))
    return None


def diff(
    left: Json,
    right: Json,
    float_tolerance: float = 0,
    path: str = "",
) -> list[str]:
    if isinstance(left, list):
        if not isinstance(right, list):
            return [f"{path}: left is list but right is {type(right)}"]
        if len(left) != len(right):
            result = [
                f"{path}: left length is {len(left)} but right length is {len(right)}"
            ]
            left_json_str = json_dumps(left, indent=4, sort_keys=True)
            right_json_str = json_dumps(right, indent=4, sort_keys=True)
            unified_diff = [
                line.rstrip()
                for line in difflib.unified_diff(
                    right_json_str.splitlines(keepends=True),
                    left_json_str.splitlines(keepends=True),
                    f"{path}/right",
                    f"{path}/left",
                )
            ]
            if len(unified_diff) > 1000:
                return result
            return result + unified_diff
        diffs: list[str] = []
        for i, (left_child, right_child) in enumerate(zip(left, right)):
            diffs.extend(diff(left_child, right_child, float_tolerance, f"{path}[{i}]"))
        return diffs

    if isinstance(left, dict):
        if not isinstance(right, dict):
            return [f"{path}: left is dict but right is {type(right)}"]
        diffs = []
        for key in sorted(set(list(left.keys()) + list(right.keys()))):
            if key not in left:
                diffs.append(f'{path}: {key} not in left. right["{key}"]={right[key]}')
                continue
            if key not in right:
                diffs.append(f'{path}: {key} not in right, left["{key}"]={left[key]}')
                continue
            diffs.extend(
                diff(left[key], right[key], float_tolerance, f'{path}["{key}"]')
            )
        return diffs

    if isinstance(left, bool):
        if not isinstance(right, bool):
            return [f"{path}: left is bool but right is {type(right)}"]
        if left != right:
            return [f"{path}: left is {left} but right is {right}"]
        return []

    if isinstance(left, str):
        if not isinstance(right, str):
            return [f"{path}: left is str but right is {type(right)}"]
        if left != right:
            return [f'{path}: left is "{left}" but right is "{right}"']
        return []

    if left is None and right is not None:
        return [f"{path}: left is None but right is {type(right)}"]

    if isinstance(left, int) and isinstance(right, int):
        if left != right:
            return [f"{path}: left is {left} but right is {right}"]
        return []

    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        error = math.fabs(float(left) - float(right))
        if error > float_tolerance:
            return [
                f"{path}: left is {float(left):20.17f}"
                + f" but right is {float(right):20.17f}, error={error:19.17f}"
            ]
        return []

    message = f"{path}: unexpected type left={type(left)} right={type(right)}"
    raise ValueError(message)
