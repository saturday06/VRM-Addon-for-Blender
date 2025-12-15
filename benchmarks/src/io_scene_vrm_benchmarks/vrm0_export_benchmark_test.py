# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from os import environ
from pathlib import Path

import bpy
import pytest
import requests
from bpy.types import Armature
from pytest_codspeed.plugin import BenchmarkFixture

from io_scene_vrm.common import ops


def test_vrm0_export(benchmark: BenchmarkFixture) -> None:
    context = bpy.context

    bpy.ops.preferences.addon_enable(module="io_scene_vrm")

    environ["BLENDER_VRM_AUTOMATIC_LICENSE_CONFIRMATION"] = "true"
    blend_path = Path(__file__).parent.parent.parent / "temp" / "vrm0_export.blend"
    if not blend_path.exists():
        bpy.ops.wm.read_homefile(use_empty=True)
        url = "https://raw.githubusercontent.com/pixiv/three-vrm/v0.6.11/packages/three-vrm/examples/models/three-vrm-girl.vrm"
        path = blend_path.with_name("three-vrm-girl.vrm")
        if not path.exists():
            with requests.get(url, timeout=5 * 60) as response:
                assert response.ok
                path.write_bytes(response.content)
        assert ops.import_scene.vrm(filepath=str(path)) == {"FINISHED"}
        active_object = context.active_object
        if not active_object:
            raise AssertionError
        if not isinstance(active_object.data, Armature):
            raise TypeError
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
        bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))

    export_path = blend_path.with_name("vrm0_export.vrm")

    assert ops.export_scene.vrm(filepath=str(export_path)) == {"FINISHED"}
    context.view_layer.update()
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))

    @benchmark
    def _() -> None:
        assert ops.export_scene.vrm(filepath=str(export_path)) == {"FINISHED"}
        context.view_layer.update()


if __name__ == "__main__":
    pytest.main()
