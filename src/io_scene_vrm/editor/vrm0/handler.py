# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import bpy
from bpy.app.handlers import persistent

from ...common.logger import get_logger
from .property_group import Vrm0BlendShapeGroupPropertyGroup

logger = get_logger(__name__)


@persistent
def frame_change_post(_unused: object) -> None:
    context = bpy.context
    Vrm0BlendShapeGroupPropertyGroup.apply_pending_preview_update_to_armatures(context)
