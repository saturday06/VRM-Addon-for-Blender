# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import bpy
from bpy.app.handlers import persistent
from bpy.types import Depsgraph, Scene

from ...common.logger import get_logger
from ...common.scene_watcher import trigger_scene_watcher
from .property_group import Vrm1ExpressionPropertyGroup
from .scene_watcher import LookAtPreviewUpdater

logger = get_logger(__name__)


@persistent
def frame_change_post(_unused: object) -> None:
    context = bpy.context

    Vrm1ExpressionPropertyGroup.apply_pending_preview_update_to_armatures(context)

    # Update materials
    Vrm1ExpressionPropertyGroup.update_materials(context)


@persistent
def depsgraph_update_post(_scene: Scene, _depsgraph: Depsgraph) -> None:
    trigger_scene_watcher(LookAtPreviewUpdater)
