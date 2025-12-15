# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from os import environ
from pathlib import Path

import bpy
import pytest
import requests
from pytest_codspeed.plugin import BenchmarkFixture

from io_scene_vrm.common import ops


def test_vrm1_export(benchmark: BenchmarkFixture) -> None:
    context = bpy.context

    bpy.ops.preferences.addon_enable(module="io_scene_vrm")

    environ["BLENDER_VRM_AUTOMATIC_LICENSE_CONFIRMATION"] = "true"
    blend_path = Path(__file__).parent.parent.parent / "temp" / "vrm1_export.blend"
    if not blend_path.exists():
        bpy.ops.wm.read_homefile(use_empty=True)
        url = "https://raw.githubusercontent.com/vrm-c/vrm-specification/c24d76d99a18738dd2c266be1c83f089064a7b5e/samples/Seed-san/vrm/Seed-san.vrm"
        path = blend_path.with_name("Seed-san.vrm")
        if not path.exists():
            with requests.get(url, timeout=5 * 60) as response:
                assert response.ok
                path.write_bytes(response.content)
        assert ops.import_scene.vrm(filepath=str(path)) == {"FINISHED"}
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
        bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))

    export_path = blend_path.with_name("vrm1_export.vrm")

    assert ops.export_scene.vrm(filepath=str(export_path)) == {"FINISHED"}
    context.view_layer.update()
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))

    @benchmark
    def _() -> None:
        assert ops.export_scene.vrm(filepath=str(export_path)) == {"FINISHED"}
        context.view_layer.update()


if __name__ == "__main__":
    pytest.main()
