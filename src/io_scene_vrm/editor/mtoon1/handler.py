# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import bpy
from bpy.app.handlers import persistent

from ...common.logger import get_logger
from ...common.scene_watcher import trigger_scene_watcher
from . import migration
from .scene_watcher import MToon1AutoSetup, OutlineUpdater

logger = get_logger(__name__)


@persistent
def depsgraph_update_pre(_unused: object) -> None:
    trigger_scene_watcher(MToon1AutoSetup)
    if bpy.app.version < (3, 3):
        return
    trigger_scene_watcher(OutlineUpdater)


@persistent
def load_post(_unsed: object) -> None:
    migration.state.material_blender_4_2_warning_shown = False
