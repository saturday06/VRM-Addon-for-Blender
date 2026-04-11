# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import bpy
from bpy.app.handlers import persistent

from ...common.logger import get_logger
from ..extension_accessor import get_armature_extension
from .property_group import Vrm0BlendShapeGroupPropertyGroup

_logger = get_logger(__name__)


@persistent
def frame_change_post(_unused: object) -> None:
    context = bpy.context
    Vrm0BlendShapeGroupPropertyGroup.apply_pending_preview_update_to_armatures(context)


@persistent
def save_pre(_unused: object) -> None:
    context = bpy.context
    for armature_data in context.blend_data.armatures:
        vrm0 = get_armature_extension(armature_data).vrm0
        vrm0.secondary_animation.fixup(armature_object=None)
