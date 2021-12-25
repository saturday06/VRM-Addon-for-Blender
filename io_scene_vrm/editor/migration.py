import functools

import bpy

from ..common import version
from .property_group import BonePropertyGroup
from .vrm0 import migration as vrm0_migration


def migrate(armature: bpy.types.Object, defer: bool) -> None:
    if not armature or not armature.name or not armature.data.name:
        return

    ext = armature.data.vrm_addon_extension
    if (
        tuple(ext.addon_version) >= version.version()
        and armature.data.name == ext.armature_data_name
        and vrm0_migration.is_unnecessary(ext.vrm0)
    ):
        return

    if defer:
        bpy.app.timers.register(functools.partial(migrate, armature, False))
        return

    for bone_property_group in BonePropertyGroup.get_all_bone_property_groups(armature):
        bone_property_group.refresh(armature)

    vrm0_migration.migrate(ext.vrm0, armature)

    ext.addon_version = version.version()
    ext.armature_data_name = armature.data.name
