# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import functools
from dataclasses import dataclass
from typing import Final, Optional

import bpy
from bpy.types import Armature, Context

from ..common import ops
from ..common.logger import get_logger
from ..common.preferences import get_preferences
from ..common.version import get_addon_version
from .extension import (
    VrmAddonArmatureExtensionPropertyGroup,
    VrmAddonSceneExtensionPropertyGroup,
    get_armature_extension,
)
from .mtoon1 import migration as mtoon1_migration
from .spring_bone1 import migration as spring_bone1_migration
from .vrm0 import migration as vrm0_migration
from .vrm1 import migration as vrm1_migration

logger = get_logger(__name__)


@dataclass
class State:
    blend_file_compatibility_warning_shown: bool = False
    blend_file_addon_compatibility_warning_shown: bool = False


state: Final = State()


def is_unnecessary(armature_data: Armature) -> bool:
    ext = get_armature_extension(armature_data)
    return tuple(
        ext.addon_version
    ) >= get_addon_version() and vrm0_migration.is_unnecessary(ext.vrm0)


def defer_migrate(armature_object_name: str) -> bool:
    context = bpy.context

    armature = context.blend_data.objects.get(armature_object_name)
    if not armature:
        return False
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return False
    if is_unnecessary(armature_data):
        return True
    bpy.app.timers.register(
        functools.partial(
            migrate_timer_callback,
            armature_object_name,
        )
    )
    return False


def migrate_timer_callback(armature_object_name: str) -> None:
    """Match the type of migrate() to bpy.app.timers.register."""
    context = bpy.context  # Context cannot span frames, so get it anew
    migrate(context, armature_object_name)


def migrate(context: Optional[Context], armature_object_name: str) -> bool:
    if context is None:
        context = bpy.context

    armature = context.blend_data.objects.get(armature_object_name)
    if not armature:
        return False
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return False

    if is_unnecessary(armature_data):
        return True

    ext = get_armature_extension(armature_data)

    vrm0_migration.migrate(context, ext.vrm0, armature)
    vrm1_migration.migrate(context, ext.vrm1, armature)
    spring_bone1_migration.migrate(context, armature)

    if (
        ext.has_vrm_model_metadata(armature)
        and tuple(ext.addon_version) < (3, 14, 0)
        and not ext.get("spec_version")
    ):
        ext.spec_version = ext.SPEC_VERSION_VRM0

    updated_addon_version = get_addon_version()
    logger.info(
        "Upgrade armature %s %s to %s",
        armature_object_name,
        tuple(ext.addon_version),
        updated_addon_version,
    )
    ext.addon_version = updated_addon_version
    return True


def migrate_all_objects(
    context: Context,
    *,
    skip_non_migrated_armatures: bool = False,
    show_progress: bool = False,
) -> None:
    for obj in context.blend_data.objects:
        if obj.type == "ARMATURE" and isinstance(armature_data := obj.data, Armature):
            if skip_non_migrated_armatures:
                ext = get_armature_extension(armature_data)
                if (
                    tuple(ext.addon_version)
                    == VrmAddonArmatureExtensionPropertyGroup.INITIAL_ADDON_VERSION
                ):
                    continue
            migrate(context, obj.name)

    VrmAddonSceneExtensionPropertyGroup.update_vrm0_material_property_names(
        context, context.scene.name
    )
    mtoon1_migration.migrate(context, show_progress=show_progress)
    validate_blend_file_compatibility(context)
    validate_blend_file_addon_compatibility(context)

    preferences = get_preferences(context)

    updated_addon_version = get_addon_version()
    if tuple(preferences.addon_version) != updated_addon_version:
        logger.debug(
            "Upgrade preferences %s to %s",
            tuple(preferences.addon_version),
            updated_addon_version,
        )

    if tuple(preferences.addon_version) != preferences.INITIAL_ADDON_VERSION and tuple(
        preferences.addon_version
    ) < (2, 34, 0):
        preferences.enable_advanced_preferences = True
        preferences.export_gltf_animations = True

    preferences.addon_version = updated_addon_version


def validate_blend_file_compatibility(context: Context) -> None:
    """Warn when attempting to edit a file created in newer Blender with older Blender.

    Due to add-on version support issues, there are often reports of users trying to
    edit files created in newer Blender with older Blender, which can cause shape keys
    to break. This warning alerts users to be careful.
    """
    if not context.blend_data.filepath:
        return
    if not have_vrm_model(context):
        return

    blend_file_major_minor_version = (
        context.blend_data.version[0],
        context.blend_data.version[1],
    )
    current_major_minor_version = (bpy.app.version[0], bpy.app.version[1])
    if blend_file_major_minor_version <= current_major_minor_version:
        return

    file_version_str = ".".join(map(str, blend_file_major_minor_version))
    app_version_str = ".".join(map(str, current_major_minor_version))

    logger.error(
        "Opening incompatible file: file_blender_version=%s running_blender_version=%s",
        file_version_str,
        app_version_str,
    )

    if not state.blend_file_compatibility_warning_shown:
        state.blend_file_compatibility_warning_shown = True
        # Use timer because dialog disappears automatically if not executed with
        # timer in Blender 4.2.0
        bpy.app.timers.register(
            functools.partial(
                show_blend_file_compatibility_warning,
                file_version_str,
                app_version_str,
            ),
            first_interval=0.1,
        )


def show_blend_file_compatibility_warning(file_version: str, app_version: str) -> None:
    ops.vrm.show_blend_file_compatibility_warning(
        "INVOKE_DEFAULT",
        file_version=file_version,
        app_version=app_version,
    )


def validate_blend_file_addon_compatibility(context: Context) -> None:
    """Warn when attempting to edit a file created with a newer VRM add-on.

    This warning is for files using an older VRM add-on.
    """
    if not context.blend_data.filepath:
        return
    installed_addon_version = get_addon_version()

    # TODO: It might be better to store the version in Scene or similar
    up_to_date = True
    file_addon_version: tuple[int, ...] = (0, 0, 0)
    for armature in context.blend_data.armatures:
        file_addon_version = tuple(get_armature_extension(armature).addon_version)
        if file_addon_version > installed_addon_version:
            up_to_date = False
            break
    if up_to_date:
        return

    file_addon_version_str = ".".join(map(str, file_addon_version))
    installed_addon_version_str = ".".join(map(str, installed_addon_version))

    logger.error(
        "Opening incompatible VRM add-on version: file=%s installed=%s",
        file_addon_version_str,
        installed_addon_version_str,
    )

    if not state.blend_file_compatibility_warning_shown:
        state.blend_file_compatibility_warning_shown = True
        # Use timer because dialog disappears automatically if not executed with
        # timer in Blender 4.2.0
        bpy.app.timers.register(
            functools.partial(
                show_blend_file_addon_compatibility_warning,
                file_addon_version_str,
                installed_addon_version_str,
            ),
            first_interval=0.1,
        )


def show_blend_file_addon_compatibility_warning(
    file_addon_version: str, installed_addon_version: str
) -> None:
    ops.vrm.show_blend_file_addon_compatibility_warning(
        "INVOKE_DEFAULT",
        file_addon_version=file_addon_version,
        installed_addon_version=installed_addon_version,
    )


def have_vrm_model(context: Context) -> bool:
    return any(
        map(
            VrmAddonArmatureExtensionPropertyGroup.has_vrm_model_metadata,
            context.blend_data.objects,
        )
    )
