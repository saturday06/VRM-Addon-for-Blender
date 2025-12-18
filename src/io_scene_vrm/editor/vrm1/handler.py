# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import time

import bpy
from bpy.app.handlers import persistent

from ...common.logger import get_logger
from ...common.scene_watcher import trigger_scene_watcher
from ..extension import get_armature_extension
from .property_group import Vrm1ExpressionPropertyGroup
from .scene_watcher import LookAtPreviewUpdater

logger = get_logger(__name__)


class _LookAtPreviewTriggerCache:
    def __init__(self) -> None:
        self.last_check_time = 0.0
        self.last_result = False


_look_at_preview_trigger_cache = _LookAtPreviewTriggerCache()
_look_at_preview_trigger_cache_interval_seconds = 0.5


def _should_trigger_look_at_preview_updater() -> bool:
    now = time.monotonic()
    if (
        now - _look_at_preview_trigger_cache.last_check_time
        < _look_at_preview_trigger_cache_interval_seconds
    ):
        return _look_at_preview_trigger_cache.last_result

    _look_at_preview_trigger_cache.last_check_time = now

    blend_data = bpy.context.blend_data
    for armature_data in blend_data.armatures:
        ext = get_armature_extension(armature_data)
        if not ext.is_vrm1():
            continue
        look_at = ext.vrm1.look_at
        if look_at.enable_preview and look_at.preview_target_bpy_object:
            _look_at_preview_trigger_cache.last_result = True
            return True

    _look_at_preview_trigger_cache.last_result = False
    return False


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
        if abs(key_block.value - value) >= 1e-6:
            key_block.value = value
    Vrm1ExpressionPropertyGroup.frame_change_post_shape_key_updates.clear()

    # Update materials
    Vrm1ExpressionPropertyGroup.update_materials(context)


@persistent
def depsgraph_update_pre(_unused: object) -> None:
    if not _should_trigger_look_at_preview_updater():
        return
    trigger_scene_watcher(LookAtPreviewUpdater)
