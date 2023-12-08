from bpy.types import Context, Mesh, UILayout, UIList

from ...common.logging import get_logger
from .property_group import (
    Vrm1ExpressionsPresetPropertyGroup,
    Vrm1ExpressionsPropertyGroup,
    Vrm1MaterialColorBindPropertyGroup,
    Vrm1MorphTargetBindPropertyGroup,
    Vrm1TextureTransformBindPropertyGroup,
)

logger = get_logger(__name__)


class VRM_UL_vrm1_expression(UIList):
    bl_idname = "VRM_UL_vrm1_expression"

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        data: object,
        _item: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        index: int,
        _flt_flag: int,
    ) -> None:
        expressions = data
        if not isinstance(expressions, Vrm1ExpressionsPropertyGroup):
            return
        preset_expression_items = list(
            expressions.preset.name_to_expression_dict().items()
        )
        if index < len(preset_expression_items):
            name, expression = preset_expression_items[index]
            icon = Vrm1ExpressionsPresetPropertyGroup.NAME_TO_ICON_DICT.get(name)
            if not icon:
                logger.error(f"Unknown preset expression: {name}")
                icon = "SHAPEKEY_DATA"
        else:
            custom_expressions = expressions.custom
            custom_index = index - len(preset_expression_items)
            if custom_index >= len(custom_expressions):
                return
            expression = custom_expressions[custom_index]
            name = expression.custom_name
            icon = "SHAPEKEY_DATA"

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        split = layout.split(align=True, factor=0.55)
        split.label(text=name, translate=False, icon=icon)
        split.prop(expression, "preview", text="Preview")


class VRM_UL_vrm1_morph_target_bind(UIList):
    bl_idname = "VRM_UL_vrm1_morph_target_bind"

    def draw_item(
        self,
        context: Context,
        layout: UILayout,
        _data: object,
        item: object,
        icon: int,
        _active_data: object,
        _active_prop_name: str,
        _index: int,
        _flt_flag: int,
    ) -> None:
        blend_data = context.blend_data
        morph_target_bind = item
        if not isinstance(morph_target_bind, Vrm1MorphTargetBindPropertyGroup):
            return

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        name = morph_target_bind.node.mesh_object_name
        mesh_object = blend_data.objects.get(morph_target_bind.node.mesh_object_name)
        if mesh_object:
            mesh_data = mesh_object.data
            if isinstance(mesh_data, Mesh):
                shape_keys = mesh_data.shape_keys
                if shape_keys:
                    keys = shape_keys.key_blocks.keys()
                    if morph_target_bind.index in keys:
                        name += " / " + morph_target_bind.index
        layout.label(text=name, translate=False, icon="MESH_DATA")


class VRM_UL_vrm1_material_color_bind(UIList):
    bl_idname = "VRM_UL_vrm0_material_color_bind"

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        _data: object,
        item: object,
        icon: int,
        _active_data: object,
        _active_prop_name: str,
        _index: int,
        _flt_flag: int,
    ) -> None:
        material_color_bind = item
        if not isinstance(material_color_bind, Vrm1MaterialColorBindPropertyGroup):
            return

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon_value=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        name = ""
        if material_color_bind.material:
            name = material_color_bind.material.name
            type_str = next(
                (
                    s
                    for (t, s, _, _) in Vrm1MaterialColorBindPropertyGroup.type_items
                    if t == material_color_bind.type
                ),
                None,
            )
            if type_str:
                name += " / " + type_str
        layout.label(text=name, translate=False, icon="MATERIAL")


class VRM_UL_vrm1_texture_transform_bind(UIList):
    bl_idname = "VRM_UL_vrm1_texture_transform_bind"

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        _data: object,
        item: object,
        icon: int,
        _active_data: object,
        _active_prop_name: str,
        _index: int,
        _flt_flag: int,
    ) -> None:
        texture_transform_bind = item
        if not isinstance(
            texture_transform_bind, Vrm1TextureTransformBindPropertyGroup
        ):
            return

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon_value=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        name = ""
        if texture_transform_bind.material:
            name = texture_transform_bind.material.name
        layout.label(text=name, translate=False, icon="MATERIAL")
