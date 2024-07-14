import platform
from dataclasses import dataclass
from importlib import import_module
from sys import float_info
from typing import Optional

import bpy
from bpy.app.translations import pgettext

from . import convert
from .blender_manifest import BlenderManifest
from .logging import get_logger

logger = get_logger(__name__)


@dataclass
class Cache:
    use: bool
    last_blender_restart_required: bool
    last_blender_manifest_modification_time: float
    initial_blender_manifest_content: bytes


cache = Cache(
    use=False,
    last_blender_restart_required=False,
    last_blender_manifest_modification_time=0.0,
    initial_blender_manifest_content=BlenderManifest.default_blender_manifest_path().read_bytes(),
)


def clear_addon_version_cache() -> Optional[float]:
    cache.use = False
    return None


def trigger_clear_addon_version_cache() -> None:
    if bpy.app.timers.is_registered(clear_addon_version_cache):
        return
    bpy.app.timers.register(clear_addon_version_cache, first_interval=0.5)


def max_supported_blender_major_minor_version() -> Optional[tuple[int, int]]:
    blender_version_max = BlenderManifest.read().blender_version_max
    if blender_version_max is None:
        return None
    return (blender_version_max[0], blender_version_max[1])


def addon_version() -> tuple[int, int, int]:
    return BlenderManifest.read().version


def blender_restart_required() -> bool:
    if not legacy_addon():
        # Blender Extensions Platform correctly reloads extensions
        return False

    if cache.use:
        return cache.last_blender_restart_required

    cache.use = True

    if cache.last_blender_restart_required:
        return True

    blender_manifest_path = BlenderManifest.default_blender_manifest_path()
    blender_manifest_modification_time = blender_manifest_path.stat().st_mtime
    if (
        abs(
            cache.last_blender_manifest_modification_time
            - blender_manifest_modification_time
        )
        < float_info.epsilon
    ):
        return False

    cache.last_blender_manifest_modification_time = blender_manifest_modification_time

    blender_manifest_content = blender_manifest_path.read_bytes()
    if blender_manifest_content == cache.initial_blender_manifest_content:
        return False

    cache.last_blender_restart_required = True
    return True


def legacy_addon() -> bool:
    root_module = import_module(".".join(__name__.split(".")[:-2]))
    bl_info = convert.mapping_or_none(getattr(root_module, "bl_info", None))
    if bl_info is None:
        return False

    return (
        bl_info.get("name"),
        bl_info.get("location"),
    ) == (
        # https://github.com/saturday06/VRM-Addon-for-Blender/blob/2_20_49/src/io_scene_vrm/__init__.py#L15
        "VRM format",
        # https://github.com/saturday06/VRM-Addon-for-Blender/blob/2_20_49/src/io_scene_vrm/__init__.py#L18
        "File > Import-Export",
    )


def stable_release() -> bool:
    if (  # for Blender Extensions Platform
        not legacy_addon()
        and bpy.app.version == (4, 2, 0)
        and bpy.app.version_cycle == "rc"
    ):
        return True

    if bpy.app.version_cycle == "release":
        return True

    # Microsoft Store distributes RC versions of 3.3.11 and 3.6.3 as
    # release versions.
    return platform.system() == "Windows" and bpy.app.version_cycle == "rc"


def supported() -> bool:
    v = max_supported_blender_major_minor_version()
    if v is None:
        return True
    return bpy.app.version[:2] <= v


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
