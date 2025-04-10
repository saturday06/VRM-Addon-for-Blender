import cProfile
from pstats import SortKey, Stats

import bpy
from bpy.types import Context

from io_scene_vrm.common import version
from io_scene_vrm.common.scene_watcher import RunState, SceneWatcher
from io_scene_vrm.editor.extension import (
    VrmAddonArmatureExtensionPropertyGroup,
)
from io_scene_vrm.editor.mtoon1.handler import OutlineUpdater

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


def run_and_reset_scene_watcher(scene_watcher: SceneWatcher, context: Context) -> None:
    if scene_watcher.run(context) == RunState.FINISH:
        scene_watcher.reset_run_progress()


def benchmark_outline_updater(context: Context) -> None:
    bpy.ops.preferences.addon_enable(module="io_scene_vrm")
    clean_scene(context)

    context.view_layer.update()

    scene_watcher = OutlineUpdater()
    scene_watcher.create_fast_path_performance_test_objects(context)
    # 初回実行は時間がかかっても良い
    run_and_reset_scene_watcher(scene_watcher, context)

    profiler = cProfile.Profile()
    with profiler:
        for _ in range(1000):
            run_and_reset_scene_watcher(scene_watcher, context)

    Stats(profiler).sort_stats(SortKey.CUMULATIVE).print_stats(100)


if __name__ == "__main__":
    benchmark_outline_updater(bpy.context)
