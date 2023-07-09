import bpy

from .property_group import (
    Vrm0BlendShapeBindPropertyGroup,
    Vrm0BlendShapeGroupPropertyGroup,
    Vrm0MaterialValueBindPropertyGroup,
    Vrm0SecondaryAnimationColliderGroupPropertyGroup,
    Vrm0SecondaryAnimationGroupPropertyGroup,
)


class VRM_UL_vrm0_secondary_animation_group(bpy.types.UIList):  # type: ignore[misc]
    bl_idname = "VRM_UL_vrm0_secondary_animation_group"

    def draw_item(
        self,
        _context: bpy.types.Context,
        layout: bpy.types.UILayout,
        _data: object,
        item: object,
        icon: int,
        _active_data: object,
        _active_prop_name: str,
        index: int,
        _flt_flag: int,
    ) -> None:
        bone_group = item
        if not isinstance(bone_group, Vrm0SecondaryAnimationGroupPropertyGroup):
            return

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            text = (
                f"(Spring Bone {index})"
                if bone_group.comment == ""
                else bone_group.comment
            )
            if bone_group:
                layout.label(text=text, icon="GROUP_BONE")
                # layout.prop(bone_group, "comment", text="", emboss=False, icon_value=icon)
            else:
                layout.label(text="", translate=False, icon_value=icon)
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)


class VRM_UL_vrm0_secondary_animation_group_collider_group(bpy.types.UIList):  # type: ignore[misc]
    bl_idname = "VRM_UL_vrm0_secondary_animation_group_collider_group"

    def draw_item(
        self,
        _context: bpy.types.Context,
        layout: bpy.types.UILayout,
        _data: object,
        item: object,
        icon: int,
        _active_data: object,
        _active_prop_name: str,
        _index: int,
        _flt_flag: int,
    ) -> None:
        collider_group = item
        if not isinstance(
            collider_group, Vrm0SecondaryAnimationColliderGroupPropertyGroup
        ):
            return

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            if collider_group:
                layout.label(text=collider_group.name, icon="SPHERE")
            else:
                layout.label(text="", translate=False, icon_value=icon)
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)


class VRM_UL_vrm0_blend_shape_group(bpy.types.UIList):  # type: ignore[misc]
    bl_idname = "VRM_UL_vrm0_blend_shape_group"

    def draw_item(
        self,
        _context: bpy.types.Context,
        layout: bpy.types.UILayout,
        _data: object,
        item: object,
        icon: int,
        _active_data: object,
        _active_prop_name: str,
        _index: int,
        _flt_flag: int,
    ) -> None:
        blend_shape_group = item
        if not isinstance(blend_shape_group, Vrm0BlendShapeGroupPropertyGroup):
            return

        _icon = (
            blend_shape_group.bl_rna.properties["preset_name"]
            .enum_items[blend_shape_group.preset_name]
            .icon
        )
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            if blend_shape_group:
                layout.label(text=blend_shape_group.name, icon=_icon)
                # layout.prop(blend_shape_group, "preset_name", text="")
            else:
                layout.label(text="", translate=False, icon_value=icon)
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)


class VRM_UL_vrm0_blend_shape_bind(bpy.types.UIList):  # type: ignore[misc]
    bl_idname = "VRM_UL_vrm0_blend_shape_bind"

    def draw_item(
        self,
        _context: bpy.types.Context,
        layout: bpy.types.UILayout,
        _data: object,
        item: object,
        icon: int,
        _active_data: object,
        _active_prop_name: str,
        _index: int,
        _flt_flag: int,
    ) -> None:
        blend_shape_bind = item
        if not isinstance(blend_shape_bind, Vrm0BlendShapeBindPropertyGroup):
            return

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            if blend_shape_bind:
                layout.label(text=str(blend_shape_bind.mesh), icon="MESH_DATA")
            else:
                layout.label(text="", translate=False, icon_value=icon)
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)


class VRM_UL_vrm0_material_value_bind(bpy.types.UIList):  # type: ignore[misc]
    bl_idname = "VRM_UL_vrm0_material_value_bind"

    def draw_item(
        self,
        _context: bpy.types.Context,
        layout: bpy.types.UILayout,
        _data: object,
        item: object,
        icon: int,
        _active_data: object,
        _active_prop_name: str,
        _index: int,
        _flt_flag: int,
    ) -> None:
        material_value_bind = item
        if not isinstance(material_value_bind, Vrm0MaterialValueBindPropertyGroup):
            return

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            if material_value_bind:
                layout.label(text=str(material_value_bind.material), icon="MATERIAL")
                # layout.prop(blend_shape_group, "preset_name")
            else:
                layout.label(text="", translate=False, icon_value=icon)
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)
