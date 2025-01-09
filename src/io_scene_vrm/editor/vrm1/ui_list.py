# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from bpy.types import Context, Mesh, UILayout, UIList

from ...common.logger import get_logger
from ..property_group import StringPropertyGroup
from .property_group import (
    Vrm1ExpressionsPropertyGroup,
    Vrm1FirstPersonPropertyGroup,
    Vrm1MaterialColorBindPropertyGroup,
    Vrm1MeshAnnotationPropertyGroup,
    Vrm1MetaPropertyGroup,
    Vrm1MorphTargetBindPropertyGroup,
    Vrm1TextureTransformBindPropertyGroup,
)

logger = get_logger(__name__)


class VRM_UL_vrm1_meta_author(UIList):
    bl_idname = "VRM_UL_vrm1_meta_author"

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        meta: object,
        author: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        index: int,
        _flt_flag: int,
    ) -> None:
        if not isinstance(meta, Vrm1MetaPropertyGroup):
            return
        if not isinstance(author, StringPropertyGroup):
            return

        icon = "USER"

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        if index == meta.active_author_index:
            layout.prop(author, "value", icon=icon, text="", translate=False)
        else:
            layout.label(text=author.value, icon=icon, translate=False)


class VRM_UL_vrm1_meta_reference(UIList):
    bl_idname = "VRM_UL_vrm1_meta_reference"

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        meta: object,
        reference: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        index: int,
        _flt_flag: int,
    ) -> None:
        if not isinstance(meta, Vrm1MetaPropertyGroup):
            return
        if not isinstance(reference, StringPropertyGroup):
            return

        icon = "URL"

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        if index == meta.active_reference_index:
            layout.prop(reference, "value", icon=icon, text="", translate=False)
        else:
            layout.label(text=reference.value, icon=icon, translate=False)


class VRM_UL_vrm1_first_person_mesh_annotation(UIList):
    bl_idname = "VRM_UL_vrm1_first_person_mesh_annotation"

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        first_person: object,
        mesh_annotation: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        index: int,
        _flt_flag: int,
    ) -> None:
        if not isinstance(first_person, Vrm1FirstPersonPropertyGroup):
            return
        if not isinstance(mesh_annotation, Vrm1MeshAnnotationPropertyGroup):
            return

        icon = "OUTLINER_OB_MESH"

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        row = layout.split(factor=0.6, align=True)
        if index == first_person.active_mesh_annotation_index:
            row.prop(
                mesh_annotation.node,
                "bpy_object",
                text="",
                translate=False,
                icon=icon,
            )
        else:
            row.label(
                text=mesh_annotation.node.mesh_object_name,
                translate=False,
                icon=icon,
            )
        row.prop(mesh_annotation, "type", text="", translate=False)


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
        if not isinstance(expressions, Vrm1ExpressionsPropertyGroup):
            return
        preset_expression_items = list(
            expressions.preset.name_to_expression_dict().items()
        )
        if index < len(preset_expression_items):
            name, expression = preset_expression_items[index]
            icon = expressions.preset.get_icon(name)
            if not icon:
                logger.error("Unknown preset expression: %s", name)
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
        morph_target_bind: object,
        icon: int,
        _active_data: object,
        _active_prop_name: str,
        _index: int,
        _flt_flag: int,
    ) -> None:
        blend_data = context.blend_data
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
        material_color_bind: object,
        icon: int,
        _active_data: object,
        _active_prop_name: str,
        _index: int,
        _flt_flag: int,
    ) -> None:
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
            type_name = next(
                (
                    enum.name
                    for enum in Vrm1MaterialColorBindPropertyGroup.type_enum
                    if enum.identifier == material_color_bind.type
                ),
                None,
            )
            if type_name:
                name += " / " + type_name
        layout.label(text=name, translate=False, icon="MATERIAL")


class VRM_UL_vrm1_texture_transform_bind(UIList):
    bl_idname = "VRM_UL_vrm1_texture_transform_bind"

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        _data: object,
        texture_transform_bind: object,
        icon: int,
        _active_data: object,
        _active_prop_name: str,
        _index: int,
        _flt_flag: int,
    ) -> None:
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
