# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import math
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Final, Optional
from uuid import uuid4

from bpy.types import Context

from .logger import get_logger

logger = get_logger(__name__)


class PartialProgress:
    def __init__(
        self, progress: "Progress", partial_start_ratio: float, partial_end_ratio: float
    ) -> None:
        self.progress: Final = progress
        self.partial_start_ratio: Final = partial_start_ratio
        self.partial_end_ratio: Final = partial_end_ratio

    def update(self, ratio: float) -> None:
        ratio = min(max(0.0, ratio), 1.0)
        self.progress.update(
            self.partial_start_ratio
            + ratio * (self.partial_end_ratio - self.partial_start_ratio)
        )


class Progress:
    active_progress_uuid: Optional[str] = None

    def __init__(self, context: Context, *, show_progress: bool) -> None:
        self.context: Final = context
        self.show_progress: Final = show_progress
        self.uuid: Final = uuid4().hex
        self.last_ratio = 0.0

    def partial_progress(self, partial_end_ratio: float) -> PartialProgress:
        partial_end_ratio = min(max(0.0, partial_end_ratio), 1.0)
        return PartialProgress(self, self.last_ratio, partial_end_ratio)

    def update(self, ratio: float) -> None:
        ratio = min(max(0.0, ratio), 1.0)
        self.last_ratio = ratio
        if self.active_progress_uuid != self.uuid:
            logger.error(
                "Progress.update() called from different progress active=%s self=%s",
                self.active_progress_uuid,
                self.uuid,
            )
            return

        if not self.show_progress:
            return

        # マウスカーソルが四桁の数値になり、0から9999までの値が表示できる領域がある
        # しかし、進捗率をそのまま0から9999の数値に変換すると、下二桁の数値が頻繁に
        # ラウンドトリップし進捗状況が分かりにくくなる。そのため、下二桁の表示領域
        # だけを利用し0から99の数値で進捗率を表示する
        self.context.window_manager.progress_update(math.floor(ratio * 99))


@contextmanager
def create_progress(
    context: Context, *, show_progress: bool = True
) -> Iterator[Progress]:
    saved_progress_uuid = Progress.active_progress_uuid
    try:
        if show_progress and Progress.active_progress_uuid is None:
            context.window_manager.progress_begin(0, 9999)
        progress = Progress(context, show_progress=show_progress)
        Progress.active_progress_uuid = progress.uuid
        yield progress
    finally:
        Progress.active_progress_uuid = saved_progress_uuid
        if show_progress and Progress.active_progress_uuid is None:
            context.window_manager.progress_end()
