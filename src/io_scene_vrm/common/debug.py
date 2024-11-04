# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import math
from collections.abc import Sequence
from typing import Union

import bpy
from bpy.types import Context
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


def clean_scene(context: Context) -> None:
    if context.view_layer.objects.active:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    while context.blend_data.collections:
        context.blend_data.collections.remove(context.blend_data.collections[0])
    bpy.ops.outliner.orphans_purge(do_recursive=True)
