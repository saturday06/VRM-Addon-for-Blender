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


class MicroTask(Protocol):
    def run(self, context: Context) -> RunState:
        """処理を実行する.

        このメソッドは通常100マイクロ秒未満でreturnする必要がある。
        100マイクロ秒内に処理が完了しない場合、現在状態をインスタンス変数に
        保存して処理を中断するようにする。

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
class MicroTaskSchedule:
    task: MicroTask
    requires_run_once_more: bool = False
    finished: bool = False


@dataclass
class MicroTaskScheduler:
    """MicroTaskを実行する.

    ジェネレーターやasyncを使わない理由は、Blenderのネイティブオブジェクトへの
    参照がフレームをまたいで保持できないが、ジェネレーターやasyncを使う場合は
    それを考慮してのプログラミングが難しいため。
    """

    INTERVAL: Final[float] = 0.2
    task_schedule_index = 0
    task_type_to_task_schedule: dict[type[MicroTask], MicroTaskSchedule] = field(
        default_factory=dict
    )
    task_schedules: list[MicroTaskSchedule] = field(default_factory=list)

    def schedule(self, task_type: type[MicroTask]) -> None:
        task_schedule = self.task_type_to_task_schedule.get(task_type)
        if task_schedule:
            # 呼び出し頻度が高いファストパス。
            # 最小限の処理でreturnできるようにしておく。

            if task_schedule.finished:
                # タスクが終了済みの場合は再開
                task_schedule.finished = False
                task_schedule.task.reset_run_progress()
            else:
                # タスクが実行中の場合は、
                # 「一度完了した後にもう一度実行」と設定
                task_schedule.requires_run_once_more = True
            return

        # 呼び出し頻度が低いスローパス。
        # 処理が重くなっても大丈夫。

        # テスト対象から漏れないようにするため、
        # 未登録のMicroTaskをインスタンス化しようとしたらエラーにする。
        if task_type not in self.get_all_micro_task_types():
            message = f"{task_type} is not registered"
            raise NotImplementedError(message)

        new_micro_task = task_type()
        new_schedule = MicroTaskSchedule(task=new_micro_task)
        self.task_type_to_task_schedule[task_type] = new_schedule
        self.task_schedules.append(new_schedule)

    @staticmethod
    def get_all_micro_task_types() -> Sequence[type[MicroTask]]:
        from ..editor.mtoon1.handler import OutlineUpdateTask
        from ..editor.vrm1.handler import LookAtPreviewUpdateTask

        return [OutlineUpdateTask, LookAtPreviewUpdateTask]

    def process(self, context: Context) -> None:
        """MicroTaskを一つ実行する.

        GC Allocationを抑えるため、インデックス値を用いる
        """
        if not self.task_schedules:
            return

        self.task_schedule_index += 1
        if self.task_schedule_index >= len(self.task_schedules):
            self.task_schedule_index = 0

        for task_schedule_index in range(
            self.task_schedule_index, len(self.task_schedules)
        ):
            self.task_schedule_index = task_schedule_index

            # すでに完了しているタスクは飛ばす
            task_schedule = self.task_schedules[self.task_schedule_index]
            if task_schedule.finished:
                continue

            # タスクを実行
            run_state = task_schedule.task.run(context)
            if run_state == RunState.FINISH:
                if task_schedule.requires_run_once_more:
                    task_schedule.requires_run_once_more = False
                    task_schedule.task.reset_run_progress()
                else:
                    task_schedule.finished = True

            # 一つでもタスクを実行したならreturn
            return

    def flush(self, context: Context) -> None:
        self.task_schedule_index = 0
        for task_schedule in self.task_schedules:
            while task_schedule.task.run(context) != RunState.FINISH:
                pass


micro_task_scheduler = MicroTaskScheduler()


def process_micro_task_scheduler() -> Optional[float]:
    context = bpy.context

    micro_task_scheduler.process(context)
    return MicroTaskScheduler.INTERVAL


def add_micro_task(task_type: type[MicroTask]) -> None:
    micro_task_scheduler.schedule(task_type)


def setup() -> None:
    if bpy.app.timers.is_registered(process_micro_task_scheduler):
        return
    bpy.app.timers.register(
        process_micro_task_scheduler, first_interval=MicroTaskScheduler.INTERVAL
    )


@persistent
def save_pre(_unused: object) -> None:
    context = bpy.context

    micro_task_scheduler.flush(context)
