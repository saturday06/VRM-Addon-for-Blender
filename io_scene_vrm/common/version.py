from typing import Tuple

import bpy

MAX_SUPPORTED_BLENDER_MAJOR_MINOR_VERSION = (3, 4)


def addon_version() -> Tuple[int, int, int]:
    # To avoid circular reference call __import__() in the function local scope.
    v = __import__(".".join(__name__.split(".")[:-2])).bl_info.get("version")
    if (
        not isinstance(v, tuple)
        or len(v) != 3
        or not isinstance(v[0], int)
        or not isinstance(v[1], int)
        or not isinstance(v[2], int)
    ):
        raise AssertionError(f"{v} is not valid type but {type(v)}")
    return (v[0], v[1], v[2])


def supported() -> bool:
    return bool(bpy.app.version[:2] <= MAX_SUPPORTED_BLENDER_MAJOR_MINOR_VERSION)
