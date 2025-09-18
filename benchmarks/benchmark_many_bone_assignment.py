# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import cProfile
from pathlib import Path
from pstats import SortKey, Stats

import bpy
from bpy.types import Armature, Context
from mathutils import Vector

from io_scene_vrm.common import version
from io_scene_vrm.common.human_bone_mapper import human_bone_mapper
from io_scene_vrm.editor.extension import (
    VrmAddonArmatureExtensionPropertyGroup,
    get_armature_extension,
)

addon_version = version.get_addon_version()
spec_version = VrmAddonArmatureExtensionPropertyGroup.SPEC_VERSION_VRM1


def generate_many_bones(context: Context) -> None:
    bpy.ops.object.add(type="ARMATURE", enter_editmode=True, location=(0, 0, 0))
    armature_object = context.object
    if not armature_object:
        raise AssertionError
    armature_data = armature_object.data
    if not isinstance(armature_data, Armature):
        raise TypeError

    context.view_layer.objects.active = armature_object

    ext = get_armature_extension(armature_data)
    ext.spec_version = ext.SPEC_VERSION_VRM1

    bpy.ops.object.mode_set(mode="EDIT")

    edit_bones = armature_data.edit_bones
    root_bone_name = "root"
    root_bone = edit_bones.new(root_bone_name)

    for bone_x in range(16):
        for bone_y in range(-7, 8):
            parent_bone_name = root_bone.name
            for bone_z in range(32):
                parent_bone = edit_bones[parent_bone_name]
                child_bone_name = f"mop_strand_x{bone_x}_y{bone_y}_z{bone_z}"
                child_bone = edit_bones.new(child_bone_name)

                # for cleanup, assign parent before error check
                child_bone.parent = parent_bone

                if child_bone.name != child_bone_name:
                    raise ValueError(child_bone_name)

                if parent_bone_name == root_bone.name:
                    child_bone.head = Vector((bone_x / 8.0, bone_y / 8.0, 0.0))
                else:
                    child_bone.head = parent_bone.tail.copy()
                child_bone.tail = Vector(
                    (bone_x / 8.0 + 1 * bone_z / 4, bone_y / 8.0, 0.0)
                )
                child_bone.use_connect = False
                parent_bone_name = child_bone_name

    bpy.ops.object.mode_set(mode="OBJECT")


def benchmark_many_bone_assignment(context: Context) -> None:
    bpy.ops.preferences.addon_enable(module="io_scene_vrm")

    version_str = "_".join(map(str, tuple(bpy.app.version)))
    path = Path(__file__).parent / "temp" / f"many_bone_assignment_{version_str}.blend"
    if not path.exists():
        bpy.ops.wm.read_homefile(use_empty=True)
        generate_many_bones(context)
        context.view_layer.update()
        bpy.ops.wm.save_as_mainfile(filepath=str(path))
        bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=str(path))

    armature = context.blend_data.objects.get("Armature")
    if (
        not armature
        or not (armature_data := armature.data)
        or not isinstance(armature_data, Armature)
    ):
        raise AssertionError

    profiler = cProfile.Profile()
    with profiler:
        human_bone_mapper.create_human_bone_mapping(armature)

    Stats(profiler).sort_stats(SortKey.TIME).print_stats(50)


if __name__ == "__main__":
    benchmark_many_bone_assignment(bpy.context)
