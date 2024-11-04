# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from . import handlers as handlers
from . import timers as timers
from . import translations as translations

debug: bool
debug_depsgraph: bool
debug_depsgraph_build: bool
debug_depsgraph_eval: bool
debug_depsgraph_pretty: bool
debug_depsgraph_tag: bool
debug_depsgraph_time: bool
debug_events: bool
debug_ffmpeg: bool
debug_freestyle: bool
debug_handlers: bool
debug_io: bool
debug_python: bool
debug_simdata: bool
debug_value: bool
debug_wm: bool
tempdir: str
use_event_simulate: bool
build_platform: bytes
build_type: bytes
version_cycle: str
version: tuple[int, int, int]
binary_path: str
