# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import bpy
import pytest
from bpy.types import Context
from pytest_codspeed.plugin import BenchmarkFixture

from io_scene_vrm.common.scene_watcher import (
    RunState,
    SceneWatcher,
    create_fast_path_performance_test_scene,
)
from io_scene_vrm.editor.mtoon1.scene_watcher import OutlineUpdater


def run_and_reset_scene_watcher(scene_watcher: SceneWatcher, context: Context) -> None:
    if scene_watcher.run(context) == RunState.FINISH:
        scene_watcher.reset_run_progress()


def test_outline_updater(benchmark: BenchmarkFixture) -> None:
    context = bpy.context

    bpy.ops.preferences.addon_enable(module="io_scene_vrm")

    scene_watcher = OutlineUpdater()
    create_fast_path_performance_test_scene(context, scene_watcher)
    # Initial execution can take longer
    run_and_reset_scene_watcher(scene_watcher, context)

    @benchmark
    def _() -> None:
        for _ in range(1000):
            run_and_reset_scene_watcher(scene_watcher, context)


if __name__ == "__main__":
    pytest.main()
