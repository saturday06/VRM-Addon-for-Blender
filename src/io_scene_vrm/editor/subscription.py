# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from dataclasses import dataclass

import bpy
from bpy.types import Armature, Bone, Object

from ..common.logger import get_logger
from .migration import (
    on_change_bpy_armature_name,
    on_change_bpy_bone_name,
    on_change_bpy_object_location,
    on_change_bpy_object_mode,
    on_change_bpy_object_name,
)

logger = get_logger(__name__)


@dataclass
class Subscription:
    object_name_subscription_owner = object()
    object_mode_subscription_owner = object()
    object_location_subscription_owner = object()
    bone_name_subscription_owner = object()
    armature_name_subscription_owner = object()
    setup_once: bool = False


subscription = Subscription()


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
