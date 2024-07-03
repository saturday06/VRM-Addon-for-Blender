import functools
from typing import Optional

import bpy
from bpy.types import Armature, Context

from ..common.logging import get_logger
from ..common.preferences import get_preferences
from ..common.version import addon_version
from .extension import (
    VrmAddonArmatureExtensionPropertyGroup,
    VrmAddonSceneExtensionPropertyGroup,
    get_armature_extension,
)
from .mtoon1 import migration as mtoon1_migration
from .mtoon1 import ops as mtoon1_ops
from .property_group import BonePropertyGroup
from .spring_bone1 import migration as spring_bone1_migration
from .vrm0 import migration as vrm0_migration
from .vrm0.property_group import Vrm0HumanoidPropertyGroup
from .vrm1 import migration as vrm1_migration
from .vrm1 import property_group as vrm1_property_group

logger = get_logger(__name__)


def is_unnecessary(armature_data: Armature) -> bool:
    ext = get_armature_extension(armature_data)
    return (
        tuple(ext.addon_version) >= addon_version()
        and armature_data.name == ext.armature_data_name
        and vrm0_migration.is_unnecessary(ext.vrm0)
    )


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
    """migrate()の型をbpy.app.timers.registerに合わせるためのラッパー."""
    context = bpy.context  # Contextはフレームを跨げないので新たに取得する
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
    ext.armature_data_name = armature_data.name

    for bone_property_group in BonePropertyGroup.get_all_bone_property_groups(armature):
        bone_property_group.armature_data_name = armature_data.name

    vrm0_migration.migrate(context, ext.vrm0, armature)
    vrm1_migration.migrate(context, ext.vrm1, armature)
    spring_bone1_migration.migrate(context, armature)

    updated_addon_version = addon_version()
    logger.info(
        "Upgrade armature %s %s to %s",
        armature_object_name,
        tuple(ext.addon_version),
        updated_addon_version,
    )
    ext.addon_version = updated_addon_version
    return True


def migrate_all_objects(
    context: Context, *, skip_non_migrated_armatures: bool = False
) -> None:
    for obj in context.blend_data.objects:
        if obj.type == "ARMATURE":
            if skip_non_migrated_armatures:
                ext = getattr(obj.data, "vrm_addon_extension", None)
                if not isinstance(ext, VrmAddonArmatureExtensionPropertyGroup):
                    continue
                if (
                    tuple(ext.addon_version)
                    == VrmAddonArmatureExtensionPropertyGroup.INITIAL_ADDON_VERSION
                ):
                    continue
            migrate(context, obj.name)

    VrmAddonSceneExtensionPropertyGroup.update_vrm0_material_property_names(
        context, context.scene.name
    )
    mtoon1_migration.migrate(context)

    preferences = get_preferences(context)

    updated_addon_version = addon_version()
    logger.debug(
        "Upgrade preferences %s to %s",
        tuple(preferences.addon_version),
        updated_addon_version,
    )
    preferences.addon_version = updated_addon_version


def on_change_bpy_object_name() -> None:
    context = bpy.context

    for armature in context.blend_data.armatures:
        ext = getattr(armature, "vrm_addon_extension", None)
        if not isinstance(ext, VrmAddonArmatureExtensionPropertyGroup):
            continue
        if (
            tuple(ext.addon_version)
            == VrmAddonArmatureExtensionPropertyGroup.INITIAL_ADDON_VERSION
        ):
            continue

        # TODO: Needs optimization!
        for collider in ext.spring_bone1.colliders:
            collider.broadcast_bpy_object_name(context)


def on_change_bpy_object_mode() -> None:
    context = bpy.context

    active_object = context.active_object
    if not active_object:
        return
    mtoon1_ops.VRM_OT_refresh_mtoon1_outline.refresh_object(context, active_object)


def on_change_bpy_object_location() -> None:
    context = bpy.context
    active_object = context.active_object
    if not active_object:
        return
    vrm1_property_group.Vrm1LookAtPropertyGroup.update_all_previews(context)


def on_change_bpy_bone_name() -> None:
    context = bpy.context

    for armature in context.blend_data.armatures:
        ext = getattr(armature, "vrm_addon_extension", None)
        if not isinstance(ext, VrmAddonArmatureExtensionPropertyGroup):
            continue
        if (
            tuple(ext.addon_version)
            == VrmAddonArmatureExtensionPropertyGroup.INITIAL_ADDON_VERSION
        ):
            continue

        Vrm0HumanoidPropertyGroup.update_all_node_candidates(context, armature.name)


def on_change_bpy_armature_name() -> None:
    context = bpy.context

    migrate_all_objects(context, skip_non_migrated_armatures=True)
