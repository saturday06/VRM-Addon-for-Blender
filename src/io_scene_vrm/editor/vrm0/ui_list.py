# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from bpy.types import Armature, Context, Mesh, UILayout, UIList

from ...common import convert
from ...common.logger import get_logger
from ..menu import VRM_MT_bone_assignment
from ..property_group import BonePropertyGroup
from .menu import VRM_MT_vrm0_secondary_animation_group_collider_group
from .property_group import (
    Vrm0BlendShapeBindPropertyGroup,
    Vrm0BlendShapeGroupPropertyGroup,
    Vrm0FirstPersonPropertyGroup,
    Vrm0MaterialValueBindPropertyGroup,
    Vrm0MeshAnnotationPropertyGroup,
    Vrm0SecondaryAnimationColliderGroupPropertyGroup,
    Vrm0SecondaryAnimationColliderGroupReferencePropertyGroup,
    Vrm0SecondaryAnimationColliderPropertyGroup,
    Vrm0SecondaryAnimationGroupPropertyGroup,
)

logger = get_logger(__name__)


class VRM_UL_vrm0_first_person_mesh_annotation(UIList):
    bl_idname = "VRM_UL_vrm0_first_person_mesh_annotation"

    def filter_items(
        self,
        _context: Context,
        data: object,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        items = convert.sequence_or_none(getattr(data, propname, None))
        if items is None:
            return ([], [])

        flt_flags: list[int] = [self.bitflag_filter_item] * len(items)
        flt_neworder: list[int] = []

        filter_name: str = self.filter_name.casefold()
        if not filter_name:
            return (flt_flags, flt_neworder)

        for index, item in enumerate(items):
            if (
                isinstance(item, Vrm0MeshAnnotationPropertyGroup)
                and filter_name in item.mesh.mesh_object_name.casefold()
            ):
                continue
            flt_flags[index] = 0

        return (flt_flags, flt_neworder)

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

    def format_label_text(
        self, bone_group: Vrm0SecondaryAnimationGroupPropertyGroup
    ) -> str:
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

        return text

    def filter_items(
        self,
        _context: Context,
        data: object,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        items = convert.sequence_or_none(getattr(data, propname, None))
        if items is None:
            return ([], [])

        flt_flags: list[int] = [self.bitflag_filter_item] * len(items)
        flt_neworder: list[int] = []

        filter_name: str = self.filter_name.casefold()
        if not filter_name:
            return (flt_flags, flt_neworder)

        for index, item in enumerate(items):
            if (
                isinstance(item, Vrm0SecondaryAnimationGroupPropertyGroup)
                and filter_name in self.format_label_text(item).casefold()
            ):
                continue
            flt_flags[index] = 0

        return (flt_flags, flt_neworder)

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

        layout.label(
            text=self.format_label_text(bone_group) or "(EMPTY)",
            translate=False,
            icon=icon,
        )


class VRM_UL_vrm0_secondary_animation_group_bone(UIList):
    bl_idname = "VRM_UL_vrm0_secondary_animation_group_bone"

    def filter_items(
        self,
        _context: Context,
        data: object,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        items = convert.sequence_or_none(getattr(data, propname, None))
        if items is None:
            return ([], [])

        flt_flags: list[int] = [self.bitflag_filter_item] * len(items)
        flt_neworder: list[int] = []

        filter_name: str = self.filter_name.casefold()
        if not filter_name:
            return (flt_flags, flt_neworder)

        for index, item in enumerate(items):
            if (
                isinstance(item, BonePropertyGroup)
                and filter_name in item.bone_name.casefold()
            ):
                continue
            flt_flags[index] = 0

        return (flt_flags, flt_neworder)

    def draw_item(
        self,
        _context: Context,
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

        icon = "BONE_DATA"

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        if index == bone_group.active_bone_index:
            VRM_MT_bone_assignment.draw_input_layout(
                layout,
                bone,
                icon=icon,
                simple=True,
            )
        else:
            layout.label(text=bone.bone_name, translate=False, icon=icon)


class VRM_UL_vrm0_secondary_animation_group_collider_group(UIList):
    bl_idname = "VRM_UL_vrm0_secondary_animation_group_collider_group"

    def filter_items(
        self,
        _context: Context,
        data: object,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        items = convert.sequence_or_none(getattr(data, propname, None))
        if items is None:
            return ([], [])

        flt_flags: list[int] = [self.bitflag_filter_item] * len(items)
        flt_neworder: list[int] = []

        filter_name: str = self.filter_name.casefold()
        if not filter_name:
            return (flt_flags, flt_neworder)

        for index, item in enumerate(items):
            if (
                isinstance(
                    item, Vrm0SecondaryAnimationColliderGroupReferencePropertyGroup
                )
                and filter_name in item.collider_group_display_name.casefold()
            ):
                continue
            flt_flags[index] = 0

        return (flt_flags, flt_neworder)

    def draw_item(
        self,
        _context: Context,
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
        if not isinstance(
            collider_group, Vrm0SecondaryAnimationColliderGroupReferencePropertyGroup
        ):
            return

        armature_data = bone_group.id_data
        if not isinstance(armature_data, Armature):
            logger.error("Failed to find armature")
            return

        icon = "PIVOT_INDIVIDUAL"

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        if index == bone_group.active_collider_group_index:
            VRM_MT_vrm0_secondary_animation_group_collider_group.draw_input_layout(
                layout,
                bone_group,
                collider_group,
                icon=icon,
            )
        else:
            layout.label(
                text=collider_group.collider_group_display_name,
                translate=False,
                icon=icon,
            )


class VRM_UL_vrm0_secondary_animation_collider_group(UIList):
    bl_idname = "VRM_UL_vrm0_secondary_animation_collider_group"

    def filter_items(
        self,
        _context: Context,
        data: object,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        items = convert.sequence_or_none(getattr(data, propname, None))
        if items is None:
            return ([], [])

        flt_flags: list[int] = [self.bitflag_filter_item] * len(items)
        flt_neworder: list[int] = []

        filter_name: str = self.filter_name.casefold()
        if not filter_name:
            return (flt_flags, flt_neworder)

        for index, item in enumerate(items):
            if (
                isinstance(item, Vrm0SecondaryAnimationColliderGroupPropertyGroup)
                and filter_name in item.display_name.casefold()
            ):
                continue
            flt_flags[index] = 0

        return (flt_flags, flt_neworder)

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

        layout.label(text=collider_group.display_name, translate=False, icon=icon)


class VRM_UL_vrm0_secondary_animation_collider_group_collider(UIList):
    bl_idname = "VRM_UL_vrm0_secondary_animation_collider_group_collider"

    def filter_items(
        self,
        _context: Context,
        data: object,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        items = convert.sequence_or_none(getattr(data, propname, None))
        if items is None:
            return ([], [])

        flt_flags: list[int] = [self.bitflag_filter_item] * len(items)
        flt_neworder: list[int] = []

        filter_name: str = self.filter_name.casefold()
        if not filter_name:
            return (flt_flags, flt_neworder)

        for index, item in enumerate(items):
            if (
                isinstance(item, Vrm0SecondaryAnimationColliderPropertyGroup)
                and (bpy_object := item.bpy_object)
                and filter_name in bpy_object.name.casefold()
            ):
                continue
            flt_flags[index] = 0

        return (flt_flags, flt_neworder)

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

        bpy_object = collider.bpy_object
        if bpy_object is None:
            return

        row = layout.split(align=True, factor=0.7)
        if index == collider_group.active_collider_index:
            row.prop(
                bpy_object,
                "name",
                icon=icon,
                translate=False,
                text="",
            )
            row.prop(bpy_object, "empty_display_size", text="")
        else:
            row.label(text=bpy_object.name, icon=icon, translate=False)
            row.prop(bpy_object, "empty_display_size", text="", emboss=False)


class VRM_UL_vrm0_blend_shape_group(UIList):
    bl_idname = "VRM_UL_vrm0_blend_shape_group"

    def filter_items(
        self,
        _context: Context,
        data: object,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        items = convert.sequence_or_none(getattr(data, propname, None))
        if items is None:
            return ([], [])

        flt_flags: list[int] = [self.bitflag_filter_item] * len(items)
        flt_neworder: list[int] = []

        filter_name: str = self.filter_name.casefold()
        if not filter_name:
            return (flt_flags, flt_neworder)

        for index, item in enumerate(items):
            if (
                isinstance(item, Vrm0BlendShapeGroupPropertyGroup)
                and filter_name in item.name.casefold()
            ):
                continue
            flt_flags[index] = 0

        return (flt_flags, flt_neworder)

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

    def format_label_text(
        self, context: Context, blend_shape_bind: Vrm0BlendShapeBindPropertyGroup
    ) -> str:
        text = blend_shape_bind.mesh.mesh_object_name
        mesh_object = context.blend_data.objects.get(
            blend_shape_bind.mesh.mesh_object_name
        )
        if mesh_object:
            mesh_data = mesh_object.data
            if isinstance(mesh_data, Mesh):
                shape_keys = mesh_data.shape_keys
                if shape_keys:
                    keys = shape_keys.key_blocks.keys()
                    if blend_shape_bind.index in keys:
                        text += " / " + blend_shape_bind.index
        return text

    def filter_items(
        self,
        context: Context,
        data: object,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        items = convert.sequence_or_none(getattr(data, propname, None))
        if items is None:
            return ([], [])

        flt_flags: list[int] = [self.bitflag_filter_item] * len(items)
        flt_neworder: list[int] = []

        filter_name: str = self.filter_name.casefold()
        if not filter_name:
            return (flt_flags, flt_neworder)

        for index, item in enumerate(items):
            if (
                isinstance(item, Vrm0BlendShapeBindPropertyGroup)
                and filter_name in self.format_label_text(context, item).casefold()
            ):
                continue
            flt_flags[index] = 0

        return (flt_flags, flt_neworder)

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
        blend_shape_bind = item
        if not isinstance(blend_shape_bind, Vrm0BlendShapeBindPropertyGroup):
            return

        if self.layout_type == "GRID":
            layout.alignment = "CENTER"
            layout.label(text="", translate=False, icon_value=icon)
            return

        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return

        layout.label(
            text=self.format_label_text(context, blend_shape_bind),
            translate=False,
            icon="MESH_DATA",
        )


class VRM_UL_vrm0_material_value_bind(UIList):
    bl_idname = "VRM_UL_vrm0_material_value_bind"

    def format_label_text(
        self, material_value_bind: Vrm0MaterialValueBindPropertyGroup
    ) -> str:
        text = ""
        material = material_value_bind.material
        if material:
            text = material.name
            if material_value_bind.property_name:
                text += " / " + material_value_bind.property_name
        return text

    def filter_items(
        self,
        _context: Context,
        data: object,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        items = convert.sequence_or_none(getattr(data, propname, None))
        if items is None:
            return ([], [])

        flt_flags: list[int] = [self.bitflag_filter_item] * len(items)
        flt_neworder: list[int] = []

        filter_name: str = self.filter_name.casefold()
        if not filter_name:
            return (flt_flags, flt_neworder)

        for index, item in enumerate(items):
            if (
                isinstance(item, Vrm0MaterialValueBindPropertyGroup)
                and filter_name in self.format_label_text(item).casefold()
            ):
                continue
            flt_flags[index] = 0

        return (flt_flags, flt_neworder)

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

        layout.label(
            text=self.format_label_text(material_value_bind),
            translate=False,
            icon="MATERIAL",
        )
