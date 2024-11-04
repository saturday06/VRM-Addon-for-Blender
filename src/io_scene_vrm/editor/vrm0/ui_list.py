# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from bpy.types import Context, Mesh, UILayout, UIList

from ..extension import get_armature_extension
from ..property_group import BonePropertyGroup, StringPropertyGroup
from .property_group import (
    Vrm0BlendShapeBindPropertyGroup,
    Vrm0BlendShapeGroupPropertyGroup,
    Vrm0FirstPersonPropertyGroup,
    Vrm0MaterialValueBindPropertyGroup,
    Vrm0MeshAnnotationPropertyGroup,
    Vrm0SecondaryAnimationColliderGroupPropertyGroup,
    Vrm0SecondaryAnimationColliderPropertyGroup,
    Vrm0SecondaryAnimationGroupPropertyGroup,
)


class VRM_UL_vrm0_first_person_mesh_annotation(UIList):
    bl_idname = "VRM_UL_vrm0_first_person_mesh_annotation"

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
        if not isinstance(first_person, Vrm0FirstPersonPropertyGroup):
            return
        if not isinstance(mesh_annotation, Vrm0MeshAnnotationPropertyGroup):
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
                mesh_annotation.mesh,
                "bpy_object",
                icon=icon,
                text="",
                translate=False,
            )
        else:
            row.label(
                text=mesh_annotation.mesh.mesh_object_name,
                translate=False,
                icon=icon,
            )
        row.prop(mesh_annotation, "first_person_flag", text="", translate=False)


class VRM_UL_vrm0_secondary_animation_group(UIList):
    bl_idname = "VRM_UL_vrm0_secondary_animation_group"

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        _data: object,
        bone_group: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        _index: int,
        _flt_flag: int,
    ) -> None:
        if not isinstance(bone_group, Vrm0SecondaryAnimationGroupPropertyGroup):
            return

        icon = "BONE_DATA"

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        text = ""
        if bone_group.bones:
            text = (
                "(" + ", ".join(str(bone.bone_name) for bone in bone_group.bones) + ")"
            )

        if bone_group.center.bone_name:
            if text:
                text = " - " + text
            text = bone_group.center.bone_name + text

        if bone_group.comment:
            if text:
                text = " / " + text
            text = bone_group.comment + text

        if not text:
            text = "(EMPTY)"

        layout.label(text=text, translate=False, icon=icon)


class VRM_UL_vrm0_secondary_animation_group_bone(UIList):
    bl_idname = "VRM_UL_vrm0_secondary_animation_group_bone"

    def draw_item(
        self,
        context: Context,
        layout: UILayout,
        bone_group: object,
        bone: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        index: int,
        _flt_flag: int,
    ) -> None:
        if not isinstance(bone_group, Vrm0SecondaryAnimationGroupPropertyGroup):
            return
        if not isinstance(bone, BonePropertyGroup):
            return
        armature = context.blend_data.armatures.get(bone.armature_data_name)
        if armature is None:
            return

        icon = "BONE_DATA"

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        if index == bone_group.active_bone_index:
            layout.prop_search(
                bone,
                "bone_name",
                armature,
                "bones",
                text="",
                translate=False,
                icon=icon,
            )
        else:
            layout.label(text=bone.bone_name, translate=False, icon=icon)


class VRM_UL_vrm0_secondary_animation_group_collider_group(UIList):
    bl_idname = "VRM_UL_vrm0_secondary_animation_group_collider_group"

    def draw_item(
        self,
        context: Context,
        layout: UILayout,
        bone_group: object,
        collider_group: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        index: int,
        _flt_flag: int,
    ) -> None:
        if not isinstance(bone_group, Vrm0SecondaryAnimationGroupPropertyGroup):
            return
        if not isinstance(collider_group, StringPropertyGroup):
            return

        secondary_animation = None
        for armature in context.blend_data.armatures:
            ext = get_armature_extension(armature).vrm0
            if any(bone_group == bg for bg in ext.secondary_animation.bone_groups):
                secondary_animation = ext.secondary_animation
                break
        if secondary_animation is None:
            return

        icon = "PIVOT_INDIVIDUAL"

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        if index == bone_group.active_collider_group_index:
            layout.prop_search(
                collider_group,
                "value",
                secondary_animation,
                "collider_groups",
                text="",
                translate=False,
                icon=icon,
            )
        else:
            layout.label(text=collider_group.value, translate=False, icon=icon)


class VRM_UL_vrm0_secondary_animation_collider_group(UIList):
    bl_idname = "VRM_UL_vrm0_secondary_animation_collider_group"

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        _data: object,
        collider_group: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        _index: int,
        _flt_flag: int,
    ) -> None:
        if not isinstance(
            collider_group, Vrm0SecondaryAnimationColliderGroupPropertyGroup
        ):
            return

        icon = "SPHERE"

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        layout.label(text=collider_group.name, translate=False, icon=icon)


class VRM_UL_vrm0_secondary_animation_collider_group_collider(UIList):
    bl_idname = "VRM_UL_vrm0_secondary_animation_collider_group_collider"

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
        collider_group: object,
        collider: object,
        _icon: int,
        _active_data: object,
        _active_prop_name: str,
        index: int,
        _flt_flag: int,
    ) -> None:
        if not isinstance(
            collider_group, Vrm0SecondaryAnimationColliderGroupPropertyGroup
        ):
            return
        if not isinstance(collider, Vrm0SecondaryAnimationColliderPropertyGroup):
            return

        icon = "MESH_UVSPHERE"

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        if collider.bpy_object is None:
            return

        row = layout.split(align=True, factor=0.7)
        if index == collider_group.active_collider_index:
            row.prop(
                collider.bpy_object,
                "name",
                icon=icon,
                translate=False,
                text="",
            )
            row.prop(collider.bpy_object, "empty_display_size", text="")
        else:
            row.label(text=collider.bpy_object.name, icon=icon, translate=False)
            row.prop(collider.bpy_object, "empty_display_size", text="", emboss=False)


class VRM_UL_vrm0_blend_shape_group(UIList):
    bl_idname = "VRM_UL_vrm0_blend_shape_group"

    def draw_item(
        self,
        _context: Context,
        layout: UILayout,
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

        preset = next(
            (
                preset
                for preset in blend_shape_group.preset_name_enum
                if preset.identifier == blend_shape_group.preset_name
            ),
            None,
        )
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


class VRM_UL_vrm0_blend_shape_bind(UIList):
    bl_idname = "VRM_UL_vrm0_blend_shape_bind"

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
            if isinstance(mesh_data, Mesh):
                shape_keys = mesh_data.shape_keys
                if shape_keys:
                    keys = shape_keys.key_blocks.keys()
                    if blend_shape_bind.index in keys:
                        name += " / " + blend_shape_bind.index
        layout.label(text=name, translate=False, icon="MESH_DATA")


class VRM_UL_vrm0_material_value_bind(UIList):
    bl_idname = "VRM_UL_vrm0_material_value_bind"

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
