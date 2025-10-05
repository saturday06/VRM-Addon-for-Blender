# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import cProfile
from pathlib import Path
from pstats import SortKey, Stats

import bpy
import requests
from bpy.types import Context

from io_scene_vrm.common import ops


def benchmark_vrm0_import(context: Context) -> None:
    bpy.ops.preferences.addon_enable(module="io_scene_vrm")
    bpy.ops.wm.read_homefile(use_empty=True)

    url = "https://raw.githubusercontent.com/pixiv/three-vrm/v0.6.11/packages/three-vrm/examples/models/three-vrm-girl.vrm"
    path = Path(__file__).parent / "temp" / "three-vrm-girl.vrm"
    if not path.exists():
        with requests.get(url, timeout=5 * 60) as response:
            assert response.ok
            path.write_bytes(response.content)

    profiler = cProfile.Profile()
    with profiler:
        assert ops.import_scene.vrm(filepath=str(path)) == {"FINISHED"}
        context.view_layer.update()

    Stats(profiler).sort_stats(SortKey.TIME).print_stats(50)


if __name__ == "__main__":
    benchmark_vrm0_import(bpy.context)
