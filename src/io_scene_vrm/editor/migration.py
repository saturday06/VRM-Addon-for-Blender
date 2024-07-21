import functools
from dataclasses import dataclass
from typing import Final, Optional

import bpy
from bpy.types import Armature, Context

from ..common import ops
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


@dataclass
class State:
    blend_file_compatibility_warning_shown: bool = False
    blend_file_addon_compatibility_warning_shown: bool = False


state: Final = State()


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
    context: Context,
    *,
    skip_non_migrated_armatures: bool = False,
    show_progress: bool = False,
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
    mtoon1_migration.migrate(context, show_progress=show_progress)
    validate_blend_file_compatibility(context)
    validate_blend_file_addon_compatibility(context)

    preferences = get_preferences(context)

    updated_addon_version = addon_version()
    logger.debug(
        "Upgrade preferences %s to %s",
        tuple(preferences.addon_version),
        updated_addon_version,
    )
    preferences.addon_version = updated_addon_version


def validate_blend_file_compatibility(context: Context) -> None:
    """新しいBlenderで作成されたファイルを古いBlenderで編集しようとした場合に警告をする.

    アドオンの対応バージョンの事情で新しいBlenderで編集されたファイルを古いBlenderで編集しようとし、
    それによりシェイプキーが壊れるなどの報告がよく上がる。警告を出すことでユーザーに注意を促す。
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
        # Blender 4.2.0ではtimerで実行しないとダイアログが自動で消えるのでタイマーを使う
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
    """新しいVRMアドオンで作成されたファイルを古いVRMアドオンで編集しようとした場合に警告をする."""
    if not context.blend_data.filepath:
        return
    installed_addon_version = addon_version()

    # TODO: これはSceneあたりにバージョンを生やしたほうが良いかも
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
        # Blender 4.2.0ではtimerで実行しないとダイアログが自動で消えるのでタイマーを使う
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
    for obj in context.blend_data.objects:
        if obj.type != "ARMATURE":
            continue
        armature = obj.data
        if not isinstance(armature, Armature):
            continue

        # https://github.com/saturday06/VRM-Addon-for-Blender/blob/2_0_3/io_scene_vrm/editor/migration.py#L372-L373
        ext = get_armature_extension(armature)
        if tuple(ext.addon_version) > (2, 0, 1):
            return True

        # https://github.com/saturday06/VRM-Addon-for-Blender/blob/0_79/importer/model_build.py#L731
        humanoid_params_key = obj.get("humanoid_params")
        if not isinstance(humanoid_params_key, str):
            continue
        # https://github.com/saturday06/VRM-Addon-for-Blender/blob/0_79/importer/model_build.py#L723-L726
        if not humanoid_params_key.startswith(".json"):
            continue

        return True
    return False


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
