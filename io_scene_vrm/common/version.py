from typing import Tuple

import bpy

MAX_SUPPORTED_BLENDER_MAJOR_MINOR_VERSION = (3, 2)


# To avoid circular reference
def version() -> Tuple[int, int, int]:
    v = __import__(".".join(__name__.split(".")[:-2])).bl_info.get("version")
    if (
        not isinstance(v, tuple)
        or len(v) != 3
        or not isinstance(v[0], int)
        or not isinstance(v[1], int)
        or not isinstance(v[2], int)
    ):
        raise Exception(f"{v} is not valid type")
    return (v[0], v[1], v[2])


def supported() -> bool:
    return bool(bpy.app.version[:2] <= MAX_SUPPORTED_BLENDER_MAJOR_MINOR_VERSION)
