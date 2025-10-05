# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import cProfile
from os import environ
from pathlib import Path
from pstats import SortKey, Stats

import bpy
import requests
from bpy.types import Context

from io_scene_vrm.common import ops


def benchmark_vrm0_export(context: Context) -> None:
    bpy.ops.preferences.addon_enable(module="io_scene_vrm")

    environ["BLENDER_VRM_AUTOMATIC_LICENSE_CONFIRMATION"] = "true"
    blend_path = Path(__file__).parent / "temp" / "vrm1_export.blend"
    if not blend_path.exists():
        bpy.ops.wm.read_homefile(use_empty=True)
        url = "https://raw.githubusercontent.com/vrm-c/vrm-specification/c24d76d99a18738dd2c266be1c83f089064a7b5e/samples/Seed-san/vrm/Seed-san.vrm"
        path = Path(__file__).parent / "temp" / "Seed-san.vrm"
        if not path.exists():
            with requests.get(url, timeout=5 * 60) as response:
                assert response.ok
                path.write_bytes(response.content)
        assert ops.import_scene.vrm(filepath=str(path)) == {"FINISHED"}
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
        bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))

    export_path = Path(__file__).parent / "temp" / "vrm1_export.vrm"

    profiler = cProfile.Profile()
    with profiler:
        assert ops.export_scene.vrm(filepath=str(export_path)) == {"FINISHED"}
        context.view_layer.update()

    Stats(profiler).sort_stats(SortKey.TIME).print_stats(50)


if __name__ == "__main__":
    benchmark_vrm0_export(bpy.context)
