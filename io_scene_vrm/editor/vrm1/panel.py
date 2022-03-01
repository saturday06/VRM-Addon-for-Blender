import bpy
from bpy.app.translations import pgettext

from ...common.human_bone import HumanBones
from .. import operator, search
from ..extension import VrmAddonArmatureExtensionPropertyGroup
from ..migration import migrate
from ..panel import VRM_PT_vrm_armature_object_property
from . import operator as vrm1_operator
from .property_group import (
    Vrm1ExpressionPropertyGroup,
    Vrm1ExpressionsPropertyGroup,
    Vrm1FirstPersonPropertyGroup,
    Vrm1HumanBonePropertyGroup,
    Vrm1HumanBonesPropertyGroup,
    Vrm1HumanoidPropertyGroup,
    Vrm1LookAtPropertyGroup,
    Vrm1MetaPropertyGroup,
    Vrm1SpringBonePropertyGroup,
)


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
    human_bone_props: Vrm1HumanBonePropertyGroup,
    icon: str,
) -> None:
    layout.prop_search(
        human_bone_props.node,
        "value",
        human_bone_props,
        "node_candidates",
        text="",
        translate=False,
        icon=icon,
    )


def draw_vrm1_humanoid_layout(
    armature: bpy.types.Object,
    layout: bpy.types.UILayout,
    humanoid_props: Vrm1HumanoidPropertyGroup,
) -> None:
    if migrate(armature.name, defer=True):
        Vrm1HumanBonesPropertyGroup.check_last_bone_names_and_update(armature.data.name)

    data = armature.data
    human_bones_props = humanoid_props.human_bones

    armature_box = layout
    t_pose_box = armature_box.box()
    column = t_pose_box.row().column()
    column.label(text="VRM T-Pose", icon="OUTLINER_OB_ARMATURE")
    column.label(text="Pose Library")
    column.prop_search(
        humanoid_props, "pose_library", bpy.data, "actions", text="", translate=False
    )
    column.label(text="Pose")
    if (
        humanoid_props.pose_library
        and humanoid_props.pose_library.name in bpy.data.actions
    ):
        column.prop_search(
            humanoid_props,
            "pose_marker_name",
            humanoid_props.pose_library,
            "pose_markers",
            text="",
            translate=False,
        )
    else:
        pose_marker_name_empty_box = column.box()
        pose_marker_name_empty_box.scale_y = 0.5
        pose_marker_name_empty_box.label(text="Current Pose")

    armature_box.operator(
        operator.VRM_OT_save_human_bone_mappings.bl_idname, icon="EXPORT"
    )
    armature_box.operator(
        operator.VRM_OT_load_human_bone_mappings.bl_idname, icon="IMPORT"
    )

    if operator.VRM_OT_simplify_vroid_bones.vroid_bones_exist(data):
        simplify_vroid_bones_op = armature_box.operator(
            operator.VRM_OT_simplify_vroid_bones.bl_idname,
            text=pgettext(operator.VRM_OT_simplify_vroid_bones.bl_label),
            icon="GREASEPENCIL",
        )
        simplify_vroid_bones_op.armature_name = armature.name

    split_factor = 0.2

    requires_box = armature_box.box()
    requires_box.label(text="VRM Required Bones", icon="ARMATURE_DATA")
    row = requires_box.row().split(factor=split_factor)
    column = row.column()
    column.label(text=HumanBones.HEAD.label)
    column.label(text=HumanBones.NECK.label)
    column.label(text=HumanBones.CHEST.label)
    column = row.column()
    icon = "USER"
    draw_vrm1_bone_prop_search(column, human_bones_props.head, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.spine, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.hips, icon)

    row = requires_box.row().split(factor=split_factor)
    column = row.column()
    column.label(text="")
    column.label(text=HumanBones.LEFT_UPPER_ARM.label_no_left_right)
    column.label(text=HumanBones.LEFT_LOWER_ARM.label_no_left_right)
    column.label(text=HumanBones.LEFT_HAND.label_no_left_right)
    column.separator()
    column.label(text=HumanBones.LEFT_UPPER_LEG.label_no_left_right)
    column.label(text=HumanBones.LEFT_LOWER_LEG.label_no_left_right)
    column.label(text=HumanBones.LEFT_FOOT.label_no_left_right)

    column = row.column()
    column.label(text="Right")
    icon = "VIEW_PAN"
    draw_vrm1_bone_prop_search(column, human_bones_props.right_upper_arm, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.right_lower_arm, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.right_hand, icon)
    column.separator()
    icon = "MOD_DYNAMICPAINT"
    draw_vrm1_bone_prop_search(column, human_bones_props.right_upper_leg, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.right_lower_leg, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.right_foot, icon)

    column = row.column()
    column.label(text="Left")
    icon = "VIEW_PAN"
    draw_vrm1_bone_prop_search(column, human_bones_props.left_upper_arm, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.left_lower_arm, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.left_hand, icon)
    column.separator()
    icon = "MOD_DYNAMICPAINT"
    draw_vrm1_bone_prop_search(column, human_bones_props.left_upper_leg, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.left_lower_leg, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.left_foot, icon)

    defines_box = armature_box.box()
    defines_box.label(text="VRM Optional Bones", icon="BONE_DATA")

    row = defines_box.row().split(factor=split_factor)
    icon = "HIDE_OFF"
    column = row.column()
    column.label(text="")
    column.label(text=HumanBones.LEFT_EYE.label_no_left_right)
    column = row.column()
    column.label(text="Right")
    draw_vrm1_bone_prop_search(column, human_bones_props.right_eye, icon)
    column = row.column()
    column.label(text="Left")
    draw_vrm1_bone_prop_search(column, human_bones_props.left_eye, icon)

    row = defines_box.row().split(factor=split_factor)
    column = row.column()
    column.label(text=HumanBones.JAW.label)
    column.label(text=HumanBones.UPPER_CHEST.label)
    column.label(text=HumanBones.SPINE.label)
    column.label(text=HumanBones.HIPS.label)

    column = row.column()
    icon = "USER"
    draw_vrm1_bone_prop_search(column, human_bones_props.jaw, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.neck, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.upper_chest, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.chest, icon)

    split_factor = 0.5
    row = defines_box.row().split(factor=split_factor)
    column = row.column()
    column.label(text=HumanBones.RIGHT_SHOULDER.label)
    column.label(text=HumanBones.RIGHT_THUMB_PROXIMAL.label)
    column.label(text=HumanBones.RIGHT_THUMB_INTERMEDIATE.label)
    column.label(text=HumanBones.RIGHT_THUMB_DISTAL.label)
    column.label(text=HumanBones.RIGHT_INDEX_PROXIMAL.label)
    column.label(text=HumanBones.RIGHT_INDEX_INTERMEDIATE.label)
    column.label(text=HumanBones.RIGHT_INDEX_DISTAL.label)
    column.label(text=HumanBones.RIGHT_MIDDLE_PROXIMAL.label)
    column.label(text=HumanBones.RIGHT_MIDDLE_INTERMEDIATE.label)
    column.label(text=HumanBones.RIGHT_MIDDLE_DISTAL.label)
    column.label(text=HumanBones.RIGHT_RING_PROXIMAL.label)
    column.label(text=HumanBones.RIGHT_RING_INTERMEDIATE.label)
    column.label(text=HumanBones.RIGHT_RING_DISTAL.label)
    column.label(text=HumanBones.RIGHT_LITTLE_PROXIMAL.label)
    column.label(text=HumanBones.RIGHT_LITTLE_INTERMEDIATE.label)
    column.label(text=HumanBones.RIGHT_LITTLE_DISTAL.label)
    column.label(text=HumanBones.RIGHT_TOES.label)

    column = row.column()
    icon = "USER"
    draw_vrm1_bone_prop_search(column, human_bones_props.right_shoulder, icon)
    icon = "VIEW_PAN"
    draw_vrm1_bone_prop_search(column, human_bones_props.right_thumb_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.right_thumb_intermediate, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.right_thumb_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.right_index_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.right_index_intermediate, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.right_index_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.right_middle_proximal, icon)
    draw_vrm1_bone_prop_search(
        column, human_bones_props.right_middle_intermediate, icon
    )
    draw_vrm1_bone_prop_search(column, human_bones_props.right_middle_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.right_ring_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.right_ring_intermediate, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.right_ring_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.right_little_proximal, icon)
    draw_vrm1_bone_prop_search(
        column, human_bones_props.right_little_intermediate, icon
    )
    draw_vrm1_bone_prop_search(column, human_bones_props.right_little_distal, icon)
    icon = "MOD_DYNAMICPAINT"
    draw_vrm1_bone_prop_search(column, human_bones_props.right_toes, icon)

    row = defines_box.row().split(factor=split_factor)
    column = row.column()
    column.label(text=HumanBones.LEFT_SHOULDER.label)
    column.label(text=HumanBones.LEFT_THUMB_PROXIMAL.label)
    column.label(text=HumanBones.LEFT_THUMB_INTERMEDIATE.label)
    column.label(text=HumanBones.LEFT_THUMB_DISTAL.label)
    column.label(text=HumanBones.LEFT_INDEX_PROXIMAL.label)
    column.label(text=HumanBones.LEFT_INDEX_INTERMEDIATE.label)
    column.label(text=HumanBones.LEFT_INDEX_DISTAL.label)
    column.label(text=HumanBones.LEFT_MIDDLE_PROXIMAL.label)
    column.label(text=HumanBones.LEFT_MIDDLE_INTERMEDIATE.label)
    column.label(text=HumanBones.LEFT_MIDDLE_DISTAL.label)
    column.label(text=HumanBones.LEFT_RING_PROXIMAL.label)
    column.label(text=HumanBones.LEFT_RING_INTERMEDIATE.label)
    column.label(text=HumanBones.LEFT_RING_DISTAL.label)
    column.label(text=HumanBones.LEFT_LITTLE_PROXIMAL.label)
    column.label(text=HumanBones.LEFT_LITTLE_INTERMEDIATE.label)
    column.label(text=HumanBones.LEFT_LITTLE_DISTAL.label)
    column.label(text=HumanBones.LEFT_TOES.label)

    column = row.column()
    icon = "USER"
    draw_vrm1_bone_prop_search(column, human_bones_props.left_shoulder, icon)
    icon = "VIEW_PAN"
    draw_vrm1_bone_prop_search(column, human_bones_props.left_thumb_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.left_thumb_intermediate, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.left_thumb_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.left_index_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.left_index_intermediate, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.left_index_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.left_middle_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.left_middle_intermediate, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.left_middle_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.left_ring_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.left_ring_intermediate, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.left_ring_distal, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.left_little_proximal, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.left_little_intermediate, icon)
    draw_vrm1_bone_prop_search(column, human_bones_props.left_little_distal, icon)
    icon = "MOD_DYNAMICPAINT"
    draw_vrm1_bone_prop_search(column, human_bones_props.left_toes, icon)


class VRM_PT_vrm1_humanoid_armature_object_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm1_humanoid_armature_object_property"
    bl_label = "VRM 1.0-Beta Humanoid"
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
            context.active_object.data.vrm_addon_extension.vrm1.vrm.humanoid,
        )


class VRM_PT_vrm1_humanoid_ui(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm1_humanoid_ui"
    bl_label = "VRM 1.0-Beta Humanoid"
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
        if not armature:
            return
        draw_vrm1_humanoid_layout(
            armature, self.layout, armature.data.vrm_addon_extension.vrm1.vrm.humanoid
        )


def draw_vrm1_first_person_layout(
    armature: bpy.types.Object,
    context: bpy.types.Context,
    layout: bpy.types.UILayout,
    first_person_props: Vrm1FirstPersonPropertyGroup,
) -> None:
    migrate(armature.name, defer=True)
    blend_data = context.blend_data
    box = layout.box()
    box.label(text="Mesh Annotations", icon="FULLSCREEN_EXIT")
    for mesh_annotation_index, mesh_annotation in enumerate(
        first_person_props.mesh_annotations
    ):
        row = box.row()
        row.prop_search(
            mesh_annotation.node,
            "value",
            blend_data,
            "meshes",
            text="",
            translate=False,
        )
        row.prop(mesh_annotation, "first_person_flag", text="", translate=False)
        remove_mesh_annotation_op = row.operator(
            vrm1_operator.VRM_OT_remove_vrm1_first_person_mesh_annotation.bl_idname,
            text="Remove",
            icon="REMOVE",
        )
        remove_mesh_annotation_op.armature_data_name = armature.data.name
        remove_mesh_annotation_op.mesh_annotation_index = mesh_annotation_index
    add_mesh_annotation_op = box.operator(
        vrm1_operator.VRM_OT_add_vrm1_first_person_mesh_annotation.bl_idname
    )
    add_mesh_annotation_op.armature_data_name = armature.data.name


class VRM_PT_vrm1_first_person_armature_object_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm1_first_person_armature_object_property"
    bl_label = "VRM 1.0-Beta First Person"
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
            context.active_object.data.vrm_addon_extension.vrm1.vrm.first_person,
        )


class VRM_PT_vrm1_first_person_ui(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm1_first_person_ui"
    bl_label = "VRM 1.0-Beta First Person"
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
            draw_vrm1_first_person_layout(
                armature,
                context,
                self.layout,
                armature.data.vrm_addon_extension.vrm1.vrm.first_person,
            )


def draw_vrm1_look_at_layout(
    armature: bpy.types.Object,
    _context: bpy.types.Context,
    layout: bpy.types.UILayout,
    look_at_props: Vrm1LookAtPropertyGroup,
) -> None:
    migrate(armature.name, defer=True)

    layout.prop(look_at_props, "offset_from_head_bone", icon="BONE_DATA")
    layout.prop(look_at_props, "type")

    box = layout.box()
    box.label(text="Range Map Horizontal Inner", icon="FULLSCREEN_EXIT")
    box.prop(look_at_props.range_map_horizontal_inner, "input_max_value")
    box.prop(look_at_props.range_map_horizontal_inner, "output_scale")
    box = layout.box()
    box.label(text="Range Map Horizontal Outer", icon="FULLSCREEN_ENTER")
    box.prop(look_at_props.range_map_horizontal_outer, "input_max_value")
    box.prop(look_at_props.range_map_horizontal_outer, "output_scale")
    box = layout.box()
    box.label(text="Range Map Vertical Up", icon="TRIA_UP")
    box.prop(look_at_props.range_map_vertical_up, "input_max_value")
    box.prop(look_at_props.range_map_vertical_up, "output_scale")
    box = layout.box()
    box.label(text="Range Map Vertical Down", icon="TRIA_DOWN")
    box.prop(look_at_props.range_map_vertical_down, "input_max_value")
    box.prop(look_at_props.range_map_vertical_down, "output_scale")


class VRM_PT_vrm1_look_at_armature_object_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm1_look_at_armature_object_property"
    bl_label = "VRM 1.0-Beta Look at"
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
            context.active_object.data.vrm_addon_extension.vrm1.vrm.look_at,
        )


class VRM_PT_vrm1_look_at_ui(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm1_look_at_ui"
    bl_label = "VRM 1.0-Beta Look At"
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
                armature.data.vrm_addon_extension.vrm1.vrm.look_at,
            )


def draw_vrm1_expression_layout(
    armature: bpy.types.Object,
    context: bpy.types.Context,
    layout: bpy.types.UILayout,
    name: str,
    expression_props: Vrm1ExpressionPropertyGroup,
    removable: bool,
) -> None:
    blend_data = context.blend_data

    row = layout.row()
    row.alignment = "LEFT"
    row.prop(
        expression_props,
        "show_expanded",
        icon="TRIA_DOWN" if expression_props.show_expanded else "TRIA_RIGHT",
        emboss=False,
        text=name,
        translate=False,
    )
    if not expression_props.show_expanded:
        return

    box = layout.box()
    row = box.row()
    row.alignment = "LEFT"
    row.prop(
        expression_props,
        "show_expanded_morph_target_binds",
        icon="TRIA_DOWN"
        if expression_props.show_expanded_morph_target_binds
        else "TRIA_RIGHT",
        emboss=False,
    )
    if expression_props.show_expanded_morph_target_binds:
        for bind_index, bind_props in enumerate(expression_props.morph_target_binds):
            bind_box = box.box()
            bind_box.prop_search(
                bind_props.node, "value", blend_data, "meshes", text="Mesh"
            )
            if (
                bind_props.node.value
                and bind_props.node.value in blend_data.meshes
                and blend_data.meshes[bind_props.node.value]
                and blend_data.meshes[bind_props.node.value].shape_keys
                and blend_data.meshes[bind_props.node.value].shape_keys.key_blocks
                and blend_data.meshes[
                    bind_props.node.value
                ].shape_keys.key_blocks.keys()
            ):
                bind_box.prop_search(
                    bind_props,
                    "index",
                    blend_data.meshes[bind_props.node.value].shape_keys,
                    "key_blocks",
                    text="Shape key",
                )
            bind_box.prop(bind_props, "weight")

            remove_bind_op = bind_box.operator(
                vrm1_operator.VRM_OT_remove_vrm1_expression_morph_target_bind.bl_idname,
                icon="REMOVE",
            )
            remove_bind_op.armature_data_name = armature.data.name
            remove_bind_op.expression_name = name
            remove_bind_op.bind_index = bind_index

        add_bind_op = box.operator(
            vrm1_operator.VRM_OT_add_vrm1_expression_morph_target_bind.bl_idname,
            icon="ADD",
        )
        add_bind_op.armature_data_name = armature.data.name
        add_bind_op.expression_name = name

    row = box.row()
    row.alignment = "LEFT"
    row.prop(
        expression_props,
        "show_expanded_material_color_binds",
        icon="TRIA_DOWN"
        if expression_props.show_expanded_material_color_binds
        else "TRIA_RIGHT",
        emboss=False,
    )
    if expression_props.show_expanded_material_color_binds:
        for bind_index, bind_props in enumerate(expression_props.material_color_binds):
            bind_box = box.box()
            bind_box.prop_search(bind_props, "material", blend_data, "materials")
            bind_box.prop(bind_props, "type")
            bind_box.prop(bind_props, "target_value")

            remove_bind_op = bind_box.operator(
                vrm1_operator.VRM_OT_remove_vrm1_expression_material_color_bind.bl_idname,
                icon="REMOVE",
            )
            remove_bind_op.armature_data_name = armature.data.name
            remove_bind_op.expression_name = name
            remove_bind_op.bind_index = bind_index
        add_bind_op = box.operator(
            vrm1_operator.VRM_OT_add_vrm1_expression_material_color_bind.bl_idname,
            icon="ADD",
        )
        add_bind_op.armature_data_name = armature.data.name
        add_bind_op.expression_name = name

    row = box.row()
    row.alignment = "LEFT"
    row.prop(
        expression_props,
        "show_expanded_texture_transform_binds",
        icon="TRIA_DOWN"
        if expression_props.show_expanded_texture_transform_binds
        else "TRIA_RIGHT",
        emboss=False,
    )
    if expression_props.show_expanded_texture_transform_binds:
        for bind_index, bind_props in enumerate(
            expression_props.texture_transform_binds
        ):
            bind_box = box.box()
            bind_box.prop_search(bind_props, "material", blend_data, "materials")
            bind_box.prop(bind_props, "scale")
            bind_box.prop(bind_props, "offset")

            remove_bind_op = bind_box.operator(
                vrm1_operator.VRM_OT_remove_vrm1_expression_texture_transform_bind.bl_idname,
                icon="REMOVE",
            )
            remove_bind_op.armature_data_name = armature.data.name
            remove_bind_op.expression_name = name
            remove_bind_op.bind_index = bind_index
        add_bind_op = box.operator(
            vrm1_operator.VRM_OT_add_vrm1_expression_texture_transform_bind.bl_idname,
            icon="ADD",
        )
        add_bind_op.armature_data_name = armature.data.name
        add_bind_op.expression_name = name

    box.prop(expression_props, "is_binary", icon="IPO_CONSTANT")
    box.prop(expression_props, "override_blink")
    box.prop(expression_props, "override_look_at")
    box.prop(expression_props, "override_mouth")

    if removable:
        remove_custom_expression_op = box.operator(
            vrm1_operator.VRM_OT_remove_vrm1_expressions_custom_expression.bl_idname,
            icon="REMOVE",
        )
        remove_custom_expression_op.armature_data_name = armature.data.name
        remove_custom_expression_op.custom_expression_name = name


def draw_vrm1_expressions_layout(
    armature: bpy.types.Object,
    context: bpy.types.Context,
    layout: bpy.types.UILayout,
    expressions_props: Vrm1ExpressionsPropertyGroup,
) -> None:
    migrate(armature.name, defer=True)

    for (
        name,
        expression_props,
    ) in expressions_props.all_name_to_expression_dict().items():
        removable = name not in expressions_props.preset_name_to_expression_dict()
        draw_vrm1_expression_layout(
            armature, context, layout, name, expression_props, removable
        )

    add_custom_expression_op = layout.operator(
        vrm1_operator.VRM_OT_add_vrm1_expressions_custom_expression.bl_idname,
        icon="ADD",
    )
    add_custom_expression_op.custom_expression_name = "New"
    add_custom_expression_op.armature_data_name = armature.data.name


class VRM_PT_vrm1_expressions_armature_object_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm1_expressions_armature_object_property"
    bl_label = "VRM 1.0-Beta Expressions"
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
            context.active_object.data.vrm_addon_extension.vrm1.vrm.expressions,
        )


class VRM_PT_vrm1_expressions_ui(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm1_expressions_ui"
    bl_label = "VRM 1.0-Beta Expressions"
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
            armature.data.vrm_addon_extension.vrm1.vrm.expressions,
        )


def draw_vrm1_spring_bone_layout(
    armature: bpy.types.Object,
    layout: bpy.types.UILayout,
    spring_bone_props: Vrm1SpringBonePropertyGroup,
) -> None:
    migrate(armature.name, defer=True)

    colliders_box = layout.box()
    colliders_row = colliders_box.row()
    colliders_row.alignment = "LEFT"
    colliders_row.prop(
        spring_bone_props,
        "show_expanded_colliders",
        icon="TRIA_DOWN" if spring_bone_props.show_expanded_colliders else "TRIA_RIGHT",
        emboss=False,
    )
    if spring_bone_props.show_expanded_colliders:
        colliders_expanded_box = colliders_box.box().column()
        for collider_index, collider_props in enumerate(spring_bone_props.colliders):
            if not collider_props.blender_object:  # TODO: restore
                continue

            collider_row = colliders_expanded_box.row()
            collider_row.alignment = "LEFT"
            collider_row.prop(
                collider_props,
                "show_expanded",
                icon="TRIA_DOWN" if collider_props.show_expanded else "TRIA_RIGHT",
                emboss=False,
                text=collider_props.blender_object.name,
                translate=False,
            )

            if not collider_props.show_expanded:
                continue

            collider_column = colliders_expanded_box.box().column()
            collider_column.prop(
                collider_props.blender_object, "name", icon="MESH_UVSPHERE", text=""
            )
            collider_column.prop(collider_props.shape, "shape")
            collider_column.prop_search(
                collider_props.node, "value", armature.data, "bones"
            )
            remove_collider_op = collider_column.operator(
                vrm1_operator.VRM_OT_remove_vrm1_spring_bone_collider.bl_idname,
                icon="REMOVE",
                text="Remove",
            )
            remove_collider_op.armature_data_name = armature.data.name
            remove_collider_op.collider_index = collider_index

        add_collider_op = colliders_box.operator(
            vrm1_operator.VRM_OT_add_vrm1_spring_bone_collider.bl_idname,
            icon="ADD",
        )
        add_collider_op.armature_data_name = armature.data.name

    collider_groups_box = layout.box()
    collider_groups_row = collider_groups_box.row()
    collider_groups_row.alignment = "LEFT"
    collider_groups_row.prop(
        spring_bone_props,
        "show_expanded_collider_groups",
        icon="TRIA_DOWN"
        if spring_bone_props.show_expanded_collider_groups
        else "TRIA_RIGHT",
        emboss=False,
    )
    if spring_bone_props.show_expanded_collider_groups:
        collider_groups_expanded_box = collider_groups_box.box().column()
        for collider_group_index, collider_group_props in enumerate(
            spring_bone_props.collider_groups
        ):

            collider_group_row = collider_groups_expanded_box.row()
            collider_group_row.alignment = "LEFT"
            collider_group_row.prop(
                collider_group_props,
                "show_expanded",
                icon="TRIA_DOWN"
                if collider_group_props.show_expanded
                else "TRIA_RIGHT",
                emboss=False,
                text="COLL",
                translate=False,
            )

            if not collider_group_props.show_expanded:
                continue

            collider_group_column = collider_groups_expanded_box.box().column()
            collider_group_column.prop(
                collider_group_props,
                "name",
            )
            for _collider_index, collider_props in collider_group_props.colliders:
                collider_group_column.prop_search(
                    collider_props,
                    "name",
                )

            remove_collider_group_op = collider_group_column.operator(
                vrm1_operator.VRM_OT_remove_vrm1_spring_bone_collider_group.bl_idname,
                icon="REMOVE",
            )
            remove_collider_group_op.armature_data_name = armature.data.name
            remove_collider_group_op.collider_group_index = collider_group_index
        add_collider_group_op = collider_groups_box.operator(
            vrm1_operator.VRM_OT_add_vrm1_spring_bone_collider_group.bl_idname,
            icon="ADD",
        )
        add_collider_group_op.armature_data_name = armature.data.name

    springs_box = layout.box()
    springs_row = springs_box.row()
    springs_row.alignment = "LEFT"
    springs_row.prop(
        spring_bone_props,
        "show_expanded_springs",
        icon="TRIA_DOWN" if spring_bone_props.show_expanded_springs else "TRIA_RIGHT",
        emboss=False,
    )
    if spring_bone_props.show_expanded_springs:
        springs_expanded_box = springs_box.box().column()
        for spring_index, spring_props in enumerate(spring_bone_props.springs):
            spring_row = springs_expanded_box.row()
            spring_row.alignment = "LEFT"
            spring_row.prop(
                spring_props,
                "show_expanded",
                icon="TRIA_DOWN" if spring_props.show_expanded else "TRIA_RIGHT",
                emboss=False,
                text="SPR",
                translate=False,
            )
            if not spring_props.show_expanded:
                continue

            spring_column = springs_expanded_box.box().column()

            remove_spring_op = spring_column.operator(
                vrm1_operator.VRM_OT_remove_vrm1_spring_bone_spring.bl_idname,
                icon="REMOVE",
            )
            remove_spring_op.armature_data_name = armature.data.name
            remove_spring_op.spring_index = spring_index
        add_spring_op = springs_box.operator(
            vrm1_operator.VRM_OT_add_vrm1_spring_bone_spring.bl_idname,
            icon="ADD",
        )
        add_spring_op.armature_data_name = armature.data.name


class VRM_PT_vrm1_spring_bone_armature_object_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm1_spring_bone_armature_object_property"
    bl_label = "VRM 1.0-Beta Spring Bone"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return active_object_is_vrm1_armature(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="PHYSICS")

    def draw(self, context: bpy.types.Context) -> None:
        draw_vrm1_spring_bone_layout(
            context.active_object,
            self.layout,
            context.active_object.data.vrm_addon_extension.vrm1.spring_bone,
        )


class VRM_PT_vrm1_spring_bone_ui(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm1_spring_bone_ui"
    bl_label = "VRM 1.0-Beta Spring Bone"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.current_armature_is_vrm1(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="PHYSICS")

    def draw(self, context: bpy.types.Context) -> None:
        armature = search.current_armature(context)
        if not armature:
            return
        draw_vrm1_spring_bone_layout(
            armature,
            self.layout,
            armature.data.vrm_addon_extension.vrm1.spring_bone,
        )


def draw_vrm1_meta_layout(
    armature: bpy.types.Object,
    context: bpy.types.Context,
    layout: bpy.types.UILayout,
    meta_props: Vrm1MetaPropertyGroup,
) -> None:
    migrate(armature.name, defer=True)
    blend_data = context.blend_data

    layout.prop_search(meta_props, "thumbnail_image", blend_data, "images")

    layout.prop(meta_props, "name", icon="FILE_BLEND")
    layout.prop(meta_props, "version", icon="LINENUMBERS_ON")

    authors_box = layout.box()
    authors_box.label(text="Authors:")
    if len(meta_props.authors) > 0:
        authors_row = authors_box.split(align=True, factor=0.7)
        authors_prop_column = authors_row.column()
        for author_props in meta_props.authors:
            authors_prop_column.prop(
                author_props, "value", text="", translate=False, icon="USER"
            )
    if len(meta_props.authors) > 1:
        authors_remove_column = authors_row.column()
        for author_index in range(len(meta_props.authors)):
            remove_author_op = authors_remove_column.operator(
                vrm1_operator.VRM_OT_remove_vrm1_meta_author.bl_idname,
                text="Remove",
                icon="REMOVE",
            )
            remove_author_op.armature_data_name = armature.data.name
            remove_author_op.author_index = author_index
    add_author_op = authors_box.operator(
        vrm1_operator.VRM_OT_add_vrm1_meta_author.bl_idname
    )
    add_author_op.armature_data_name = armature.data.name

    layout.prop(meta_props, "copyright_information")
    layout.prop(meta_props, "contact_information")

    references_box = layout.box()
    references_box.label(text="References:")
    if len(meta_props.references) > 0:
        references_row = references_box.split(align=True, factor=0.7)
        references_prop_column = references_row.column()
        for reference_props in meta_props.references:
            references_prop_column.prop(
                reference_props, "value", text="", translate=False, icon="URL"
            )
    if len(meta_props.references) > 1:
        references_remove_column = references_row.column()
        for reference_index in range(len(meta_props.references)):
            remove_reference_op = references_remove_column.operator(
                vrm1_operator.VRM_OT_remove_vrm1_meta_reference.bl_idname,
                text="Remove",
                icon="REMOVE",
            )
            remove_reference_op.armature_data_name = armature.data.name
            remove_reference_op.reference_index = reference_index
    add_reference_op = references_box.operator(
        vrm1_operator.VRM_OT_add_vrm1_meta_reference.bl_idname
    )
    add_reference_op.armature_data_name = armature.data.name

    layout.prop(meta_props, "third_party_licenses")
    layout.prop(meta_props, "license_url", icon="URL")
    layout.prop(meta_props, "avatar_permission", icon="MATCLOTH")
    layout.prop(meta_props, "commercial_usage", icon="SOLO_OFF")
    layout.prop(meta_props, "credit_notation")
    layout.prop(meta_props, "modification")
    layout.prop(meta_props, "allow_excessively_violent_usage")
    layout.prop(meta_props, "allow_excessively_sexual_usage")
    layout.prop(meta_props, "allow_political_or_religious_usage")
    layout.prop(meta_props, "allow_antisocial_or_hate_usage")
    layout.prop(meta_props, "allow_redistribution")
    layout.prop(meta_props, "other_license_url", icon="URL")


class VRM_PT_vrm1_meta_armature_object_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm1_meta_armature_object_property"
    bl_label = "VRM 1.0-Beta Meta"
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
                context.active_object, context, self.layout, ext.vrm1.vrm.meta
            )


class VRM_PT_vrm1_meta_ui(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm1_meta_ui"
    bl_label = "VRM 1.0-Beta Meta"
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
            armature.data.vrm_addon_extension.vrm1.vrm.meta,
        )
