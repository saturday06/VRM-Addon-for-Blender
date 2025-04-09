import cProfile
import functools
from pstats import SortKey, Stats

import bpy
from bpy.types import Context

from io_scene_vrm.common import version
from io_scene_vrm.common.micro_task import MicroTask, RunState
from io_scene_vrm.editor.extension import (
    VrmAddonArmatureExtensionPropertyGroup,
)
from io_scene_vrm.editor.vrm1.handler import LookAtPreviewUpdateTask

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


def run_and_reset_micro_task(micro_task: MicroTask) -> None:
    if micro_task.run() == RunState.FINISH:
        micro_task.reset_run_progress()


def benchmark_look_at_preview_update_task(context: Context) -> None:
    bpy.ops.preferences.addon_enable(module="io_scene_vrm")
    clean_scene(context)

    context.view_layer.update()

    task = LookAtPreviewUpdateTask()
    task.create_fast_path_performance_test_objects()
    run = functools.partial(run_and_reset_micro_task, task)
    run()  # 初回実行は時間がかかっても良い

    profiler = cProfile.Profile()
    with profiler:
        for _ in range(1000):
            run()

    Stats(profiler).sort_stats(SortKey.CUMULATIVE).print_stats(100)


if __name__ == "__main__":
    benchmark_look_at_preview_update_task(bpy.context)
