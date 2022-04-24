from sys import float_info
from typing import Dict

import bpy
from bpy.app.translations import pgettext

from .. import search
from ..extension import VrmAddonArmatureExtensionPropertyGroup
from ..panel import VRM_PT_vrm_armature_object_property
from .property_group import NodeConstraint1NodeConstraintPropertyGroup


def active_object_is_vrm1_armature(context: bpy.types.Context) -> bool:
    return bool(
        context
        and context.active_object
        and context.active_object.type == "ARMATURE"
        and hasattr(context.active_object.data, "vrm_addon_extension")
        and isinstance(
            context.active_object.data.vrm_addon_extension,
            VrmAddonArmatureExtensionPropertyGroup,
        )
        and context.active_object.data.vrm_addon_extension.is_vrm1()
    )


def draw_node_constraint1_layout(
    armature: bpy.types.Object,
    layout: bpy.types.UILayout,
    node_constraint_props: NodeConstraint1NodeConstraintPropertyGroup,
) -> None:
    aim_constraints_box = layout.box()
    aim_constraints_row = aim_constraints_box.row()
    aim_constraints_row.alignment = "LEFT"
    aim_constraints_row.prop(
        node_constraint_props,
        "show_expanded_aim_constraints",
        icon="TRIA_DOWN"
        if node_constraint_props.show_expanded_aim_constraints
        else "TRIA_RIGHT",
        emboss=False,
    )
    if node_constraint_props.show_expanded_aim_constraints:
        aim_constraints_column = aim_constraints_box.column()
        aim_constraints: Dict[str, bpy.types.DampedTrackConstraint] = {}
        for bone in armature.pose.bones:
            for constraint in bone.constraints:
                if (
                    isinstance(constraint, bpy.types.DampedTrackConstraint)
                    and constraint.enabled
                    and abs(constraint.head_tail) < float_info.epsilon
                ):
                    aim_constraints[bone.name] = constraint
                    break
        if aim_constraints:
            aim_constraints_expanded_column = aim_constraints_column.column()
            for bone_name, aim_constraint in aim_constraints.items():
                aim_constraint_row = aim_constraints_expanded_column.row()
                aim_constraint_row.alignment = "LEFT"
                aim_constraint_row.label(
                    text=bone_name + ": " + aim_constraint.name,
                    icon="CONSTRAINT_BONE",
                    translate=False,
                )

        aim_constraints_help_column = aim_constraints_column.box().column()
        help_message = pgettext(
            "Aim Constraintになる条件\n"
            " - (仮の仕様です)\n"
            " - 有効\n"
            " - ボーンコンストレイント\n"
            " - 減衰トラック\n"
            " - ターゲットがボーン\n"
            " - ヘッド/テールが0\n"
            " - Bボーンに従わない\n"
            " - 複数が条件を満たす場合は一番上にあるもの\n"
        )
        for index, help_line in enumerate(help_message.splitlines()):
            aim_constraints_help_column.label(
                text=help_line, translate=False, icon="HELP" if index == 0 else "NONE"
            )


class VRM_PT_node_constraint1_armature_object_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_node_constraint1_armature_object_property"
    bl_label = "Node Constraint 1.0-Beta"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return active_object_is_vrm1_armature(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="CONSTRAINT")

    def draw(self, context: bpy.types.Context) -> None:
        draw_node_constraint1_layout(
            context.active_object,
            self.layout,
            context.active_object.data.vrm_addon_extension.node_constraint1,
        )


class VRM_PT_node_constraint1_ui(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_node_constraint1_ui"
    bl_label = "Node Constraint 1.0-Beta"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.current_armature_is_vrm1(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="CONSTRAINT")

    def draw(self, context: bpy.types.Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        draw_node_constraint1_layout(
            armature,
            self.layout,
            armature.data.vrm_addon_extension.node_constraint1,
        )
