import functools
from dataclasses import dataclass
from typing import Optional

import bpy
from bpy.types import Armature, Bone, Context, Object

from ..common.logging import get_logger
from ..common.preferences import get_preferences
from ..common.version import addon_version
from .extension import (
    VrmAddonArmatureExtensionPropertyGroup,
    VrmAddonSceneExtensionPropertyGroup,
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
    ext = armature_data.vrm_addon_extension
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

    ext = armature_data.vrm_addon_extension
    ext.armature_data_name = armature_data.name

    for bone_property_group in BonePropertyGroup.get_all_bone_property_groups(armature):
        bone_property_group.armature_data_name = armature_data.name

    vrm0_migration.migrate(context, ext.vrm0, armature)
    vrm1_migration.migrate(context, ext.vrm1, armature)
    spring_bone1_migration.migrate(context, armature)

    updated_addon_version = addon_version()
    logger.info(
        f"Upgrade armature {armature_object_name}"
        + f" {tuple(ext.addon_version)} to {updated_addon_version}"
    )
    ext.addon_version = updated_addon_version

    setup_subscription(load_post=False)
    return True


def migrate_all_objects(
    context: Context, skip_non_migrated_armatures: bool = False
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
        "Upgrade preferences"
        + f" {tuple(preferences.addon_version)} to {updated_addon_version}"
    )
    preferences.addon_version = updated_addon_version


@dataclass
class Subscription:
    object_name_subscription_owner = object()
    object_mode_subscription_owner = object()
    object_location_subscription_owner = object()
    bone_name_subscription_owner = object()
    armature_name_subscription_owner = object()
    setup_once: bool = False


subscription = Subscription()


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


def setup_subscription(*, load_post: bool) -> None:
    if subscription.setup_once:
        if load_post:
            # If called by load_post, unsubscribe and setup again.
            teardown_subscription()
        else:
            # If a subscription is already setup, do nothing.
            return

    subscription.setup_once = True

    object_name_subscribe_to = (Object, "name")
    bpy.msgbus.subscribe_rna(
        key=object_name_subscribe_to,
        owner=subscription.object_name_subscription_owner,
        args=(),
        notify=on_change_bpy_object_name,
    )

    object_mode_subscribe_to = (Object, "mode")
    bpy.msgbus.subscribe_rna(
        key=object_mode_subscribe_to,
        owner=subscription.object_mode_subscription_owner,
        args=(),
        notify=on_change_bpy_object_mode,
    )

    object_location_subscribe_to = (Object, "location")
    bpy.msgbus.subscribe_rna(
        key=object_location_subscribe_to,
        owner=subscription.object_location_subscription_owner,
        args=(),
        notify=on_change_bpy_object_location,
    )

    bone_name_subscribe_to = (Bone, "name")
    bpy.msgbus.subscribe_rna(
        key=bone_name_subscribe_to,
        owner=subscription.bone_name_subscription_owner,
        args=(),
        notify=on_change_bpy_bone_name,
    )

    armature_name_subscribe_to = (Armature, "name")
    bpy.msgbus.subscribe_rna(
        key=armature_name_subscribe_to,
        owner=subscription.armature_name_subscription_owner,
        args=(),
        notify=on_change_bpy_armature_name,
    )

    bpy.msgbus.publish_rna(key=object_name_subscribe_to)
    bpy.msgbus.publish_rna(key=object_mode_subscribe_to)
    bpy.msgbus.publish_rna(key=object_location_subscribe_to)
    bpy.msgbus.publish_rna(key=bone_name_subscribe_to)
    bpy.msgbus.publish_rna(key=armature_name_subscribe_to)


def teardown_subscription() -> None:
    subscription.setup_once = False
    bpy.msgbus.clear_by_owner(subscription.armature_name_subscription_owner)
    bpy.msgbus.clear_by_owner(subscription.bone_name_subscription_owner)
    bpy.msgbus.clear_by_owner(subscription.object_location_subscription_owner)
    bpy.msgbus.clear_by_owner(subscription.object_mode_subscription_owner)
    bpy.msgbus.clear_by_owner(subscription.object_name_subscription_owner)
