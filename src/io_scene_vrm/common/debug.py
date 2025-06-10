# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import math
from collections.abc import Sequence
from typing import Union

from mathutils import Matrix, Quaternion, Vector


def dump(v: Union[Matrix, Vector, Quaternion, float]) -> str:
    if isinstance(v, (float, int)):
        return str(v)

    if isinstance(v, Matrix):
        t, r, s = v.decompose()
        return f"Matrix(T={dump(t)},R={dump(r)},S={dump(s)})"

    if isinstance(v, Vector):
        return f"({v.x:.3f},{v.y:.3f},{v.z:.3f})"

    x, y, z = (round(math.degrees(xyz)) for xyz in v.to_euler()[:])
    return f"Euler({x},{y},{z})"


def assert_vector3_equals(
    expected: Vector, actual: Sequence[float], message: str
) -> None:
    if len(actual) != 3:
        message = f"actual length is not 3: {actual}"
        raise AssertionError(message)

    threshold = 0.0001
    if abs(expected[0] - actual[0]) > threshold:
        message = f"{message}: {tuple(expected)} is different from {tuple(actual)}"
        raise AssertionError(message)
    if abs(expected[1] - actual[1]) > threshold:
        message = f"{message}: {tuple(expected)} is different from {tuple(actual)}"
        raise AssertionError(message)
    if abs(expected[2] - actual[2]) > threshold:
        message = f"{message}: {tuple(expected)} is different from {tuple(actual)}"
        raise AssertionError(message)


def cleanse_modules() -> None:
    """Search for your plugin modules in blender python sys.modules and remove them.

    To support reload properly, try to access a package var, if it's there,
    reload everything.

    This function may cause errors that are difficult to investigate. Please use with
    caution. See also:
    https://github.com/saturday06/VRM-Addon-for-Blender/issues/506#issuecomment-2183766778
    """
    import sys

    all_modules = sys.modules
    all_modules = dict(sorted(all_modules.items(), key=lambda x: x[0]))  # sort them

    for k in all_modules:
        if k == __name__ or k.startswith(__name__ + "."):
            del sys.modules[k]
