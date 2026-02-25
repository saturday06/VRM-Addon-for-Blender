# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import bpy
from bpy.app.handlers import persistent
from bpy.types import Depsgraph, Scene

from ...common.animation import is_animation_playing
from ...common.logger import get_logger
from ...common.scene_watcher import trigger_scene_watcher
from .property_group import Vrm1ExpressionPropertyGroup
from .scene_watcher import LookAtPreviewUpdater

logger = get_logger(__name__)


@persistent
def frame_change_post(_unused: object) -> None:
    context = bpy.context

    if is_animation_playing(context):
        Vrm1ExpressionPropertyGroup.apply_pending_preview_update_to_armatures(context)
    else:
        for armature in context.blend_data.armatures:
            Vrm1ExpressionPropertyGroup.apply_previews(context, armature)

    # Update materials
    Vrm1ExpressionPropertyGroup.update_materials(context)


@persistent
def depsgraph_update_post(_scene: Scene, _depsgraph: Depsgraph) -> None:
    trigger_scene_watcher(LookAtPreviewUpdater)
