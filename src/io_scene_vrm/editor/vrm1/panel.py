# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Set as AbstractSet

from bpy.types import Armature, Context, Object, Panel, UILayout

from ...common.logger import get_logger
from .. import search
from ..extension import get_armature_extension
from .property_group import (
    Vrm1ExpressionsPropertyGroup,
)
from .ui_list import (
    VRM_UL_vrm1_expression,
)

logger = get_logger(__name__)


def draw_vrm1_expressions_layout(
    armature: Object,
    context: Context,
    layout: UILayout,
    expressions: Vrm1ExpressionsPropertyGroup,
) -> None:
    layout.template_list(
        VRM_UL_vrm1_expression.bl_idname,
        "",
        expressions,
        "expression_ui_list_elements",
        expressions,
        "active_expression_ui_list_element_index",
        rows=5,
    )


class VRM_PT_vrm1_expressions_ui(Panel):
    bl_idname = "VRM_PT_vrm1_expressions_ui"
    bl_label = "Expressions"
    bl_translation_context = "VRM"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options: AbstractSet[str] = {"DEFAULT_CLOSED"}

    def draw_header(self, _context: Context) -> None:
        self.layout.label(icon="SHAPEKEY_DATA")

    def draw(self, context: Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        draw_vrm1_expressions_layout(
            armature,
            context,
            self.layout,
            get_armature_extension(armature_data).vrm1.expressions,
        )
