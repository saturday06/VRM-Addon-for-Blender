from collections.abc import Callable

import bpy
from bpy.app.handlers import persistent

from .property_group import Vrm1ExpressionPropertyGroup

if not persistent:  # for fake-bpy-modules

    def persistent(func: Callable[[object], None]) -> Callable[[object], None]:
        return func


@persistent  # type: ignore[misc]
def depsgraph_update_pre(_dummy: object) -> None:
    for armature in bpy.data.armatures:
        expressions = armature.vrm_addon_extension.vrm1.expressions

        # アニメーションキーフレームに表示される名前を設定する
        preset_name_to_expression_dict = expressions.preset.name_to_expression_dict()
        for preset_name, preset_expression in preset_name_to_expression_dict.items():
            if preset_expression.name != preset_name:
                preset_expression.name = preset_name

        # UIList用のダミー要素を設定する
        ui_len = len(expressions.expression_ui_list_elements)
        all_len = len(preset_name_to_expression_dict) + len(expressions.custom)
        if ui_len == all_len:
            continue
        if ui_len > all_len:
            for _ in range(ui_len - all_len):
                expressions.expression_ui_list_elements.remove(0)
        if all_len > ui_len:
            for _ in range(all_len - ui_len):
                expressions.expression_ui_list_elements.add()


@persistent  # type: ignore[misc]
def frame_change_pre(_dummy: object) -> None:
    Vrm1ExpressionPropertyGroup.frame_change_post_shape_key_updates.clear()


@persistent  # type: ignore[misc]
def frame_change_post(_dummy: object) -> None:
    for (
        shape_key_name,
        key_block_name,
    ), value in Vrm1ExpressionPropertyGroup.frame_change_post_shape_key_updates.items():
        shape_key = bpy.data.shape_keys.get(shape_key_name)
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
