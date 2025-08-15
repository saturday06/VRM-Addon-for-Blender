# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from bpy.types import Context, UILayout, UIList

from ...common.logger import get_logger

logger = get_logger(__name__)


class VRM_UL_vrm1_expression(UIList):
    bl_idname = "VRM_UL_vrm1_expression"

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        expressions: object,
        _item: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        index: int,
        _flt_flag: int,
    ) -> None:
        layout.label(text=f"Item {index}", translate=False, icon="OUTLINER_OB_EMPTY")
