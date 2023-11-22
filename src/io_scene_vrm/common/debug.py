import math
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
