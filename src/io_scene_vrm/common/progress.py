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

        # The mouse cursor becomes a four-digit number, and there is an area
        # where values from 0 to 9999 can be displayed. However, if the
        # progress rate is directly converted to a number from 0 to 9999, the
        # last two digits will frequently round-trip, making the progress
        # difficult to understand. Therefore, only the last two digits display
        # area is used to show the progress rate as a number from 0 to 99.
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
