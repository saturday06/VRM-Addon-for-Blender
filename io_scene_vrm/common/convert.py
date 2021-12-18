import collections
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
    return (x, y, z)


def vrm_json_curve_to_list(curve: Any) -> Optional[List[float]]:
    if not isinstance(curve, collections.Iterable):
        return None
    values = [v if isinstance(v, (int, float)) else 0 for v in curve]
    while len(values) < 8:
        values.append(0)
    while len(values) > 8:
        values.pop()
    return values
