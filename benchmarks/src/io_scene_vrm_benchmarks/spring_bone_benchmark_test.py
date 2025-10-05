# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from pathlib import Path

import bpy
import pytest
import requests
from bpy.types import Armature
from mathutils import Vector
from pytest_codspeed.plugin import BenchmarkFixture

from io_scene_vrm.common import ops
from io_scene_vrm.editor.extension import (
    get_armature_extension,
)
from io_scene_vrm.editor.spring_bone1.handler import update_pose_bone_rotations


def test_spring_bone(benchmark: BenchmarkFixture) -> None:
    context = bpy.context

    bpy.ops.preferences.addon_enable(module="io_scene_vrm")
    bpy.ops.wm.read_homefile(use_empty=True)

    url = "https://raw.githubusercontent.com/vrm-c/vrm-specification/c24d76d99a18738dd2c266be1c83f089064a7b5e/samples/VRM1_Constraint_Twist_Sample/vrm/VRM1_Constraint_Twist_Sample.vrm"
    path = (
        Path(__file__).parent.parent.parent
        / "temp"
        / "VRM1_Constraint_Twist_Sample.vrm"
    )
    if not path.exists():
        with requests.get(url, timeout=5 * 60) as response:
            assert response.ok
            path.write_bytes(response.content)

    assert ops.import_scene.vrm(filepath=str(path)) == {"FINISHED"}

    armature = context.object
    if (
        not armature
        or not (armature_data := armature.data)
        or not isinstance(armature_data, Armature)
    ):
        raise AssertionError

    get_armature_extension(armature_data).spring_bone1.enable_animation = True

    context.view_layer.update()
    update_pose_bone_rotations(context, delta_time=1.0 / 24.0)
    armature.location = Vector((1, 0, 0))
    context.view_layer.update()

    @benchmark
    def _() -> None:
        for _ in range(10):
            update_pose_bone_rotations(context, delta_time=1.0 / 24.0)


if __name__ == "__main__":
    pytest.main()
