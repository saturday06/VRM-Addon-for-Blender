# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import bpy
from bpy.app.handlers import persistent

from ...common.logger import get_logger
from ...common.scene_watcher import trigger_scene_watcher
from .property_group import Vrm1ExpressionPropertyGroup
from .scene_watcher import LookAtPreviewUpdater

logger = get_logger(__name__)


@persistent
def frame_change_pre(_unused: object) -> None:
    Vrm1ExpressionPropertyGroup.frame_change_post_shape_key_updates.clear()


@persistent
def frame_change_post(_unused: object) -> None:
    context = bpy.context

    for (
        shape_key_name,
        key_block_name,
    ), value in Vrm1ExpressionPropertyGroup.frame_change_post_shape_key_updates.items():
        shape_key = context.blend_data.shape_keys.get(shape_key_name)
        if not shape_key:
            continue
        key_blocks = shape_key.key_blocks
        if not key_blocks:
            continue
        key_block = key_blocks.get(key_block_name)
        if not key_block:
            continue
        key_block.value = value
    Vrm1ExpressionPropertyGroup.frame_change_post_shape_key_updates.clear()

    # Update materials
    Vrm1ExpressionPropertyGroup.update_materials(context)


@persistent
def depsgraph_update_pre(_unused: object) -> None:
    trigger_scene_watcher(LookAtPreviewUpdater)
