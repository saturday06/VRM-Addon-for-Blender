import cProfile
from pathlib import Path
from pstats import SortKey

import bpy
from bpy.types import Context

from io_scene_vrm.common import ops, version
from io_scene_vrm.editor.extension import (
    VrmAddonArmatureExtensionPropertyGroup,
)

addon_version = version.get_addon_version()
spec_version = VrmAddonArmatureExtensionPropertyGroup.SPEC_VERSION_VRM1


def clean_scene(context: Context) -> None:
    if context.view_layer.objects.active:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    while context.blend_data.collections:
        context.blend_data.collections.remove(context.blend_data.collections[0])
    bpy.ops.outliner.orphans_purge(do_recursive=True)


def benchmark_spring_bone(context: Context) -> None:
    bpy.ops.preferences.addon_enable(module="io_scene_vrm")
    clean_scene(context)

    profiler = cProfile.Profile()
    with profiler:
        ops.import_scene.vrm(
            filepath=str(
                Path(__file__).parent.parent
                / "tests"
                / "resources"
                / "vrm"
                / "4.2"
                / "out"
                / "blend"
                / "mtoon1_2_20_61_vrm1.vrm"
            )
        )

    profiler.print_stats(SortKey.CUMULATIVE)


if __name__ == "__main__":
    benchmark_spring_bone(bpy.context)
