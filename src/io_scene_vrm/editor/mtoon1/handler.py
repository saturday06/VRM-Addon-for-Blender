# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import bpy
from bpy.app.handlers import persistent
from bpy.types import Depsgraph, Scene

from ...common.logger import get_logger
from ...common.scene_watcher import trigger_scene_watcher
from . import migration
from .scene_watcher import MToon1AutoSetup, OutlineUpdater

logger = get_logger(__name__)


@persistent
def depsgraph_update_post(_scene: Scene, depsgraph: Depsgraph) -> None:
    if depsgraph.id_type_updated("MATERIAL"):
        trigger_scene_watcher(MToon1AutoSetup)

    if bpy.app.version >= (3, 3):
        trigger_scene_watcher(OutlineUpdater)


@persistent
def load_post(_unsed: object) -> None:
    migration.state.material_blender_4_2_warning_shown = False
