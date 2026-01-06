# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import base64
import hashlib
import inspect
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from tempfile import mkdtemp
from typing import Final, Optional, Protocol

import bpy
from bpy.app.handlers import persistent
from bpy.types import Context


class RunState(Enum):
    PREEMPT = 1
    FINISH = 2


class SceneWatcher(Protocol):
    """Protocol for detecting scene changes and performing some action when detected."""

    def run(self, context: Context) -> RunState:
        """Detect scene changes and perform some action when detected.

        If no changes that need to be detected have occurred in the scene, this method
        must return in less than 100 microseconds. If there is not enough time, save
        the current state to instance variables and interrupt the process.

        This method is executed multiple times across Blender frames. Usually such
        processing can be efficiently implemented using generators or async, but this
        class does not do so.

        The reason is that references to Blender's native objects cannot be held
        across frames, but programming with generators and async is difficult when
        considering this limitation.

        :return FINISH if processing is complete. PREEMPT if not complete.
        """
        raise NotImplementedError

    def create_fast_path_performance_test_objects(self, context: Context) -> None:
        """Create objects for testing whether run() normally completes.

        This tests whether the run() method normally completes in less than 100
        microseconds.
        """
        raise NotImplementedError

    def reset_run_progress(self) -> None:
        """Reset the interrupted state of run()."""
        raise NotImplementedError


@dataclass
class SceneWatcherSchedule:
    """Holds SceneWatcher and its operation status."""

    scene_watcher: SceneWatcher
    requires_run_once_more: bool = False
    finished: bool = False


@dataclass
class SceneWatcherScheduler:
    """Periodically executes registered SceneWatchers in order.

    This scheduler is careful not to block the UI while executing the
    SceneWatcher instances.
    """

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
            # High-frequency fast path.
            # Allow returning with minimal processing.

            if scene_watcher_schedule.finished:
                # If the task is finished, restart it
                scene_watcher_schedule.finished = False
                scene_watcher_schedule.scene_watcher.reset_run_progress()
            else:
                # If the task is running,
                # set it to "run once more after completion"
                scene_watcher_schedule.requires_run_once_more = True
            return

        # Low-frequency slow path.
        # Heavy processing is okay.

        # To prevent unregistered SceneWatchers from being missed in testing,
        # throw an error if trying to instantiate an unregistered SceneWatcher.
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
        """Execute one SceneWatcher.

        Use index values to reduce GC allocation.
        """
        if not self.scene_watcher_schedules:
            return False

        for _ in range(len(self.scene_watcher_schedules)):
            self.scene_watcher_schedule_index += 1
            self.scene_watcher_schedule_index %= len(self.scene_watcher_schedules)

            # Skip tasks that are already completed
            scene_watcher_schedule = self.scene_watcher_schedules[
                self.scene_watcher_schedule_index
            ]
            if scene_watcher_schedule.finished:
                continue

            # Execute the task
            run_state = scene_watcher_schedule.scene_watcher.run(context)
            if run_state == RunState.FINISH:
                if scene_watcher_schedule.requires_run_once_more:
                    scene_watcher_schedule.requires_run_once_more = False
                    scene_watcher_schedule.scene_watcher.reset_run_progress()
                else:
                    scene_watcher_schedule.finished = True

            # Return if at least one task was executed
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


def create_fast_path_performance_test_scene(
    context: Context, scene_watcher: SceneWatcher
) -> None:
    class_file_path_str = inspect.getfile(type(scene_watcher))
    if not class_file_path_str:
        message = f"No path for class {type(scene_watcher)}"
        raise ValueError(message)
    class_file_path = Path(class_file_path_str)
    if not class_file_path.exists():
        message = f"No {class_file_path} found"
        raise ValueError(message)
    class_source_hash = (
        base64.urlsafe_b64encode(
            hashlib.sha3_224(class_file_path.read_bytes()).digest()
        )
        .rstrip(b"=")
        .decode()
    )
    repository_root_path = (
        Path(__file__).resolve(strict=True).parent.parent.parent.parent
    )
    if (repository_root_path / ".git").exists() and (
        repository_root_path / "pyproject.toml"
    ).exists():
        temp_path = repository_root_path / "tests" / "temp"
    else:
        temp_path = Path(mkdtemp(prefix="vrm-format-"))
    cached_blend_path = temp_path / (
        type(scene_watcher).__name__
        + "-"
        + "_".join(map(str, bpy.app.version))
        + "-"
        + class_source_hash
        + ".blend"
    )
    if not cached_blend_path.exists():
        bpy.ops.wm.read_homefile(use_empty=True)
        scene_watcher.create_fast_path_performance_test_objects(context)
        bpy.ops.wm.save_as_mainfile(filepath=str(cached_blend_path))
        bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.wm.open_mainfile(filepath=str(cached_blend_path))


def trigger_scene_watcher(scene_watcher_type: type[SceneWatcher]) -> None:
    scene_watcher_scheduler.trigger(scene_watcher_type)


@persistent
def save_pre(_unused: object) -> None:
    context = bpy.context

    scene_watcher_scheduler.flush(context)
