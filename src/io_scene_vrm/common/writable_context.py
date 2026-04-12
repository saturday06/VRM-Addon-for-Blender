# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from dataclasses import dataclass, field
from typing import Final, Optional, Protocol

import bpy
from bpy.app.handlers import persistent
from bpy.types import Context


class WritableContextBecomesAvailableOnceHandler(Protocol):
    def __call__(self, context: Context, *, load_post: bool) -> None: ...


@dataclass
class State:
    registered_handlers: list[WritableContextBecomesAvailableOnceHandler] = field(
        default_factory=list[WritableContextBecomesAvailableOnceHandler]
    )
    pending_handlers: list[WritableContextBecomesAvailableOnceHandler] = field(
        default_factory=list[WritableContextBecomesAvailableOnceHandler]
    )


_state: Final = State()


def register_writable_context_becomes_available_once_handler(
    handler: WritableContextBecomesAvailableOnceHandler,
) -> None:
    if handler not in _state.registered_handlers:
        _state.registered_handlers.append(handler)
    if handler not in _state.pending_handlers:
        _state.pending_handlers.append(handler)

    if not bpy.app.timers.is_registered(
        _writable_context_becomes_available_timer_callback
    ):
        bpy.app.timers.register(_writable_context_becomes_available_timer_callback)


def _writable_context_becomes_available_timer_callback() -> Optional[float]:
    context = bpy.context
    trigger_writable_context_becomes_available_once_handlers(context, load_post=False)


def trigger_writable_context_becomes_available_once_handlers(
    context: Context, *, load_post: bool
) -> None:
    try:
        while _state.pending_handlers:
            handler = _state.pending_handlers.pop()
            handler(context, load_post=load_post)
    finally:
        _state.pending_handlers.clear()


@persistent
def load_post(_unused: object) -> None:
    context = bpy.context
    for handler in _state.registered_handlers:
        if handler not in _state.pending_handlers:
            _state.pending_handlers.append(handler)
    trigger_writable_context_becomes_available_once_handlers(context, load_post=True)


@persistent
def depsgraph_update_pre(_unused: object) -> None:
    context = bpy.context
    trigger_writable_context_becomes_available_once_handlers(context, load_post=False)


def clear_writable_context_becomes_available_once_handlers() -> None:
    _state.registered_handlers.clear()
    _state.pending_handlers.clear()
    if bpy.app.timers.is_registered(_writable_context_becomes_available_timer_callback):
        bpy.app.timers.unregister(_writable_context_becomes_available_timer_callback)
