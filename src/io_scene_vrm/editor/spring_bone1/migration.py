# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from bpy.types import Armature, Context, Object

from ..extension_accessor import get_armature_extension
from .ops import assign_spring_bone1_from_vrm0
from .property_group import SpringBone1SpringBonePropertyGroup


def migrate_blender_object(armature: Armature) -> None:
    ext = get_armature_extension(armature)
    if tuple(ext.addon_version) >= (2, 3, 27):
        return

    for collider in ext.spring_bone1.colliders:
        bpy_object = collider.pop("blender_object", None)
        if isinstance(bpy_object, Object):
            collider.bpy_object = bpy_object


def fixup_gravity_dir(armature: Armature) -> None:
    ext = get_armature_extension(armature)

    if tuple(ext.addon_version) <= (2, 14, 3):
        for spring in ext.spring_bone1.springs:
            for joint in spring.joints:
                joint.gravity_dir = [
                    joint.gravity_dir[0],
                    joint.gravity_dir[2],
                    joint.gravity_dir[1],
                ]

    if tuple(ext.addon_version) <= (2, 14, 10):
        for spring in ext.spring_bone1.springs:
            for joint in spring.joints:
                joint.gravity_dir = [
                    joint.gravity_dir[0],
                    -joint.gravity_dir[1],
                    joint.gravity_dir[2],
                ]

    if tuple(ext.addon_version) <= (2, 15, 3):
        for spring in ext.spring_bone1.springs:
            for joint in spring.joints:
                gravity_dir = list(joint.gravity_dir)
                joint.gravity_dir = (gravity_dir[0] + 1, 0, 0)  # Make a change
                joint.gravity_dir = gravity_dir


def fixup_collider_group_name(armature: Armature) -> None:
    ext = get_armature_extension(armature)
    if tuple(ext.addon_version) <= (2, 20, 38):
        spring_bone = get_armature_extension(armature).spring_bone1
        for collider_group in spring_bone.collider_groups:
            collider_group.fix_index()


def is_unnecessary(spring_bone1: SpringBone1SpringBonePropertyGroup) -> bool:
    return not spring_bone1.initial_automatic_spring_bone_assignment


def migrate(context: Context, armature: Object) -> None:
    armature_data = armature.data
    if not isinstance(armature_data, Armature):
        return
    migrate_blender_object(armature_data)
    fixup_gravity_dir(armature_data)
    fixup_collider_group_name(armature_data)

    ext = get_armature_extension(armature_data)
    spring_bone1 = ext.spring_bone1

    if (
        tuple(ext.addon_version) < (3, 21, 2)
        and tuple(ext.addon_version) != ext.INITIAL_ADDON_VERSION
    ):
        spring_bone1.initial_automatic_spring_bone_assignment = False

    if spring_bone1.initial_automatic_spring_bone_assignment:
        spring_bone1.initial_automatic_spring_bone_assignment = False
        assign_spring_bone1_from_vrm0(context, armature.name)
