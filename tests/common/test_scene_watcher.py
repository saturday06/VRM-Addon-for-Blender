# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import functools
import platform
from os import getenv
from timeit import timeit

import bpy
from bpy.types import Context

from io_scene_vrm.common.scene_watcher import (
    RunState,
    SceneWatcher,
    SceneWatcherScheduler,
    create_fast_path_performance_test_scene,
)
from io_scene_vrm.common.test_helper import AddonTestCase, make_test_method_name


class __TestSceneWatcherBase(AddonTestCase):
    @staticmethod
    def run_and_reset_scene_watcher(
        scene_watcher: SceneWatcher, context: Context
    ) -> None:
        if scene_watcher.run(context) == RunState.FINISH:
            scene_watcher.reset_run_progress()

    def assert_performance(self, scene_watcher_type: type[SceneWatcher]) -> None:
        context = bpy.context

        scene_watcher = scene_watcher_type()
        create_fast_path_performance_test_scene(context, scene_watcher)

        run = functools.partial(
            self.run_and_reset_scene_watcher, scene_watcher, context
        )
        run()  # Initial execution can take longer

        timeout_margin_factor = 1.0
        if getenv("CI") == "true":
            # Add margin for CI server execution
            timeout_margin_factor *= 2.0
        if platform.system() == "Darwin" and platform.machine() == "x86_64":
            # Add margin for macOS x86_64 as only older machines exist
            timeout_margin_factor *= 1.5

        number = 20000
        timeout_seconds = 0.000_100 * timeout_margin_factor
        elapsed = timeit(run, number=number)
        self.assertLess(
            elapsed / float(number),
            timeout_seconds,
            f"{scene_watcher_type}.run() execution time must be less than "
            f"{timeout_seconds}s, but {elapsed / float(number)}s elapsed.",
        )


TestSceneWatcher = type(
    "TestSceneWatcher",
    (__TestSceneWatcherBase,),
    {
        make_test_method_name(scene_watcher_type.__name__): functools.partialmethod(
            __TestSceneWatcherBase.assert_performance, scene_watcher_type
        )
        for scene_watcher_type in SceneWatcherScheduler.get_all_scene_watcher_types()
    },
)
