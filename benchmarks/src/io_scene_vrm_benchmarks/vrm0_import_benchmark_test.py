# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from pathlib import Path

import bpy
import pytest
import requests
from pytest_codspeed.plugin import BenchmarkFixture

from io_scene_vrm.common import ops


def test_vrm0_import(benchmark: BenchmarkFixture) -> None:
    context = bpy.context

    bpy.ops.preferences.addon_enable(module="io_scene_vrm")
    bpy.ops.wm.read_homefile(use_empty=True)

    url = "https://raw.githubusercontent.com/pixiv/three-vrm/v0.6.11/packages/three-vrm/examples/models/three-vrm-girl.vrm"
    path = Path(__file__).parent.parent.parent / "temp" / "three-vrm-girl.vrm"
    if not path.exists():
        with requests.get(url, timeout=5 * 60) as response:
            assert response.ok
            path.write_bytes(response.content)

    assert ops.import_scene.vrm(filepath=str(path)) == {"FINISHED"}
    context.view_layer.update()
    bpy.ops.wm.read_homefile(use_empty=True)

    @benchmark
    def _() -> None:
        assert ops.import_scene.vrm(filepath=str(path)) == {"FINISHED"}
        context.view_layer.update()


if __name__ == "__main__":
    pytest.main()
