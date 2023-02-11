import importlib
from os.path import getmtime
from pathlib import Path
from sys import float_info
from typing import List, Tuple

import bpy

from .logging import get_logger

logger = get_logger(__name__)

MAX_SUPPORTED_BLENDER_MAJOR_MINOR_VERSION = (3, 4)

last_blender_restart_required: List[bool] = []  # Mutable
last_root_init_py_modification_time: List[float] = []  # Mutable


def clear_addon_version_cache() -> None:
    last_blender_restart_required.clear()
    last_root_init_py_modification_time.clear()


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


def blender_restart_required() -> bool:
    if last_blender_restart_required:
        return last_blender_restart_required[0]

    last_blender_restart_required.clear()
    last_blender_restart_required.append(False)

    root_init_py_path = Path(__file__).parent.parent / "__init__.py"
    root_init_py_modification_time = getmtime(root_init_py_path)
    if (
        last_root_init_py_modification_time
        and abs(last_root_init_py_modification_time[0] - root_init_py_modification_time)
        < float_info.epsilon
    ):
        return last_blender_restart_required[0]
    last_root_init_py_modification_time.clear()
    last_root_init_py_modification_time.append(root_init_py_modification_time)

    spec = importlib.util.spec_from_file_location(
        "blender_vrm_addon_root_init_py_version_checking",
        root_init_py_path,
    )
    if spec is None:
        logger.warning("Failed to create module spec")
        return last_blender_restart_required[0]
    mod = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        logger.warning("Failed to create module spec loader")
        return last_blender_restart_required[0]
    spec.loader.exec_module(mod)

    bl_info = getattr(mod, "bl_info", None)
    if not isinstance(bl_info, dict):
        return last_blender_restart_required[0]
    bl_info_version = bl_info.get("version")
    if bl_info_version == addon_version():
        return last_blender_restart_required[0]

    last_blender_restart_required.clear()
    last_blender_restart_required.append(True)
    return last_blender_restart_required[0]


def supported() -> bool:
    return bool(bpy.app.version[:2] <= MAX_SUPPORTED_BLENDER_MAJOR_MINOR_VERSION)
