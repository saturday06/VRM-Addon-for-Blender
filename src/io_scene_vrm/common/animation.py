# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from dataclasses import dataclass
from typing import Final

from bpy.app.handlers import persistent
from bpy.types import Context

from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class State:
    during_animation_playback: bool = False
    during_frame_change: bool = False


state: Final = State()


def is_animation_playing(context: Context) -> bool:
    if state.during_animation_playback:
        return True
    screen = context.screen
    if not screen:
        return False
    return screen.is_animation_playing


def defer_shape_key_update(context: Context) -> bool:
    return is_animation_playing(context) or state.during_frame_change


@persistent
def animation_playback_pre(_unused: object) -> None:
    state.during_animation_playback = True


@persistent
def animation_playback_post(_unused: object) -> None:
    state.during_animation_playback = False


@persistent
def frame_change_pre(_unused: object) -> None:
    state.during_frame_change = True


@persistent
def frame_change_post(_unused: object) -> None:
    state.during_frame_change = False


def clear_global_variables() -> None:
    state.during_animation_playback = False
    state.during_frame_change = False
