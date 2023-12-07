from dataclasses import dataclass
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from sys import float_info
from typing import Optional

import bpy
from bpy.app.translations import pgettext

from .logging import get_logger

logger = get_logger(__name__)

MAX_SUPPORTED_BLENDER_MAJOR_MINOR_VERSION = (4, 0)


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
        message = f"{v} is not valid type but {type(v)}"
        raise AssertionError(message)
    return (v[0], v[1], v[2])


def blender_restart_required() -> bool:
    if cache.use:
        return cache.last_blender_restart_required

    cache.use = True

    if cache.last_blender_restart_required:
        return True

    root_init_py_path = Path(__file__).parent.parent / "__init__.py"
    root_init_py_modification_time = Path(root_init_py_path).stat().st_mtime
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


def stable_release() -> bool:
    return bpy.app.version_cycle in [
        "release",
        "rc",  # Windowsストアは3.3.11や3.6.3をRC版のままリリースしている
    ]


def supported() -> bool:
    return bpy.app.version[:2] <= MAX_SUPPORTED_BLENDER_MAJOR_MINOR_VERSION


def preferences_warning_message() -> Optional[str]:
    if blender_restart_required():
        return pgettext(
            "The VRM add-on has been updated."
            + " Please restart Blender to apply the changes."
        )
    if not stable_release():
        return pgettext(
            "VRM add-on is not compatible with Blender {blender_version_cycle}."
        ).format(blender_version_cycle=bpy.app.version_cycle.capitalize())
    if not supported():
        return pgettext(
            "The installed VRM add-on is not compatible with Blender {blender_version}."
            + " Please upgrade the add-on.",
        ).format(blender_version=".".join(map(str, bpy.app.version[:2])))
    return None


def panel_warning_message() -> Optional[str]:
    if blender_restart_required():
        return pgettext(
            "The VRM add-on has been\n"
            + "updated. Please restart Blender\n"
            + "to apply the changes."
        )
    if not stable_release():
        return pgettext(
            "VRM add-on is\n"
            + "not compatible with\n"
            + "Blender {blender_version_cycle}."
        ).format(blender_version_cycle=bpy.app.version_cycle.capitalize())
    if not supported():
        return pgettext(
            "The installed VRM add-\n"
            + "on is not compatible with\n"
            + "Blender {blender_version}. Please update."
        ).format(blender_version=".".join(map(str, bpy.app.version[:2])))
    return None


def validation_warning_message() -> Optional[str]:
    if blender_restart_required():
        return pgettext(
            "The VRM add-on has been updated."
            + " Please restart Blender to apply the changes."
        )
    if not stable_release():
        return pgettext(
            "VRM add-on is not compatible with Blender {blender_version_cycle}."
            + " The VRM may not be exported correctly.",
        ).format(blender_version_cycle=bpy.app.version_cycle.capitalize())
    if not supported():
        return pgettext(
            "The installed VRM add-on is not compatible with Blender {blender_version}."
            + " The VRM may not be exported correctly."
        ).format(blender_version=".".join(map(str, bpy.app.version)))
    return None
