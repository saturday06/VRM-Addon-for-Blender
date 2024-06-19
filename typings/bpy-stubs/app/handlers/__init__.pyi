from collections.abc import MutableSequence
from typing import Callable

def persistent(function: Callable[[object], None]) -> Callable[[object], None]: ...

# TODO: 引数の型を調べる
depsgraph_update_pre: MutableSequence[Callable[[object], None]]
depsgraph_update_post: MutableSequence[Callable[[object], None]]

save_pre: MutableSequence[Callable[[object], None]]
frame_change_pre: MutableSequence[Callable[[object], None]]
frame_change_post: MutableSequence[Callable[[object], None]]
load_post: MutableSequence[Callable[[object], None]]
