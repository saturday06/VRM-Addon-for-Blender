# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import MutableSequence
from typing import Callable, TypeVar

from bpy.types import Depsgraph, Scene
from typing_extensions import ParamSpec

__PersistentParam = ParamSpec("__PersistentParam")
__PersistentParamReturn = TypeVar("__PersistentParamReturn")

def persistent(
    function: Callable[__PersistentParam, __PersistentParamReturn],
) -> Callable[__PersistentParam, __PersistentParamReturn]: ...

animation_playback_post: MutableSequence[Callable[[object], None]]
animation_playback_pre: MutableSequence[Callable[[object], None]]

# TODO: Investigate the type of arguments
depsgraph_update_post: MutableSequence[
    Callable[[Scene, Depsgraph], None] | Callable[[Scene], None]
]
depsgraph_update_pre: MutableSequence[
    Callable[[Scene, Depsgraph], None] | Callable[[Scene], None]
]
frame_change_post: MutableSequence[Callable[[object], None]]
frame_change_pre: MutableSequence[Callable[[object], None]]
load_factory_preferences_post: MutableSequence[Callable[[object], None]]
load_factory_startup_post: MutableSequence[Callable[[object], None]]
load_post: MutableSequence[Callable[[object], None]]
load_pre: MutableSequence[Callable[[object], None]]
redo_post: MutableSequence[Callable[[object], None]]
redo_pre: MutableSequence[Callable[[object], None]]
render_cancel: MutableSequence[Callable[[object], None]]
render_complete: MutableSequence[Callable[[object], None]]
render_init: MutableSequence[Callable[[object], None]]
render_post: MutableSequence[Callable[[object], None]]
render_pre: MutableSequence[Callable[[object], None]]
render_stats: MutableSequence[Callable[[object], None]]
render_write: MutableSequence[Callable[[object], None]]
save_post: MutableSequence[Callable[[object], None]]
save_pre: MutableSequence[Callable[[object], None]]
undo_post: MutableSequence[Callable[[object], None]]
undo_pre: MutableSequence[Callable[[object], None]]
version_update: MutableSequence[Callable[[object], None]]
