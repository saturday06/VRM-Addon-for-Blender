from typing import Optional

import bpy
from bpy.app.translations import pgettext

from ...common.logging import get_logger
from ...common.vrm1.human_bone import HumanBoneSpecifications
from .. import ops, search
from ..extension import (
    VrmAddonArmatureExtensionPropertyGroup,
    VrmAddonSceneExtensionPropertyGroup,
)
from ..migration import migrate
from ..panel import VRM_PT_vrm_armature_object_property
from . import ops as vrm1_ops
from .property_group import (
    Vrm1CustomExpressionPropertyGroup,
    Vrm1ExpressionPropertyGroup,
    Vrm1ExpressionsPropertyGroup,
    Vrm1FirstPersonPropertyGroup,
    Vrm1HumanBonePropertyGroup,
    Vrm1HumanBonesPropertyGroup,
    Vrm1HumanoidPropertyGroup,
    Vrm1LookAtPropertyGroup,
    Vrm1MetaPropertyGroup,
)

logger = get_logger(__name__)


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


def draw_vrm1_bone_prop_search(
    layout: bpy.types.UILayout,
    human_bone: Vrm1HumanBonePropertyGroup,
    icon: str,
) -> None:
    layout.prop_search(
        human_bone.node,
        "bone_name",
        human_bone,
        "node_candidates",
        text="",
        translate=False,
        icon=icon,
    )


def draw_vrm1_humanoid_required_bones_layout(
    human_bones: Vrm1HumanBonesPropertyGroup,
    layout: bpy.types.UILayout,
) -> None:
    split_factor = 0.2

    layout.label(text="VRM Required Bones", icon="ARMATURE_DATA")

    row = layout.row(align=True).split(factor=split_factor, align=True)
    column = row.column(align=True)
    column.label(text=HumanBoneSpecifications.HEAD.label)
    column.label(text=HumanBoneSpecifications.SPINE.label)
    column.label(text=HumanBoneSpecifications.HIPS.label)
    column = row.column(align=True)
    icon = "USER"
    draw_vrm1_bone_prop_search(column, human_bones.head, icon)
    draw_vrm1_bone_prop_search(column, human_bones.spine, icon)
    draw_vrm1_bone_prop_search(column, human_bones.hips, icon)

    row = layout.row(align=True).split(factor=split_factor, align=True)
    column = row.column(align=True)
    column.label(text="")
    column.label(text=HumanBoneSpecifications.LEFT_UPPER_ARM.label_no_left_right)
    column.label(text=HumanBoneSpecifications.LEFT_LOWER_ARM.label_no_left_right)
    column.label(text=HumanBoneSpecifications.LEFT_HAND.label_no_left_right)
    column.separator()
    column.label(text=HumanBoneSpecifications.LEFT_UPPER_LEG.label_no_left_right)
    column.label(text=HumanBoneSpecifications.LEFT_LOWER_LEG.label_no_left_right)
    column.label(text=HumanBoneSpecifications.LEFT_FOOT.label_no_left_right)

    column = row.column(align=True)
    column.label(text="Right")
    icon = "VIEW_PAN"
    draw_vrm1_bone_prop_search(column, human_bones.right_upper_arm, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_lower_arm, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_hand, icon)
    column.separator()
    icon = "MOD_DYNAMICPAINT"
    draw_vrm1_bone_prop_search(column, human_bones.right_upper_leg, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_lower_leg, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_foot, icon)

    column = row.column(align=True)
    column.label(text="Left")
    icon = "VIEW_PAN"
    draw_vrm1_bone_prop_search(column, human_bones.left_upper_arm, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_lower_arm, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_hand, icon)
    column.separator()
    icon = "MOD_DYNAMICPAINT"
    draw_vrm1_bone_prop_search(column, human_bones.left_upper_leg, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_lower_leg, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_foot, icon)


def draw_vrm1_humanoid_optional_bones_layout(
    human_bones: Vrm1HumanBonesPropertyGroup,
    layout: bpy.types.UILayout,
) -> None:
    split_factor = 0.2

    layout.label(text="VRM Optional Bones", icon="BONE_DATA")

    row = layout.row(align=True).split(factor=split_factor, align=True)
    icon = "HIDE_OFF"
    label_column = row.column(align=True)
    label_column.label(text="")
    label_column.label(text=HumanBoneSpecifications.LEFT_EYE.label_no_left_right)
    label_column.label(text=HumanBoneSpecifications.JAW.label)
    label_column.label(text=HumanBoneSpecifications.NECK.label)
    label_column.label(text=HumanBoneSpecifications.RIGHT_SHOULDER.label_no_left_right)
    label_column.label(text=HumanBoneSpecifications.UPPER_CHEST.label)
    label_column.label(text=HumanBoneSpecifications.CHEST.label)
    label_column.label(text=HumanBoneSpecifications.RIGHT_TOES.label_no_left_right)

    search_column = row.column(align=True)

    right_left_row = search_column.row(align=True)
    right_left_row.label(text="Right")
    right_left_row.label(text="Left")

    right_left_row = search_column.row(align=True)
    draw_vrm1_bone_prop_search(right_left_row, human_bones.right_eye, icon)
    draw_vrm1_bone_prop_search(right_left_row, human_bones.left_eye, icon)

    icon = "USER"
    draw_vrm1_bone_prop_search(search_column, human_bones.jaw, icon)
    draw_vrm1_bone_prop_search(search_column, human_bones.neck, icon)

    icon = "VIEW_PAN"
    right_left_row = search_column.row(align=True)
    draw_vrm1_bone_prop_search(right_left_row, human_bones.right_shoulder, icon)
    draw_vrm1_bone_prop_search(right_left_row, human_bones.left_shoulder, icon)

    icon = "USER"
    draw_vrm1_bone_prop_search(search_column, human_bones.upper_chest, icon)
    draw_vrm1_bone_prop_search(search_column, human_bones.chest, icon)

    icon = "MOD_DYNAMICPAINT"
    right_left_row = search_column.row(align=True)
    draw_vrm1_bone_prop_search(right_left_row, human_bones.right_toes, icon)
    draw_vrm1_bone_prop_search(right_left_row, human_bones.left_toes, icon)

    row = layout.row(align=True).split(factor=split_factor, align=True)
    column = row.column(align=True)
    column.label(text="", translate=False)
    column.label(text="Left Thumb:")
    column.label(text="Left Index:")
    column.label(text="Left Middle:")
    column.label(text="Left Ring:")
    column.label(text="Left Little:")
    column.separator()
    column.label(text="Right Thumb:")
    column.label(text="Right Index:")
    column.label(text="Right Middle:")
    column.label(text="Right Ring:")
    column.label(text="Right Little:")

    icon = "VIEW_PAN"
    column = row.column(align=True)
    column.label(text="Root")
    draw_vrm1_bone_prop_search(column, human_bones.left_thumb_metacarpal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_index_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_middle_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_ring_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_little_proximal, icon)
    column.separator()
    draw_vrm1_bone_prop_search(column, human_bones.right_thumb_metacarpal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_index_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_middle_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_ring_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_little_proximal, icon)

    column = row.column(align=True)
    column.label(text="", translate=False)
    draw_vrm1_bone_prop_search(column, human_bones.left_thumb_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_index_intermediate, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_middle_intermediate, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_ring_intermediate, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_little_intermediate, icon)
    column.separator()
    draw_vrm1_bone_prop_search(column, human_bones.right_thumb_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_index_intermediate, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_middle_intermediate, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_ring_intermediate, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_little_intermediate, icon)

    column = row.column(align=True)
    column.label(text="Tip")
    draw_vrm1_bone_prop_search(column, human_bones.left_thumb_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_index_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_middle_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_ring_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.left_little_distal, icon)
    column.separator()
    draw_vrm1_bone_prop_search(column, human_bones.right_thumb_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_index_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_middle_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_ring_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones.right_little_distal, icon)


def draw_vrm1_humanoid_layout(
    armature: bpy.types.Object,
    layout: bpy.types.UILayout,
    humanoid: Vrm1HumanoidPropertyGroup,
) -> None:
    if migrate(armature.name, defer=True):
        Vrm1HumanBonesPropertyGroup.check_last_bone_names_and_update(armature.data.name)

    data = armature.data
    human_bones = humanoid.human_bones

    armature_box = layout

    t_pose_box = armature_box.box()
    column = t_pose_box.row().column()
    column.label(text="VRM T-Pose", icon="OUTLINER_OB_ARMATURE")
    if bpy.app.version < (3, 0):
        column.label(text="Pose Library")
    else:
        column.label(text="Pose Asset")
    column.prop_search(
        humanoid, "pose_library", bpy.data, "actions", text="", translate=False
    )
    if humanoid.pose_library and humanoid.pose_library.pose_markers:
        column.label(text="Pose")
        column.prop_search(
            humanoid,
            "pose_marker_name",
            humanoid.pose_library,
            "pose_markers",
            text="",
            translate=False,
        )

    bone_operator_column = layout.column()
    bone_operator_column.operator(
        vrm1_ops.VRM_OT_assign_vrm1_humanoid_human_bones_automatically.bl_idname,
        icon="ARMATURE_DATA",
    ).armature_name = armature.name

    if ops.VRM_OT_simplify_vroid_bones.vroid_bones_exist(data):
        simplify_vroid_bones_op = armature_box.operator(
            ops.VRM_OT_simplify_vroid_bones.bl_idname,
            text=pgettext(ops.VRM_OT_simplify_vroid_bones.bl_label),
            icon="GREASEPENCIL",
        )
        simplify_vroid_bones_op.armature_name = armature.name

    draw_vrm1_humanoid_required_bones_layout(human_bones, armature_box.box())
    draw_vrm1_humanoid_optional_bones_layout(human_bones, armature_box.box())


class VRM_PT_vrm1_humanoid_armature_object_property(bpy.types.Panel):  # type: ignore[misc]
    bl_idname = "VRM_PT_vrm1_humanoid_armature_object_property"
    bl_label = "Humanoid"
    bl_translation_context = "VRM"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return active_object_is_vrm1_armature(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="ARMATURE_DATA")

    def draw(self, context: bpy.types.Context) -> None:
        draw_vrm1_humanoid_layout(
            context.active_object,
            self.layout,
            context.active_object.data.vrm_addon_extension.vrm1.humanoid,
        )


class VRM_PT_vrm1_humanoid_ui(bpy.types.Panel):  # type: ignore[misc]
    bl_idname = "VRM_PT_vrm1_humanoid_ui"
    bl_label = "Humanoid"
    bl_translation_context = "VRM"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.current_armature_is_vrm1(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="ARMATURE_DATA")

    def draw(self, context: bpy.types.Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        draw_vrm1_humanoid_layout(
            armature, self.layout, armature.data.vrm_addon_extension.vrm1.humanoid
        )


def draw_vrm1_first_person_layout(
    armature: bpy.types.Object,
    context: bpy.types.Context,
    layout: bpy.types.UILayout,
    first_person: Vrm1FirstPersonPropertyGroup,
) -> None:
    if migrate(armature.name, defer=True):
        VrmAddonSceneExtensionPropertyGroup.check_mesh_object_names_and_update(
            context.scene.name
        )
    box = layout.box()
    box.label(text="Mesh Annotations", icon="FULLSCREEN_EXIT")
    for mesh_annotation_index, mesh_annotation in enumerate(
        first_person.mesh_annotations
    ):
        row = box.row()
        row.prop_search(
            mesh_annotation.node,
            "mesh_object_name",
            context.scene.vrm_addon_extension,
            "mesh_object_names",
            text="",
            translate=False,
            icon="OUTLINER_OB_MESH",
        )
        row.prop(mesh_annotation, "type", text="", translate=False)
        remove_mesh_annotation_op = row.operator(
            vrm1_ops.VRM_OT_remove_vrm1_first_person_mesh_annotation.bl_idname,
            text="Remove",
            icon="REMOVE",
        )
        remove_mesh_annotation_op.armature_name = armature.name
        remove_mesh_annotation_op.mesh_annotation_index = mesh_annotation_index
    add_mesh_annotation_op = box.operator(
        vrm1_ops.VRM_OT_add_vrm1_first_person_mesh_annotation.bl_idname
    )
    add_mesh_annotation_op.armature_name = armature.name


class VRM_PT_vrm1_first_person_armature_object_property(bpy.types.Panel):  # type: ignore[misc]
    bl_idname = "VRM_PT_vrm1_first_person_armature_object_property"
    bl_label = "First Person"
    bl_translation_context = "VRM"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return active_object_is_vrm1_armature(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="HIDE_OFF")

    def draw(self, context: bpy.types.Context) -> None:
        draw_vrm1_first_person_layout(
            context.active_object,
            context,
            self.layout,
            context.active_object.data.vrm_addon_extension.vrm1.first_person,
        )


class VRM_PT_vrm1_first_person_ui(bpy.types.Panel):  # type: ignore[misc]
    bl_idname = "VRM_PT_vrm1_first_person_ui"
    bl_label = "First Person"
    bl_translation_context = "VRM"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.current_armature_is_vrm1(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="USER")

    def draw(self, context: bpy.types.Context) -> None:
        armature = search.current_armature(context)
        if (
            armature
            and hasattr(armature.data, "vrm_addon_extension")
            and isinstance(
                armature.data.vrm_addon_extension,
                VrmAddonArmatureExtensionPropertyGroup,
            )
        ):
            draw_vrm1_first_person_layout(
                armature,
                context,
                self.layout,
                armature.data.vrm_addon_extension.vrm1.first_person,
            )


def draw_vrm1_look_at_layout(
    armature: bpy.types.Object,
    _context: bpy.types.Context,
    layout: bpy.types.UILayout,
    look_at: Vrm1LookAtPropertyGroup,
) -> None:
    migrate(armature.name, defer=True)

    layout.prop(look_at, "offset_from_head_bone", icon="BONE_DATA")
    layout.prop(look_at, "type")

    column = layout.box().column(align=True)
    column.label(text="Range Map Horizontal Inner", icon="FULLSCREEN_EXIT")
    column.prop(look_at.range_map_horizontal_inner, "input_max_value")
    column.prop(look_at.range_map_horizontal_inner, "output_scale")
    column = layout.box().column(align=True)
    column.label(text="Range Map Horizontal Outer", icon="FULLSCREEN_ENTER")
    column.prop(look_at.range_map_horizontal_outer, "input_max_value")
    column.prop(look_at.range_map_horizontal_outer, "output_scale")
    column = layout.box().column(align=True)
    column.label(text="Range Map Vertical Up", icon="TRIA_UP")
    column.prop(look_at.range_map_vertical_up, "input_max_value")
    column.prop(look_at.range_map_vertical_up, "output_scale")
    column = layout.box().column(align=True)
    column.label(text="Range Map Vertical Down", icon="TRIA_DOWN")
    column.prop(look_at.range_map_vertical_down, "input_max_value")
    column.prop(look_at.range_map_vertical_down, "output_scale")


class VRM_PT_vrm1_look_at_armature_object_property(bpy.types.Panel):  # type: ignore[misc]
    bl_idname = "VRM_PT_vrm1_look_at_armature_object_property"
    bl_label = "Look At"
    bl_translation_context = "VRM"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return active_object_is_vrm1_armature(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="HIDE_OFF")

    def draw(self, context: bpy.types.Context) -> None:
        draw_vrm1_look_at_layout(
            context.active_object,
            context,
            self.layout,
            context.active_object.data.vrm_addon_extension.vrm1.look_at,
        )


class VRM_PT_vrm1_look_at_ui(bpy.types.Panel):  # type: ignore[misc]
    bl_idname = "VRM_PT_vrm1_look_at_ui"
    bl_label = "Look At"
    bl_translation_context = "VRM"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.current_armature_is_vrm1(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="HIDE_OFF")

    def draw(self, context: bpy.types.Context) -> None:
        armature = search.current_armature(context)
        if (
            armature
            and hasattr(armature.data, "vrm_addon_extension")
            and isinstance(
                armature.data.vrm_addon_extension,
                VrmAddonArmatureExtensionPropertyGroup,
            )
        ):
            draw_vrm1_look_at_layout(
                armature,
                context,
                self.layout,
                armature.data.vrm_addon_extension.vrm1.look_at,
            )


def draw_vrm1_expression_layout(
    armature: bpy.types.Object,
    context: bpy.types.Context,
    layout: bpy.types.UILayout,
    name: str,
    expression: Vrm1ExpressionPropertyGroup,
    custom_expression: Optional[Vrm1CustomExpressionPropertyGroup],
) -> None:
    blend_data = context.blend_data

    row = layout.row()
    row.alignment = "LEFT"
    row.prop(
        expression,
        "show_expanded",
        icon="TRIA_DOWN" if expression.show_expanded else "TRIA_RIGHT",
        emboss=False,
        text=name,
        translate=False,
    )
    if not expression.show_expanded:
        return

    box = layout.box().column()

    if custom_expression:
        box.row().prop(custom_expression, "custom_name")

    row = box.row()
    row.alignment = "LEFT"
    row.prop(
        expression,
        "show_expanded_morph_target_binds",
        icon="TRIA_DOWN"
        if expression.show_expanded_morph_target_binds
        else "TRIA_RIGHT",
        emboss=False,
    )
    if expression.show_expanded_morph_target_binds:
        VrmAddonSceneExtensionPropertyGroup.check_mesh_object_names_and_update(
            context.scene.name
        )
        for bind_index, bind in enumerate(expression.morph_target_binds):
            bind_box = box.box().column()
            bind_box.prop_search(
                bind.node,
                "mesh_object_name",
                context.scene.vrm_addon_extension,
                "mesh_object_names",
                text="Mesh",
                icon="OUTLINER_OB_MESH",
            )
            if (
                bind.node.mesh_object_name
                and bind.node.mesh_object_name in blend_data.objects
                and blend_data.objects[bind.node.mesh_object_name].data
                and blend_data.objects[bind.node.mesh_object_name].data.shape_keys
                and blend_data.objects[
                    bind.node.mesh_object_name
                ].data.shape_keys.key_blocks
                and blend_data.objects[
                    bind.node.mesh_object_name
                ].data.shape_keys.key_blocks.keys()
            ):
                bind_box.prop_search(
                    bind,
                    "index",
                    blend_data.objects[bind.node.mesh_object_name].data.shape_keys,
                    "key_blocks",
                    text="Shape key",
                )
            bind_box.prop(bind, "weight")

            remove_bind_op = bind_box.operator(
                vrm1_ops.VRM_OT_remove_vrm1_expression_morph_target_bind.bl_idname,
                icon="REMOVE",
            )
            remove_bind_op.armature_name = armature.name
            remove_bind_op.expression_name = name
            remove_bind_op.bind_index = bind_index

        add_bind_op = box.operator(
            vrm1_ops.VRM_OT_add_vrm1_expression_morph_target_bind.bl_idname,
            icon="ADD",
        )
        add_bind_op.armature_name = armature.name
        add_bind_op.expression_name = name

    row = box.row()
    row.alignment = "LEFT"
    row.prop(
        expression,
        "show_expanded_material_color_binds",
        icon="TRIA_DOWN"
        if expression.show_expanded_material_color_binds
        else "TRIA_RIGHT",
        emboss=False,
    )
    if expression.show_expanded_material_color_binds:
        for bind_index, bind in enumerate(expression.material_color_binds):
            bind_box = box.box().column()
            bind_box.prop_search(bind, "material", blend_data, "materials")
            bind_box.prop(bind, "type")
            target_value_split = bind_box.split(factor=0.5)
            target_value_split.label(text="Target Value:")
            if bind.type == "color":
                target_value_split.prop(bind, "target_value", text="", translate=False)
            else:
                target_value_split.prop(
                    bind, "target_value_as_rgb", text="", translate=False
                )

            remove_bind_op = bind_box.operator(
                vrm1_ops.VRM_OT_remove_vrm1_expression_material_color_bind.bl_idname,
                icon="REMOVE",
            )
            remove_bind_op.armature_name = armature.name
            remove_bind_op.expression_name = name
            remove_bind_op.bind_index = bind_index
        add_bind_op = box.operator(
            vrm1_ops.VRM_OT_add_vrm1_expression_material_color_bind.bl_idname,
            icon="ADD",
        )
        add_bind_op.armature_name = armature.name
        add_bind_op.expression_name = name

    row = box.row()
    row.alignment = "LEFT"
    row.prop(
        expression,
        "show_expanded_texture_transform_binds",
        icon="TRIA_DOWN"
        if expression.show_expanded_texture_transform_binds
        else "TRIA_RIGHT",
        emboss=False,
    )
    if expression.show_expanded_texture_transform_binds:
        for bind_index, bind in enumerate(expression.texture_transform_binds):
            bind_box = box.box().column()
            bind_box.prop_search(bind, "material", blend_data, "materials")
            bind_box.prop(bind, "scale")
            bind_box.prop(bind, "offset")

            remove_bind_op = bind_box.operator(
                vrm1_ops.VRM_OT_remove_vrm1_expression_texture_transform_bind.bl_idname,
                icon="REMOVE",
            )
            remove_bind_op.armature_name = armature.name
            remove_bind_op.expression_name = name
            remove_bind_op.bind_index = bind_index
        add_bind_op = box.operator(
            vrm1_ops.VRM_OT_add_vrm1_expression_texture_transform_bind.bl_idname,
            icon="ADD",
        )
        add_bind_op.armature_name = armature.name
        add_bind_op.expression_name = name

    box.prop(expression, "is_binary", icon="IPO_CONSTANT")
    box.prop(expression, "override_blink")
    box.prop(expression, "override_look_at")
    box.prop(expression, "override_mouth")

    if custom_expression:
        remove_custom_expression_op = box.operator(
            vrm1_ops.VRM_OT_remove_vrm1_expressions_custom_expression.bl_idname,
            icon="REMOVE",
        )
        remove_custom_expression_op.armature_name = armature.name
        remove_custom_expression_op.custom_expression_name = name


def draw_vrm1_expressions_layout(
    armature: bpy.types.Object,
    context: bpy.types.Context,
    layout: bpy.types.UILayout,
    expressions: Vrm1ExpressionsPropertyGroup,
) -> None:
    migrate(armature.name, defer=True)

    column = layout.column()
    for name, expression in expressions.preset_name_to_expression_dict().items():
        draw_vrm1_expression_layout(
            armature, context, column, name, expression, custom_expression=None
        )

    for custom_expression in expressions.custom:
        draw_vrm1_expression_layout(
            armature,
            context,
            column,
            custom_expression.custom_name,
            custom_expression.expression,
            custom_expression,
        )

    add_custom_expression_op = layout.operator(
        vrm1_ops.VRM_OT_add_vrm1_expressions_custom_expression.bl_idname,
        icon="ADD",
    )
    add_custom_expression_op.custom_expression_name = "new"
    add_custom_expression_op.armature_name = armature.name


class VRM_PT_vrm1_expressions_armature_object_property(bpy.types.Panel):  # type: ignore[misc]
    bl_idname = "VRM_PT_vrm1_expressions_armature_object_property"
    bl_label = "Expressions"
    bl_translation_context = "VRM"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return active_object_is_vrm1_armature(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="SHAPEKEY_DATA")

    def draw(self, context: bpy.types.Context) -> None:
        draw_vrm1_expressions_layout(
            context.active_object,
            context,
            self.layout,
            context.active_object.data.vrm_addon_extension.vrm1.expressions,
        )


class VRM_PT_vrm1_expressions_ui(bpy.types.Panel):  # type: ignore[misc]
    bl_idname = "VRM_PT_vrm1_expressions_ui"
    bl_label = "Expressions"
    bl_translation_context = "VRM"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.current_armature_is_vrm1(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="SHAPEKEY_DATA")

    def draw(self, context: bpy.types.Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        draw_vrm1_expressions_layout(
            armature,
            context,
            self.layout,
            armature.data.vrm_addon_extension.vrm1.expressions,
        )


def draw_vrm1_meta_layout(
    armature: bpy.types.Object,
    _context: bpy.types.Context,
    layout: bpy.types.UILayout,
    meta: Vrm1MetaPropertyGroup,
) -> None:
    migrate(armature.name, defer=True)

    thumbnail_column = layout.column()
    thumbnail_column.label(text="Thumbnail:")
    thumbnail_column.template_ID_preview(meta, "thumbnail_image")

    layout.prop(meta, "vrm_name", icon="FILE_BLEND")
    layout.prop(meta, "version", icon="LINENUMBERS_ON")

    authors_box = layout.box()
    authors_box.label(text="Authors:")
    if meta.authors:
        authors_row = authors_box.split(align=True, factor=0.7)
        authors_column = authors_row.column()
        for author in meta.authors:
            authors_column.prop(author, "value", text="", translate=False, icon="USER")
        if len(meta.authors) > 1:
            authors_remove_column = authors_row.column()
            for author_index in range(len(meta.authors)):
                remove_author_op = authors_remove_column.operator(
                    vrm1_ops.VRM_OT_remove_vrm1_meta_author.bl_idname,
                    text="Remove",
                    icon="REMOVE",
                )
                remove_author_op.armature_name = armature.name
                remove_author_op.author_index = author_index
    add_author_op = authors_box.operator(vrm1_ops.VRM_OT_add_vrm1_meta_author.bl_idname)
    add_author_op.armature_name = armature.name

    layout.prop(meta, "copyright_information")
    layout.prop(meta, "contact_information")

    references_box = layout.box()
    references_box.label(text="References:")
    if meta.references:
        references_row = references_box.split(align=True, factor=0.7)
        references_column = references_row.column()
        for reference in meta.references:
            references_column.prop(
                reference, "value", text="", translate=False, icon="URL"
            )
        if len(meta.references) > 1:
            references_remove_column = references_row.column()
            for reference_index in range(len(meta.references)):
                remove_reference_op = references_remove_column.operator(
                    vrm1_ops.VRM_OT_remove_vrm1_meta_reference.bl_idname,
                    text="Remove",
                    icon="REMOVE",
                )
                remove_reference_op.armature_name = armature.name
                remove_reference_op.reference_index = reference_index
    add_reference_op = references_box.operator(
        vrm1_ops.VRM_OT_add_vrm1_meta_reference.bl_idname
    )
    add_reference_op.armature_name = armature.name

    layout.prop(meta, "third_party_licenses")
    # layout.prop(meta, "license_url", icon="URL")
    layout.prop(meta, "avatar_permission", icon="MATCLOTH")
    layout.prop(meta, "commercial_usage", icon="SOLO_OFF")
    layout.prop(meta, "credit_notation")
    layout.prop(meta, "modification")
    layout.prop(meta, "allow_excessively_violent_usage")
    layout.prop(meta, "allow_excessively_sexual_usage")
    layout.prop(meta, "allow_political_or_religious_usage")
    layout.prop(meta, "allow_antisocial_or_hate_usage")
    layout.prop(meta, "allow_redistribution")
    layout.prop(meta, "other_license_url", icon="URL")


class VRM_PT_vrm1_meta_armature_object_property(bpy.types.Panel):  # type: ignore[misc]
    bl_idname = "VRM_PT_vrm1_meta_armature_object_property"
    bl_label = "Meta"
    bl_translation_context = "VRM"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return active_object_is_vrm1_armature(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="FILE_BLEND")

    def draw(self, context: bpy.types.Context) -> None:
        ext = context.active_object.data.vrm_addon_extension
        if isinstance(ext, VrmAddonArmatureExtensionPropertyGroup):
            draw_vrm1_meta_layout(
                context.active_object, context, self.layout, ext.vrm1.meta
            )


class VRM_PT_vrm1_meta_ui(bpy.types.Panel):  # type: ignore[misc]
    bl_idname = "VRM_PT_vrm1_meta_ui"
    bl_label = "Meta"
    bl_translation_context = "VRM"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.current_armature_is_vrm1(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="FILE_BLEND")

    def draw(self, context: bpy.types.Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        draw_vrm1_meta_layout(
            armature,
            context,
            self.layout,
            armature.data.vrm_addon_extension.vrm1.meta,
        )


class VRM_PT_vrm1_bone_property(bpy.types.Panel):  # type: ignore[misc]
    bl_idname = "VRM_PT_vrm1_bone_property"
    bl_label = "VRM"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "bone"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if (
            not context.active_object
            or context.active_object.type != "ARMATURE"
            or not context.active_object.data.bones.active
        ):
            return False
        return search.current_armature_is_vrm1(context)

    def draw(self, context: bpy.types.Context) -> None:
        # context.active_bone is a EditBone
        bone = context.active_object.data.bones.active
        ext = bone.vrm_addon_extension
        layout = self.layout
        layout.prop(ext, "axis_translation")
