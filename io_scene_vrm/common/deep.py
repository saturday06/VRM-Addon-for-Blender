import math
from collections import abc
from typing import Dict, List, Union

from .logging import get_logger

logger = get_logger(__name__)

Json = Union[
    None,
    bool,
    int,
    float,
    str,
    List["Json"],
    Dict[str, "Json"],
]


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
    if isinstance(v, abc.Mapping):
        result: Dict[str, Json] = {}
        for key, value in v.items():
            if isinstance(key, str):
                result[key] = make_json(value)
                continue
            logger.warning(f"{key} {type(key)} is unrecognized type for dict key")
        return result
    if isinstance(v, abc.Iterable):
        return [make_json(x) for x in v]

    logger.warning(f"{v} {type(v)} is unrecognized type")
    return None


def get(
    json: Json,
    attrs: List[Union[int, str]],
    default: Json = None,
) -> Json:
    if json is None:
        return default

    attr = attrs.pop(0)

    if isinstance(json, list) and isinstance(attr, int) and 0 <= attr < len(json):
        if not attrs:
            return json[attr]
        return get(json[attr], attrs, default)

    if isinstance(json, dict) and isinstance(attr, str) and attr in json:
        if not attrs:
            return json[attr]
        return get(json[attr], attrs, default)

    return default


def get_list(
    json: Json,
    attrs: List[Union[int, str]],
    default: List[Json],
) -> List[Json]:
    result = get(json, attrs, default)
    return result if isinstance(result, list) else default


def diff(
    left: Json,
    right: Json,
    float_tolerance: float = 0,
    path: str = "",
) -> List[str]:
    if isinstance(left, list):
        if not isinstance(right, list):
            return [f"{path}: left is list but right is {type(right)}"]
        if len(left) != len(right):
            return [
                f"{path}: left length is {len(left)} but right length is {len(right)}"
            ]
        diffs = []
        for i, (l, r) in enumerate(zip(left, right)):
            diffs.extend(diff(l, r, float_tolerance, f"{path}[{i}]"))
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
                f"{path}: left is {float(left):20.17f} but right is {float(right):20.17f}, error={error:19.17f}"
            ]
        return []

    raise ValueError(f"{path}: unexpected type left={type(left)} right={type(right)}")
