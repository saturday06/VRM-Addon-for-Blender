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

from ..addon_test_case import AddonTestCase


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
        run()  # 初回実行は時間がかかっても良い

        timeout_margin_factor = 1.0
        if getenv("CI") == "true":
            # CIサーバーでの実行ではマージンを追加
            timeout_margin_factor *= 2.0
        if platform.system() == "Darwin" and platform.machine() == "x86_64":
            # macOSのx86_64は古いマシンしか存在しないのでマージンを追加
            timeout_margin_factor *= 1.5

        number = 20000
        timeout_seconds = 0.000_100 * timeout_margin_factor
        elapsed = timeit(run, number=number)
        self.assertLess(
            elapsed / float(number),
            timeout_seconds,
            f"{scene_watcher_type}.run()の実行時間は{timeout_seconds}秒未満である必要がありますが"
            f"{elapsed / float(number)}秒経過しました。",
        )


TestSceneWatcher = type(
    "TestSceneWatcher",
    (__TestSceneWatcherBase,),
    {
        "test_" + scene_watcher_type.__name__: functools.partialmethod(
            __TestSceneWatcherBase.assert_performance, scene_watcher_type
        )
        for scene_watcher_type in SceneWatcherScheduler.get_all_scene_watcher_types()
    },
)
