import functools
from typing import List

import bpy

from ..common import version
from .extension import VrmAddonArmatureExtensionPropertyGroup
from .property_group import BonePropertyGroup
from .spring_bone1 import migration as spring_bone1_migration
from .vrm0 import migration as vrm0_migration
from .vrm0.property_group import Vrm0HumanoidPropertyGroup


def migrate_no_defer_discarding_return_value(armature_object_name: str) -> None:
    migrate(armature_object_name, defer=False)


def migrate(armature_object_name: str, defer: bool) -> bool:
    armature = bpy.data.objects.get(armature_object_name)
    if (
        not armature
        or not armature.name
        or armature.type != "ARMATURE"
        or not armature.data.name
    ):
        return False

    ext = armature.data.vrm_addon_extension
    if (
        tuple(ext.addon_version) >= version.version()
        and armature.data.name == ext.armature_data_name
        and vrm0_migration.is_unnecessary(ext.vrm0)
    ):
        return True

    if defer:
        bpy.app.timers.register(
            functools.partial(
                migrate_no_defer_discarding_return_value, armature_object_name
            )
        )
        return False

    ext.armature_data_name = armature.data.name

    for bone_property_group in BonePropertyGroup.get_all_bone_property_groups(armature):
        bone_property_group.armature_data_name = armature.data.name

    vrm0_migration.migrate(ext.vrm0, armature)
    spring_bone1_migration.migrate(armature)

    ext.addon_version = version.version()

    setup_subscription(load_post=False)
    return True


def migrate_all_objects() -> None:
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE":
            migrate(obj.name, defer=False)


__object_name_subscription_owner = object()
__bone_name_subscription_owner = object()
__armature_name_subscription_owner = object()
__setup_once: List[bool] = []  # mutableにするためlistを使う


def __on_change_bpy_object_name() -> None:
    for armature in bpy.data.armatures:
        if not hasattr(armature, "vrm_addon_extension") or not isinstance(
            armature.vrm_addon_extension, VrmAddonArmatureExtensionPropertyGroup
        ):
            continue

        # FIXME: Needs optimization!
        for collider in armature.vrm_addon_extension.spring_bone1.colliders:
            collider.broadcast_bpy_object_name()


def __on_change_bpy_bone_name() -> None:
    for armature in bpy.data.armatures:
        if not hasattr(armature, "vrm_addon_extension") or not isinstance(
            armature.vrm_addon_extension, VrmAddonArmatureExtensionPropertyGroup
        ):
            continue

        Vrm0HumanoidPropertyGroup.check_last_bone_names_and_update(
            armature.name, defer=False
        )


def __on_change_bpy_armature_name() -> None:
    migrate_all_objects()


def setup_subscription(load_post: bool) -> None:
    # 本来なら一度しか処理しないが、load_postから呼ばれた場合は強制的に処理する
    if load_post:
        if __setup_once:
            teardown_subscription()
    elif __setup_once:
        return
    __setup_once.append(True)

    object_name_subscribe_to = (bpy.types.Object, "name")
    bpy.msgbus.subscribe_rna(
        key=object_name_subscribe_to,
        owner=__object_name_subscription_owner,
        args=(),
        notify=__on_change_bpy_object_name,
    )

    bone_name_subscribe_to = (bpy.types.Bone, "name")
    bpy.msgbus.subscribe_rna(
        key=bone_name_subscribe_to,
        owner=__bone_name_subscription_owner,
        args=(),
        notify=__on_change_bpy_bone_name,
    )

    armature_name_subscribe_to = (bpy.types.Armature, "name")
    bpy.msgbus.subscribe_rna(
        key=armature_name_subscribe_to,
        owner=__armature_name_subscription_owner,
        args=(),
        notify=__on_change_bpy_armature_name,
    )

    bpy.msgbus.publish_rna(key=object_name_subscribe_to)
    bpy.msgbus.publish_rna(key=bone_name_subscribe_to)
    bpy.msgbus.publish_rna(key=armature_name_subscribe_to)


def teardown_subscription() -> None:
    __setup_once.clear()
    bpy.msgbus.clear_by_owner(__armature_name_subscription_owner)
    bpy.msgbus.clear_by_owner(__bone_name_subscription_owner)
    bpy.msgbus.clear_by_owner(__object_name_subscription_owner)
