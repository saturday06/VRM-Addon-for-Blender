import bpy

from .property_group import (
    Vrm0BlendShapeBindPropertyGroup,
    Vrm0BlendShapeGroupPropertyGroup,
    Vrm0MaterialValueBindPropertyGroup,
    Vrm0SecondaryAnimationColliderGroupPropertyGroup,
    Vrm0SecondaryAnimationGroupPropertyGroup,
)


class VRM_UL_vrm0_secondary_animation_group(bpy.types.UIList):
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

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon_value=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        text = (
            f"(Spring Bone {index})" if bone_group.comment == "" else bone_group.comment
        )
        layout.label(text=text, translate=False, icon="GROUP_BONE")


class VRM_UL_vrm0_secondary_animation_collider_group(bpy.types.UIList):
    bl_idname = "VRM_UL_vrm0_secondary_animation_collider_group"

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

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon_value=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        layout.label(text=collider_group.name, translate=False, icon="SPHERE")


class VRM_UL_vrm0_blend_shape_group(bpy.types.UIList):
    bl_idname = "VRM_UL_vrm0_blend_shape_group"

    def draw_item(
        self,
        _context: bpy.types.Context,
        layout: bpy.types.UILayout,
        _data: object,
        item: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        _index: int,
        _flt_flag: int,
    ) -> None:
        blend_shape_group = item
        if not isinstance(blend_shape_group, Vrm0BlendShapeGroupPropertyGroup):
            return

        preset = {
            0: preset
            for preset in Vrm0BlendShapeGroupPropertyGroup.presets
            if preset.identifier == blend_shape_group.preset_name
        }.get(0)
        if not preset:
            return

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=preset.icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        text = blend_shape_group.name + " / " + preset.name
        split = layout.split(align=True, factor=0.55)
        split.label(text=text, translate=False, icon=preset.icon)
        split.prop(blend_shape_group, "preview", text="Preview")


class VRM_UL_vrm0_blend_shape_bind(bpy.types.UIList):
    bl_idname = "VRM_UL_vrm0_blend_shape_bind"

    def draw_item(
        self,
        context: bpy.types.Context,
        layout: bpy.types.UILayout,
        _data: object,
        item: object,
        icon: int,
        _active_data: object,
        _active_prop_name: str,
        _index: int,
        _flt_flag: int,
    ) -> None:
        blend_data = context.blend_data
        blend_shape_bind = item
        if not isinstance(blend_shape_bind, Vrm0BlendShapeBindPropertyGroup):
            return

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon_value=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        name = blend_shape_bind.mesh.mesh_object_name
        mesh_object = blend_data.objects.get(blend_shape_bind.mesh.mesh_object_name)
        if mesh_object:
            mesh_data = mesh_object.data
            if isinstance(mesh_data, bpy.types.Mesh):
                shape_keys = mesh_data.shape_keys
                if shape_keys:
                    keys = shape_keys.key_blocks.keys()
                    if blend_shape_bind.index in keys:
                        name += " / " + blend_shape_bind.index
        layout.label(text=name, translate=False, icon="MESH_DATA")


class VRM_UL_vrm0_material_value_bind(bpy.types.UIList):
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

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon_value=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        name = ""
        if material_value_bind.material:
            name = material_value_bind.material.name
            if material_value_bind.property_name:
                name += " / " + material_value_bind.property_name
        layout.label(text=name, translate=False, icon="MATERIAL")
