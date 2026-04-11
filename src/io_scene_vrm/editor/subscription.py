# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from dataclasses import dataclass
from typing import Final

import bpy
from bpy.types import Armature, Bone, Object

from ..common.logger import get_logger
from .extension import VrmAddonArmatureExtensionPropertyGroup
from .extension_accessor import get_armature_extension
from .migration import migrate_all_objects
from .mtoon1.property_group import refresh_mtoon1_outline_object
from .vrm0 import property_group as vrm0_property_group
from .vrm1 import property_group as vrm1_property_group

_logger = get_logger(__name__)


@dataclass
class Subscription:
    object_mode_subscription_owner = object()
    object_location_subscription_owner = object()
    bone_name_subscription_owner = object()
    armature_name_subscription_owner = object()
    setup_once: bool = False


_subscription: Final = Subscription()


def setup_subscription(*, load_post: bool) -> None:
    if _subscription.setup_once:
        if load_post:
            # If called by load_post, unsubscribe and setup again.
            teardown_subscription()
        else:
            # If a subscription is already setup, do nothing.
            return

    _subscription.setup_once = True

    object_mode_subscribe_to = (Object, "mode")
    bpy.msgbus.subscribe_rna(
        key=object_mode_subscribe_to,
        owner=_subscription.object_mode_subscription_owner,
        args=(),
        notify=on_change_bpy_object_mode,
    )

    object_location_subscribe_to = (Object, "location")
    bpy.msgbus.subscribe_rna(
        key=object_location_subscribe_to,
        owner=_subscription.object_location_subscription_owner,
        args=(),
        notify=on_change_bpy_object_location,
    )

    bone_name_subscribe_to = (Bone, "name")
    bpy.msgbus.subscribe_rna(
        key=bone_name_subscribe_to,
        owner=_subscription.bone_name_subscription_owner,
        args=(),
        notify=on_change_bpy_bone_name,
    )

    armature_name_subscribe_to = (Armature, "name")
    bpy.msgbus.subscribe_rna(
        key=armature_name_subscribe_to,
        owner=_subscription.armature_name_subscription_owner,
        args=(),
        notify=on_change_bpy_armature_name,
    )

    bpy.msgbus.publish_rna(key=object_mode_subscribe_to)
    bpy.msgbus.publish_rna(key=object_location_subscribe_to)
    bpy.msgbus.publish_rna(key=bone_name_subscribe_to)
    bpy.msgbus.publish_rna(key=armature_name_subscribe_to)


def teardown_subscription() -> None:
    _subscription.setup_once = False
    bpy.msgbus.clear_by_owner(_subscription.armature_name_subscription_owner)
    bpy.msgbus.clear_by_owner(_subscription.bone_name_subscription_owner)
    bpy.msgbus.clear_by_owner(_subscription.object_location_subscription_owner)
    bpy.msgbus.clear_by_owner(_subscription.object_mode_subscription_owner)


def on_change_bpy_object_mode() -> None:
    context = bpy.context

    active_object = context.active_object
    if not active_object:
        return
    refresh_mtoon1_outline_object(context, active_object)


def on_change_bpy_object_location() -> None:
    context = bpy.context
    active_object = context.active_object
    if not active_object:
        return
    vrm1_property_group.Vrm1LookAtPropertyGroup.update_all_previews(context)


def on_change_bpy_bone_name() -> None:
    context = bpy.context

    for armature in context.blend_data.armatures:
        ext = get_armature_extension(armature)
        if (
            tuple(ext.addon_version)
            == VrmAddonArmatureExtensionPropertyGroup.INITIAL_ADDON_VERSION
        ):
            continue

        vrm0_property_group.Vrm0HumanoidPropertyGroup.update_all_bone_name_candidates(
            context, armature.name
        )
        vrm1_property_group.Vrm1HumanBonesPropertyGroup.update_all_bone_name_candidates(
            context, armature.name
        )


def on_change_bpy_armature_name() -> None:
    context = bpy.context

    migrate_all_objects(context, heavy_migration=False)
