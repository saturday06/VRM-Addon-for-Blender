from dataclasses import dataclass
from importlib.util import module_from_spec, spec_from_file_location
from os.path import getmtime
from pathlib import Path
from sys import float_info
from typing import Optional

import bpy

from .logging import get_logger

logger = get_logger(__name__)

MAX_SUPPORTED_BLENDER_MAJOR_MINOR_VERSION = (3, 6)


@dataclass
class Cache:
    use: bool
    last_blender_restart_required: bool
    last_root_init_py_modification_time: float


cache = Cache(
    use=False,
    last_blender_restart_required=False,
    last_root_init_py_modification_time=0.0,
)


def clear_addon_version_cache() -> Optional[float]:  # pylint: disable=useless-return
    cache.use = False
    return None


def trigger_clear_addon_version_cache() -> None:
    if bpy.app.timers.is_registered(clear_addon_version_cache):
        return
    bpy.app.timers.register(clear_addon_version_cache, first_interval=0.5)


def addon_version() -> tuple[int, int, int]:
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
    if cache.use:
        return cache.last_blender_restart_required

    cache.use = True

    if cache.last_blender_restart_required:
        return True

    root_init_py_path = Path(__file__).parent.parent / "__init__.py"
    root_init_py_modification_time = getmtime(root_init_py_path)
    if (
        abs(cache.last_root_init_py_modification_time - root_init_py_modification_time)
        < float_info.epsilon
    ):
        return False

    cache.last_root_init_py_modification_time = root_init_py_modification_time

    spec = spec_from_file_location(
        "blender_vrm_addon_root_init_py_version_checking",
        root_init_py_path,
    )
    if spec is None:
        return False
    mod = module_from_spec(spec)
    if spec.loader is None:
        return False
    spec.loader.exec_module(mod)

    bl_info = getattr(mod, "bl_info", None)
    if not isinstance(bl_info, dict):
        return False
    bl_info_version = bl_info.get("version")
    if bl_info_version == addon_version():
        return False

    cache.last_blender_restart_required = True
    return True


def supported() -> bool:
    return bool(bpy.app.version[:2] <= MAX_SUPPORTED_BLENDER_MAJOR_MINOR_VERSION)
