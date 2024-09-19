from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Final, Optional, Protocol

import bpy
from bpy.app.handlers import persistent
from bpy.types import Context


class RunState(Enum):
    PREEMPT = 1
    FINISH = 2


class SceneWatcher(Protocol):
    """シーンの変更を検知し、検知した際に何らかの処理を行うようにするプロトコル."""

    def run(self, context: Context) -> RunState:
        """シーンの変更の検知と、検知した際に何らかの処理を行う.

        シーンに検知したい変更が発生していない場合、このメソッドは100マイクロ秒未満で
        returnする必要がある。時間が足りない場合、現在状態をインスタンス変数などに保存
        して処理を中断する。

        このメソッドはBlenderのフレームを跨いで複数回実行される。通常そのような処理は
        ジェネレーターやasyncを使うことで効率的に実装できるが、このクラスではそうしない。

        その理由は、Blenderのネイティブなオブジェクトへの参照をフレームをまたいで保持
        できないが、ジェネレーターやasyncはそれを考慮してのプログラミングが難しいため。

        :return 処理が完了した場合FINISH。完了しなかった場合はPREEMPT。
        """
        raise NotImplementedError

    def create_fast_path_performance_test_objects(self, context: Context) -> None:
        """run()が通常100マイクロ秒未満で完了するかのテストのためのオブジェクトを作成する."""
        raise NotImplementedError

    def reset_run_progress(self) -> None:
        """run()の中断状態をリセットする."""
        raise NotImplementedError


@dataclass
class SceneWatcherSchedule:
    """SceneWatcherと、その稼働状況を保持する."""

    scene_watcher: SceneWatcher
    requires_run_once_more: bool = False
    finished: bool = False


@dataclass
class SceneWatcherScheduler:
    """UIをブロックしないように注意しながら、登録されたSceneWatcherを順番に定期的に実行する."""

    INTERVAL: Final[float] = 0.2
    scene_watcher_schedule_index: int = 0
    scene_watcher_type_to_schedule: dict[type[SceneWatcher], SceneWatcherSchedule] = (
        field(default_factory=dict[type[SceneWatcher], SceneWatcherSchedule])
    )
    scene_watcher_schedules: list[SceneWatcherSchedule] = field(
        default_factory=list[SceneWatcherSchedule]
    )

    def trigger(self, scene_watcher_type: type[SceneWatcher]) -> None:
        scene_watcher_schedule = self.scene_watcher_type_to_schedule.get(
            scene_watcher_type
        )
        if scene_watcher_schedule:
            # 呼び出し頻度が高いファストパス。
            # 最小限の処理でreturnできるようにしておく。

            if scene_watcher_schedule.finished:
                # タスクが終了済みの場合は再開
                scene_watcher_schedule.finished = False
                scene_watcher_schedule.scene_watcher.reset_run_progress()
            else:
                # タスクが実行中の場合は、
                # 「一度完了した後にもう一度実行」と設定
                scene_watcher_schedule.requires_run_once_more = True
            return

        # 呼び出し頻度が低いスローパス。
        # 処理が重くなっても大丈夫。

        # テスト対象から漏れないようにするため、
        # 未登録のSceneWatcherをインスタンス化しようとしたらエラーにする。
        if scene_watcher_type not in self.get_all_scene_watcher_types():
            message = f"{scene_watcher_type} is not registered"
            raise NotImplementedError(message)

        new_scene_watcher = scene_watcher_type()
        new_schedule = SceneWatcherSchedule(scene_watcher=new_scene_watcher)
        self.scene_watcher_type_to_schedule[scene_watcher_type] = new_schedule
        self.scene_watcher_schedules.append(new_schedule)

    @staticmethod
    def get_all_scene_watcher_types() -> Sequence[type[SceneWatcher]]:
        from ..editor.mtoon1.scene_watcher import MToon1AutoSetup, OutlineUpdater
        from ..editor.vrm1.scene_watcher import LookAtPreviewUpdater

        return [OutlineUpdater, LookAtPreviewUpdater, MToon1AutoSetup]

    def process(self, context: Context) -> bool:
        """SceneWatcherを一つ実行する.

        GC Allocationを抑えるため、インデックス値を用いる
        """
        if not self.scene_watcher_schedules:
            return False

        for _ in range(len(self.scene_watcher_schedules)):
            self.scene_watcher_schedule_index += 1
            self.scene_watcher_schedule_index %= len(self.scene_watcher_schedules)

            # すでに完了しているタスクは飛ばす
            scene_watcher_schedule = self.scene_watcher_schedules[
                self.scene_watcher_schedule_index
            ]
            if scene_watcher_schedule.finished:
                continue

            # タスクを実行
            run_state = scene_watcher_schedule.scene_watcher.run(context)
            if run_state == RunState.FINISH:
                if scene_watcher_schedule.requires_run_once_more:
                    scene_watcher_schedule.requires_run_once_more = False
                    scene_watcher_schedule.scene_watcher.reset_run_progress()
                else:
                    scene_watcher_schedule.finished = True

            # 一つでもタスクを実行したならreturn
            return True
        return False

    def flush(self, context: Context) -> None:
        while self.process(context):
            pass


scene_watcher_scheduler = SceneWatcherScheduler()


def process_scene_watcher_scheduler() -> Optional[float]:
    context = bpy.context

    scene_watcher_scheduler.process(context)
    return SceneWatcherScheduler.INTERVAL


def trigger_scene_watcher(scene_watcher_type: type[SceneWatcher]) -> None:
    scene_watcher_scheduler.trigger(scene_watcher_type)


def setup() -> None:
    if bpy.app.timers.is_registered(process_scene_watcher_scheduler):
        return
    bpy.app.timers.register(
        process_scene_watcher_scheduler, first_interval=SceneWatcherScheduler.INTERVAL
    )


@persistent
def save_pre(_unused: object) -> None:
    context = bpy.context

    scene_watcher_scheduler.flush(context)
