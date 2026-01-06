# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from typing import Final, Optional, Protocol

import bpy
from bpy.app.handlers import persistent
from bpy.types import Context


class WritableContextBecomesAvailableOnceHandler(Protocol):
    def __call__(self, context: Context, *, load_post: bool) -> None: ...


registered_handlers: Final[list[WritableContextBecomesAvailableOnceHandler]] = []
pending_handlers: Final[list[WritableContextBecomesAvailableOnceHandler]] = []


def register_writable_context_becomes_available_once_handler(
    handler: WritableContextBecomesAvailableOnceHandler,
) -> None:
    if handler not in registered_handlers:
        registered_handlers.append(handler)
    if handler not in pending_handlers:
        pending_handlers.append(handler)

    if not bpy.app.timers.is_registered(
        writable_context_becomes_available_timer_callback
    ):
        bpy.app.timers.register(writable_context_becomes_available_timer_callback)


def writable_context_becomes_available_timer_callback() -> Optional[float]:
    context = bpy.context
    trigger_writable_context_becomes_available_once_handlers(context, load_post=False)


def trigger_writable_context_becomes_available_once_handlers(
    context: Context, *, load_post: bool
) -> None:
    try:
        while pending_handlers:
            handler = pending_handlers.pop()
            handler(context, load_post=load_post)
    finally:
        pending_handlers.clear()


@persistent
def load_post(_unused: object) -> None:
    context = bpy.context
    for handler in registered_handlers:
        if handler not in pending_handlers:
            pending_handlers.append(handler)
    trigger_writable_context_becomes_available_once_handlers(context, load_post=True)


@persistent
def depsgraph_update_pre(_unused: object) -> None:
    context = bpy.context
    trigger_writable_context_becomes_available_once_handlers(context, load_post=False)


def clear_writable_context_becomes_available_once_handlers() -> None:
    registered_handlers.clear()
    pending_handlers.clear()
    if bpy.app.timers.is_registered(writable_context_becomes_available_timer_callback):
        bpy.app.timers.unregister(writable_context_becomes_available_timer_callback)
