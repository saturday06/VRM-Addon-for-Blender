# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import bpy
from bpy.app.handlers import persistent

from ...common.animation import is_animation_playing
from ...common.logger import get_logger
from ...common.preferences import is_development_mode_enabled
from .property_group import Vrm0BlendShapeGroupPropertyGroup

logger = get_logger(__name__)


@persistent
def frame_change_post(_unused: object) -> None:
    context = bpy.context
    if not is_development_mode_enabled(context):
        Vrm0BlendShapeGroupPropertyGroup.apply_pending_preview_update_to_armatures(
            context
        )
        return

    if is_animation_playing(context):
        Vrm0BlendShapeGroupPropertyGroup.apply_pending_preview_update_to_armatures(
            context
        )
        return

    for armature in context.blend_data.armatures:
        Vrm0BlendShapeGroupPropertyGroup.apply_previews(context, armature)
