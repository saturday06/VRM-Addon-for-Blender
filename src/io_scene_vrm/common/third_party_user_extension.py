# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import inspect
import sys
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType
from typing import Optional

import bpy
from bpy.types import Context

from . import convert
from .logger import get_logger

_logger = get_logger(__name__)


def get_third_party_user_extension_name(module: ModuleType) -> Optional[str]:
    module_name = module.__name__
    module_init_path_str = getattr(module, "__file__", None)
    if not isinstance(module_init_path_str, str):
        _logger.warning(
            "Module %s does not have a valid __file__ attribute",
            module_name,
        )
        return None
    if not module_init_path_str:
        _logger.warning(
            "Module %s has an empty __file__ attribute",
            module_name,
        )
        return None
    module_init_path = Path(module_init_path_str)
    if not module_init_path.exists():
        _logger.warning("Module init path %s does not exist", module_init_path)
        return None
    module_root_path = module_init_path.parent
    if not module_root_path.is_dir():
        _logger.warning("Module root path %s is not a directory", module_root_path)
        return None

    if (
        bpy.app.version >= (4, 2)
        and (
            blender_manifest_path := module_root_path / "blender_manifest.toml"
        ).exists()
        and sys.version_info >= (3, 11)
    ):
        import tomllib

        try:
            blender_manifest_str = blender_manifest_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            _logger.exception(
                "Failed to read blender_manifest.toml for module %s",
                module_name,
            )
            return None
        try:
            blender_manifest = tomllib.loads(blender_manifest_str)
        except tomllib.TOMLDecodeError:
            _logger.warning(
                "Failed to parse blender_manifest.toml for module %s",
                module_name,
            )
            return None
        blender_manifest_name = blender_manifest.get("name")
        if not isinstance(blender_manifest_name, str) or not blender_manifest_name:
            _logger.warning(
                "Module %s has a blender_manifest.toml without a valid name",
                module_name,
            )
            return None
        blender_manifest_version = blender_manifest.get("version")
        if (
            not isinstance(blender_manifest_version, str)
            or not blender_manifest_version
        ):
            _logger.warning(
                "Module %s has a blender_manifest.toml without a valid version",
                module_name,
            )
            return None
        return blender_manifest_name + " " + blender_manifest_version

    bl_info = convert.mapping_or_none(getattr(module, "bl_info", None))
    if not bl_info:
        _logger.warning(
            "Module %s does not have a valid bl_info dictionary",
            module_name,
        )
        return None

    bl_info_name = bl_info.get("name")
    if not isinstance(bl_info_name, str):
        bl_info_name = module_name

    bl_info_version = convert.sequence_or_none(bl_info.get("version"))
    if not bl_info_version:
        bl_info_version = ("no-version",)

    return (
        bl_info_name
        + " "
        + ".".join(str(version_element) for version_element in bl_info_version)
    )


def collect_third_party_user_extensions(
    context: Context, user_extension_class_name: str
) -> list[tuple[str, object]]:
    user_extensions: list[tuple[str, object]] = []
    preferences = context.preferences
    for addon_name in preferences.addons.keys():
        addon_module = sys.modules.get(addon_name)
        if addon_module is None:
            continue
        user_extension_name = get_third_party_user_extension_name(addon_module)
        if user_extension_name is None:
            continue
        user_extension_type = getattr(addon_module, user_extension_class_name, None)
        if not isinstance(user_extension_type, type):
            continue
        try:
            user_extension: object = user_extension_type()
        except Exception:
            _logger.exception(
                "Failed to instantiate %s from addon '%s'",
                user_extension_class_name,
                addon_name,
            )
            continue
        user_extensions.append((user_extension_name, user_extension))
    return user_extensions


def trigger_third_party_user_extension_hook(
    user_extensions: Sequence[object], method_name: str, *args: object
) -> None:
    for user_extension in user_extensions:
        method = getattr(user_extension, method_name, None)
        if not callable(method):
            continue

        try:
            parameters = tuple(inspect.signature(method).parameters.values())
        except (TypeError, ValueError):
            # Some callables implemented outside Python don't expose a signature.
            method_args = args
        else:
            if any(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                and parameter.default is inspect.Parameter.empty
                for parameter in parameters
            ):
                _logger.error(
                    "Failed to call %s of %s from addon '%s': "
                    "the callback has keyword-only arguments without defaults",
                    method_name,
                    user_extension.__class__.__name__,
                    user_extension.__class__.__module__,
                )
                continue

            min_arg_count = sum(
                1
                for parameter in parameters
                if parameter.default is inspect.Parameter.empty
                and parameter.kind
                in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                )
            )
            if len(args) < min_arg_count:
                _logger.error(
                    "Failed to call %s of %s from addon '%s': "
                    "the callback requires %d argument%s, but only %d %s available",
                    method_name,
                    user_extension.__class__.__name__,
                    user_extension.__class__.__module__,
                    min_arg_count,
                    "" if min_arg_count == 1 else "s",
                    len(args),
                    "is" if len(args) == 1 else "are",
                )
                continue

            max_arg_count = sum(
                1
                for parameter in parameters
                if parameter.kind
                in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                )
            )
            if any(
                parameter.kind is inspect.Parameter.VAR_POSITIONAL
                for parameter in parameters
            ):
                method_args = args
            else:
                method_args = args[:max_arg_count]

        try:
            method(*method_args)
        except Exception:
            _logger.exception(
                "Failed to call %s of %s from addon '%s'",
                method_name,
                user_extension.__class__.__name__,
                user_extension.__class__.__module__,
            )
