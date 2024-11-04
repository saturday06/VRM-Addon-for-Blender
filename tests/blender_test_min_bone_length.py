# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from sys import float_info

import bpy
from bpy.types import Armature, Context
from mathutils import Vector

from io_scene_vrm.editor.make_armature import MIN_BONE_LENGTH


def test(context: Context) -> None:
    if context.view_layer.objects.active:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    while context.blend_data.collections:
        context.blend_data.collections.remove(context.blend_data.collections[0])

    bpy.ops.object.add(type="ARMATURE", location=(0, 0, 0))
    armature = context.object
    if not armature or not isinstance(armature.data, Armature):
        raise AssertionError

    bpy.ops.object.mode_set(mode="EDIT")
    zero_length_bone = armature.data.edit_bones.new("ZeroLengthBone")
    zero_length_bone.head = Vector((0, 0, 0))
    zero_length_bone.tail = Vector((0, 0, 0))
    bpy.ops.object.mode_set(mode="OBJECT")
    assert len(armature.data.bones) == 0

    bpy.ops.object.mode_set(mode="EDIT")
    bone = armature.data.edit_bones.new("Bone")
    bone.head = Vector((0, 0, 0))
    bone.tail = Vector((0, 0, MIN_BONE_LENGTH))
    bpy.ops.object.mode_set(mode="OBJECT")
    assert len(armature.data.bones) == 1

    bpy.ops.object.mode_set(mode="EDIT")
    too_short_bone_length = MIN_BONE_LENGTH / 10
    too_short_bone = armature.data.edit_bones.new("TooShortBone")
    too_short_bone.head = Vector((0, 0, 0))
    too_short_bone.tail = Vector((0, 0, too_short_bone_length))
    bpy.ops.object.mode_set(mode="OBJECT")
    assert too_short_bone_length > float_info.epsilon
    assert len(armature.data.bones) == 1


if __name__ == "__main__":
    test(bpy.context)
