# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import bpy
from bpy.app.handlers import persistent

from ...common.logger import get_logger
from .property_group import Vrm0BlendShapeGroupPropertyGroup

logger = get_logger(__name__)


@persistent
def frame_change_pre(_unused: object) -> None:
    Vrm0BlendShapeGroupPropertyGroup.frame_change_post_shape_key_updates.clear()


@persistent
def frame_change_post(_unused: object) -> None:
    context = bpy.context

    for (
        (
            shape_key_name,
            key_block_name,
        ),
        value,
    ) in Vrm0BlendShapeGroupPropertyGroup.frame_change_post_shape_key_updates.items():
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
    Vrm0BlendShapeGroupPropertyGroup.frame_change_post_shape_key_updates.clear()
