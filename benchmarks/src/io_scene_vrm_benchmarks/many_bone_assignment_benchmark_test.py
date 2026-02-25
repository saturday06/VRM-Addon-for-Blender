# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from pathlib import Path

import bpy
import pytest
from bpy.types import Armature, ArmatureEditBones, Context, EditBone
from pytest_codspeed.plugin import BenchmarkFixture

from io_scene_vrm.common.human_bone_mapper import human_bone_mapper
from io_scene_vrm.editor.extension import (
    get_armature_extension,
)


def add_bones(
    edit_bones: ArmatureEditBones, parent_edit_bone: EditBone, depth: int
) -> None:
    branch_counts = [1, 2, 3, 2, 3, 2, 2, 2, 3]
    if depth >= len(branch_counts):
        return
    branch_count = branch_counts[depth]

    for i in range(branch_count):
        bone = edit_bones.new(f"{parent_edit_bone.name}{i}")

        bone.head = (
            (depth * 0.3 + i * 0.05) * (1 if (i + depth) % 2 == 0 else -1),
            depth * 0.1 + i * 0.2,
            0.5 + depth * 0.1 * (1 if depth % 2 == 0 else -1),
        )

        bone.tail = (
            bone.head[0],
            bone.head[1] + 0.2,
            bone.head[2],
        )

        bone.parent = parent_edit_bone
        add_bones(edit_bones, bone, depth + 1)


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
    root_bone_name = "Bone"
    root_bone = edit_bones.new(root_bone_name)
    root_bone.head = (0, 0, 0)
    root_bone.tail = (0, 0, 0.5)
    add_bones(edit_bones, root_bone, 0)

    bpy.ops.object.mode_set(mode="OBJECT")


def test_many_bone_assignment(benchmark: BenchmarkFixture) -> None:
    context = bpy.context

    bpy.ops.preferences.addon_enable(module="io_scene_vrm")

    version_str = "_".join(map(str, tuple(bpy.app.version)))
    path = (
        Path(__file__).parent.parent.parent
        / "temp"
        / f"many_bone_assignment_{version_str}.blend"
    )
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

    @benchmark
    def _() -> None:
        human_bone_mapper.create_human_bone_mapping(armature)


if __name__ == "__main__":
    pytest.main()
