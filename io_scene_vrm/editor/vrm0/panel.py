import bpy
from bpy.app.translations import pgettext

from ...common.human_bone import HumanBone, HumanBones
from .. import operator, search
from ..extension import VrmAddonArmatureExtensionPropertyGroup
from ..migration import migrate
from ..panel import VRM_PT_vrm_armature_object_property
from . import operator as vrm0_operator
from .property_group import (
    Vrm0BlendShapeMasterPropertyGroup,
    Vrm0FirstPersonPropertyGroup,
    Vrm0HumanoidPropertyGroup,
    Vrm0MetaPropertyGroup,
    Vrm0SecondaryAnimationPropertyGroup,
)


def bone_prop_search(
    layout: bpy.types.UILayout,
    human_bone: HumanBone,
    icon: str,
    humanoid_props: Vrm0HumanoidPropertyGroup,
) -> None:
    props = None
    for human_bone_props in humanoid_props.human_bones:
        if human_bone_props.bone == human_bone.name.value:
            props = human_bone_props
            break
    if not props:
        return

    layout.prop_search(
        props.node,
        "value",
        props,
        "node_candidates",
        text="",
        translate=False,
        icon=icon,
    )


def draw_vrm0_humanoid_layout(
    armature: bpy.types.Object,
    layout: bpy.types.UILayout,
    humanoid_props: Vrm0HumanoidPropertyGroup,
) -> None:
    if migrate(armature.name, defer=True):
        Vrm0HumanoidPropertyGroup.check_last_bone_names_and_update(armature.data.name)

    data = armature.data

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
    column.label(text=HumanBones.SPINE.label)
    column.label(text=HumanBones.HIPS.label)
    column = row.column()
    icon = "USER"
    bone_prop_search(column, HumanBones.HEAD, icon, humanoid_props)
    bone_prop_search(column, HumanBones.NECK, icon, humanoid_props)
    bone_prop_search(column, HumanBones.CHEST, icon, humanoid_props)
    bone_prop_search(column, HumanBones.SPINE, icon, humanoid_props)
    bone_prop_search(column, HumanBones.HIPS, icon, humanoid_props)

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
    bone_prop_search(column, HumanBones.RIGHT_UPPER_ARM, icon, humanoid_props)
    bone_prop_search(column, HumanBones.RIGHT_LOWER_ARM, icon, humanoid_props)
    bone_prop_search(column, HumanBones.RIGHT_HAND, icon, humanoid_props)
    column.separator()
    icon = "MOD_DYNAMICPAINT"
    bone_prop_search(column, HumanBones.RIGHT_UPPER_LEG, icon, humanoid_props)
    bone_prop_search(column, HumanBones.RIGHT_LOWER_LEG, icon, humanoid_props)
    bone_prop_search(column, HumanBones.RIGHT_FOOT, icon, humanoid_props)

    column = row.column()
    column.label(text="Left")
    icon = "VIEW_PAN"
    bone_prop_search(column, HumanBones.LEFT_UPPER_ARM, icon, humanoid_props)
    bone_prop_search(column, HumanBones.LEFT_LOWER_ARM, icon, humanoid_props)
    bone_prop_search(column, HumanBones.LEFT_HAND, icon, humanoid_props)
    column.separator()
    icon = "MOD_DYNAMICPAINT"
    bone_prop_search(column, HumanBones.LEFT_UPPER_LEG, icon, humanoid_props)
    bone_prop_search(column, HumanBones.LEFT_LOWER_LEG, icon, humanoid_props)
    bone_prop_search(column, HumanBones.LEFT_FOOT, icon, humanoid_props)

    defines_box = armature_box.box()
    defines_box.label(text="VRM Optional Bones", icon="BONE_DATA")

    row = defines_box.row().split(factor=split_factor)
    icon = "HIDE_OFF"
    column = row.column()
    column.label(text="")
    column.label(text=HumanBones.LEFT_EYE.label_no_left_right)
    column = row.column()
    column.label(text="Right")
    bone_prop_search(column, HumanBones.RIGHT_EYE, icon, humanoid_props)
    column = row.column()
    column.label(text="Left")
    bone_prop_search(column, HumanBones.LEFT_EYE, icon, humanoid_props)

    row = defines_box.row().split(factor=split_factor)
    column = row.column()
    column.label(text=HumanBones.JAW.label)
    column.label(text=HumanBones.UPPER_CHEST.label)

    column = row.column()
    icon = "USER"
    bone_prop_search(column, HumanBones.JAW, icon, humanoid_props)
    bone_prop_search(column, HumanBones.UPPER_CHEST, icon, humanoid_props)

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
    bone_prop_search(column, HumanBones.RIGHT_SHOULDER, icon, humanoid_props)
    icon = "VIEW_PAN"
    bone_prop_search(column, HumanBones.RIGHT_THUMB_PROXIMAL, icon, humanoid_props)
    bone_prop_search(column, HumanBones.RIGHT_THUMB_INTERMEDIATE, icon, humanoid_props)
    bone_prop_search(column, HumanBones.RIGHT_THUMB_DISTAL, icon, humanoid_props)
    bone_prop_search(column, HumanBones.RIGHT_INDEX_PROXIMAL, icon, humanoid_props)
    bone_prop_search(column, HumanBones.RIGHT_INDEX_INTERMEDIATE, icon, humanoid_props)
    bone_prop_search(column, HumanBones.RIGHT_INDEX_DISTAL, icon, humanoid_props)
    bone_prop_search(column, HumanBones.RIGHT_MIDDLE_PROXIMAL, icon, humanoid_props)
    bone_prop_search(column, HumanBones.RIGHT_MIDDLE_INTERMEDIATE, icon, humanoid_props)
    bone_prop_search(column, HumanBones.RIGHT_MIDDLE_DISTAL, icon, humanoid_props)
    bone_prop_search(column, HumanBones.RIGHT_RING_PROXIMAL, icon, humanoid_props)
    bone_prop_search(column, HumanBones.RIGHT_RING_INTERMEDIATE, icon, humanoid_props)
    bone_prop_search(column, HumanBones.RIGHT_RING_DISTAL, icon, humanoid_props)
    bone_prop_search(column, HumanBones.RIGHT_LITTLE_PROXIMAL, icon, humanoid_props)
    bone_prop_search(column, HumanBones.RIGHT_LITTLE_INTERMEDIATE, icon, humanoid_props)
    bone_prop_search(column, HumanBones.RIGHT_LITTLE_DISTAL, icon, humanoid_props)
    icon = "MOD_DYNAMICPAINT"
    bone_prop_search(column, HumanBones.RIGHT_TOES, icon, humanoid_props)

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
    bone_prop_search(column, HumanBones.LEFT_SHOULDER, icon, humanoid_props)
    icon = "VIEW_PAN"
    bone_prop_search(column, HumanBones.LEFT_THUMB_PROXIMAL, icon, humanoid_props)
    bone_prop_search(column, HumanBones.LEFT_THUMB_INTERMEDIATE, icon, humanoid_props)
    bone_prop_search(column, HumanBones.LEFT_THUMB_DISTAL, icon, humanoid_props)
    bone_prop_search(column, HumanBones.LEFT_INDEX_PROXIMAL, icon, humanoid_props)
    bone_prop_search(column, HumanBones.LEFT_INDEX_INTERMEDIATE, icon, humanoid_props)
    bone_prop_search(column, HumanBones.LEFT_INDEX_DISTAL, icon, humanoid_props)
    bone_prop_search(column, HumanBones.LEFT_MIDDLE_PROXIMAL, icon, humanoid_props)
    bone_prop_search(column, HumanBones.LEFT_MIDDLE_INTERMEDIATE, icon, humanoid_props)
    bone_prop_search(column, HumanBones.LEFT_MIDDLE_DISTAL, icon, humanoid_props)
    bone_prop_search(column, HumanBones.LEFT_RING_PROXIMAL, icon, humanoid_props)
    bone_prop_search(column, HumanBones.LEFT_RING_INTERMEDIATE, icon, humanoid_props)
    bone_prop_search(column, HumanBones.LEFT_RING_DISTAL, icon, humanoid_props)
    bone_prop_search(column, HumanBones.LEFT_LITTLE_PROXIMAL, icon, humanoid_props)
    bone_prop_search(column, HumanBones.LEFT_LITTLE_INTERMEDIATE, icon, humanoid_props)
    bone_prop_search(column, HumanBones.LEFT_LITTLE_DISTAL, icon, humanoid_props)
    icon = "MOD_DYNAMICPAINT"
    bone_prop_search(column, HumanBones.LEFT_TOES, icon, humanoid_props)

    layout.label(text="Arm", icon="VIEW_PAN", translate=False)  # TODO: 翻訳
    layout.prop(
        humanoid_props,
        "arm_stretch",
    )
    layout.prop(humanoid_props, "upper_arm_twist")
    layout.prop(humanoid_props, "lower_arm_twist")
    layout.separator()
    layout.label(text="Leg", icon="MOD_DYNAMICPAINT")
    layout.prop(humanoid_props, "leg_stretch")
    layout.prop(humanoid_props, "upper_leg_twist")
    layout.prop(humanoid_props, "lower_leg_twist")
    layout.prop(humanoid_props, "feet_spacing")
    layout.separator()
    layout.prop(humanoid_props, "has_translation_dof")


class VRM_PT_vrm0_humanoid_armature_object_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm0_humanoid_armature_object_property"
    bl_label = "VRM 0.x Humanoid"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            context.active_object
            and context.active_object.type == "ARMATURE"
            and hasattr(context.active_object.data, "vrm_addon_extension")
        )

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="ARMATURE_DATA")

    def draw(self, context: bpy.types.Context) -> None:
        ext = context.active_object.data.vrm_addon_extension
        if isinstance(ext, VrmAddonArmatureExtensionPropertyGroup):
            draw_vrm0_humanoid_layout(
                context.active_object, self.layout, ext.vrm0.humanoid
            )


class VRM_PT_vrm0_humanoid_ui(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm0_humanoid_ui"
    bl_label = "VRM 0.x Humanoid"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.armature_exists(context)

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
            draw_vrm0_humanoid_layout(
                armature, self.layout, armature.data.vrm_addon_extension.vrm0.humanoid
            )


def draw_vrm0_first_person_layout(
    armature: bpy.types.Object,
    context: bpy.types.Context,
    layout: bpy.types.UILayout,
    first_person_props: Vrm0FirstPersonPropertyGroup,
) -> None:
    migrate(armature.name, defer=True)
    blend_data = context.blend_data
    layout.prop_search(
        first_person_props.first_person_bone, "value", armature.data, "bones"
    )
    layout.prop(first_person_props, "first_person_bone_offset", icon="BONE_DATA")
    layout.prop(first_person_props, "look_at_type_name")
    box = layout.box()
    box.label(text="Mesh Annotations", icon="FULLSCREEN_EXIT")
    for mesh_annotation_index, mesh_annotation in enumerate(
        first_person_props.mesh_annotations
    ):
        row = box.row()
        row.prop_search(mesh_annotation.mesh, "value", blend_data, "meshes")
        row.prop(mesh_annotation, "first_person_flag")
        remove_mesh_annotation_op = row.operator(
            vrm0_operator.VRM_OT_remove_vrm0_first_person_mesh_annotation.bl_idname,
            text="Remove",
            icon="REMOVE",
        )
        remove_mesh_annotation_op.armature_name = armature.name
        remove_mesh_annotation_op.mesh_annotation_index = mesh_annotation_index
    add_mesh_annotation_op = box.operator(
        vrm0_operator.VRM_OT_add_vrm0_first_person_mesh_annotation.bl_idname
    )
    add_mesh_annotation_op.armature_name = armature.name
    box = layout.box()
    box.label(text="Look At Horizontal Inner", icon="FULLSCREEN_EXIT")
    box.prop(first_person_props.look_at_horizontal_inner, "curve")
    box.prop(first_person_props.look_at_horizontal_inner, "x_range")
    box.prop(first_person_props.look_at_horizontal_inner, "y_range")
    box = layout.box()
    box.label(text="Look At Horizontal Outer", icon="FULLSCREEN_ENTER")
    box.prop(first_person_props.look_at_horizontal_outer, "curve")
    box.prop(first_person_props.look_at_horizontal_outer, "x_range")
    box.prop(first_person_props.look_at_horizontal_outer, "y_range")
    box = layout.box()
    box.label(text="Look At Vertical Up", icon="TRIA_UP")
    box.prop(first_person_props.look_at_vertical_up, "curve")
    box.prop(first_person_props.look_at_vertical_up, "x_range")
    box.prop(first_person_props.look_at_vertical_up, "y_range")
    box = layout.box()
    box.label(text="Look At Vertical Down", icon="TRIA_DOWN")
    box.prop(first_person_props.look_at_vertical_down, "curve")
    box.prop(first_person_props.look_at_vertical_down, "x_range")
    box.prop(first_person_props.look_at_vertical_down, "y_range")


class VRM_PT_vrm0_first_person_armature_object_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm0_first_person_armature_object_property"
    bl_label = "VRM 0.x First Person"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            context.active_object
            and context.active_object.type == "ARMATURE"
            and hasattr(context.active_object.data, "vrm_addon_extension")
        )

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="HIDE_OFF")

    def draw(self, context: bpy.types.Context) -> None:
        ext = context.active_object.data.vrm_addon_extension
        if isinstance(ext, VrmAddonArmatureExtensionPropertyGroup):
            draw_vrm0_first_person_layout(
                context.active_object,
                context,
                self.layout,
                ext.vrm0.first_person,
            )


class VRM_PT_vrm0_first_person_ui(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm0_first_person_ui"
    bl_label = "VRM 0.x First Person"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.armature_exists(context)

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
            draw_vrm0_first_person_layout(
                armature,
                context,
                self.layout,
                armature.data.vrm_addon_extension.vrm0.first_person,
            )


def draw_vrm0_blend_shape_master_layout(
    armature: bpy.types.Object,
    context: bpy.types.Context,
    layout: bpy.types.UILayout,
    blend_shape_master_props: Vrm0BlendShapeMasterPropertyGroup,
) -> None:
    migrate(armature.name, defer=True)
    blend_data = context.blend_data
    for blend_shape_group_index, blend_shape_group_props in enumerate(
        blend_shape_master_props.blend_shape_groups
    ):
        row = layout.row()
        row.alignment = "LEFT"
        row.prop(
            blend_shape_group_props,
            "show_expanded",
            icon="TRIA_DOWN" if blend_shape_group_props.show_expanded else "TRIA_RIGHT",
            emboss=False,
            text=blend_shape_group_props.name
            + " / "
            + blend_shape_group_props.preset_name,
            translate=False,
        )
        if not blend_shape_group_props.show_expanded:
            continue

        box = layout.box()
        box.prop(blend_shape_group_props, "name")
        box.prop(blend_shape_group_props, "preset_name")

        box.prop(blend_shape_group_props, "is_binary", icon="IPO_CONSTANT")
        box.separator()
        row = box.row()
        row.alignment = "LEFT"
        row.prop(
            blend_shape_group_props,
            "show_expanded_binds",
            icon="TRIA_DOWN"
            if blend_shape_group_props.show_expanded_binds
            else "TRIA_RIGHT",
            emboss=False,
        )
        if blend_shape_group_props.show_expanded_binds:
            for bind_index, bind_props in enumerate(blend_shape_group_props.binds):
                bind_box = box.box()
                bind_box.prop_search(
                    bind_props.mesh, "value", blend_data, "meshes", text="Mesh"
                )
                if (
                    bind_props.mesh.value
                    and bind_props.mesh.value in blend_data.meshes
                    and blend_data.meshes[bind_props.mesh.value]
                    and blend_data.meshes[bind_props.mesh.value].shape_keys
                    and blend_data.meshes[bind_props.mesh.value].shape_keys.key_blocks
                    and blend_data.meshes[
                        bind_props.mesh.value
                    ].shape_keys.key_blocks.keys()
                ):
                    bind_box.prop_search(
                        bind_props,
                        "index",
                        blend_data.meshes[bind_props.mesh.value].shape_keys,
                        "key_blocks",
                        text="Shape key",
                    )
                bind_box.prop(bind_props, "weight")
                remove_blend_shape_bind_op = bind_box.operator(
                    vrm0_operator.VRM_OT_remove_vrm0_blend_shape_bind.bl_idname,
                    icon="REMOVE",
                )
                remove_blend_shape_bind_op.armature_name = armature.name
                remove_blend_shape_bind_op.blend_shape_group_index = (
                    blend_shape_group_index
                )
                remove_blend_shape_bind_op.bind_index = bind_index
            add_blend_shape_bind_op = box.operator(
                vrm0_operator.VRM_OT_add_vrm0_blend_shape_bind.bl_idname, icon="ADD"
            )
            add_blend_shape_bind_op.armature_name = armature.name
            add_blend_shape_bind_op.blend_shape_group_index = blend_shape_group_index

        row = box.row()
        row.alignment = "LEFT"
        row.prop(
            blend_shape_group_props,
            "show_expanded_material_values",
            icon="TRIA_DOWN"
            if blend_shape_group_props.show_expanded_material_values
            else "TRIA_RIGHT",
            emboss=False,
        )
        if blend_shape_group_props.show_expanded_material_values:
            for material_value_index, material_value_props in enumerate(
                blend_shape_group_props.material_values
            ):
                material_value_box = box.box()
                material_value_box.prop_search(
                    material_value_props, "material", blend_data, "materials"
                )
                material_value_box.prop(material_value_props, "property_name")
                for (
                    target_value_index,
                    target_value_props,
                ) in enumerate(material_value_props.target_value):
                    target_value_row = material_value_box.split(align=True, factor=0.7)
                    target_value_row.prop(
                        target_value_props, "value", text=f"Value {target_value_index}"
                    )
                    remove_target_value_op = target_value_row.operator(
                        vrm0_operator.VRM_OT_remove_vrm0_material_value_bind_target_value.bl_idname,
                        text="Remove",
                        icon="REMOVE",
                    )
                    remove_target_value_op.armature_name = armature.name
                    remove_target_value_op.blend_shape_group_index = (
                        blend_shape_group_index
                    )
                    remove_target_value_op.material_value_index = material_value_index
                    remove_target_value_op.target_value_index = target_value_index
                add_target_value_op = material_value_box.operator(
                    vrm0_operator.VRM_OT_add_vrm0_material_value_bind_target_value.bl_idname,
                    icon="ADD",
                )
                add_target_value_op.armature_name = armature.name
                add_target_value_op.blend_shape_group_index = blend_shape_group_index
                add_target_value_op.material_value_index = material_value_index

                remove_material_value_op = material_value_box.operator(
                    vrm0_operator.VRM_OT_remove_vrm0_material_value_bind.bl_idname,
                    icon="REMOVE",
                )
                remove_material_value_op.armature_name = armature.name
                remove_material_value_op.blend_shape_group_index = (
                    blend_shape_group_index
                )
                remove_material_value_op.material_value_index = material_value_index
            add_material_value_op = box.operator(
                vrm0_operator.VRM_OT_add_vrm0_material_value_bind.bl_idname, icon="ADD"
            )
            add_material_value_op.armature_name = armature.name
            add_material_value_op.blend_shape_group_index = blend_shape_group_index

        remove_blend_shape_group_op = box.operator(
            vrm0_operator.VRM_OT_remove_vrm0_blend_shape_group.bl_idname, icon="REMOVE"
        )
        remove_blend_shape_group_op.armature_name = armature.name
        remove_blend_shape_group_op.blend_shape_group_index = blend_shape_group_index
    add_blend_shape_group_op = layout.operator(
        vrm0_operator.VRM_OT_add_vrm0_blend_shape_group.bl_idname, icon="ADD"
    )
    add_blend_shape_group_op.name = "New"
    add_blend_shape_group_op.armature_name = armature.name


class VRM_PT_vrm0_blend_shape_master_armature_object_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm0_blend_shape_master_armature_object_property"
    bl_label = "VRM 0.x Blend Shape Proxy"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            context.active_object
            and context.active_object.type == "ARMATURE"
            and hasattr(context.active_object.data, "vrm_addon_extension")
        )

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="SHAPEKEY_DATA")

    def draw(self, context: bpy.types.Context) -> None:
        ext = context.active_object.data.vrm_addon_extension
        if isinstance(ext, VrmAddonArmatureExtensionPropertyGroup):
            draw_vrm0_blend_shape_master_layout(
                context.active_object, context, self.layout, ext.vrm0.blend_shape_master
            )


class VRM_PT_vrm0_blend_shape_master_ui(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm0_blend_shape_master_ui"
    bl_label = "VRM 0.x Blend Shape Proxy"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.armature_exists(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="SHAPEKEY_DATA")

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
            draw_vrm0_blend_shape_master_layout(
                armature,
                context,
                self.layout,
                armature.data.vrm_addon_extension.vrm0.blend_shape_master,
            )


def draw_vrm0_secondary_animation_layout(
    armature: bpy.types.Object,
    layout: bpy.types.UILayout,
    secondary_animation: Vrm0SecondaryAnimationPropertyGroup,
) -> None:
    migrate(armature.name, defer=True)
    data = armature.data

    bone_groups_box = layout.box()
    bone_groups_box.label(text="Spring Bone Groups", icon="GROUP_BONE")
    for bone_group_index, bone_group_props in enumerate(
        secondary_animation.bone_groups
    ):
        row = bone_groups_box.row()
        row.alignment = "LEFT"

        text = ""
        if bone_group_props.bones:
            text = (
                "("
                + ", ".join(map(lambda bone: str(bone.value), bone_group_props.bones))
                + ")"
            )

        if bone_group_props.center.value:
            if text:
                text = " - " + text
            text = bone_group_props.center.value + text

        if bone_group_props.comment:
            if text:
                text = " / " + text
            text = bone_group_props.comment + text

        if not text:
            text = "(EMPTY)"

        row.prop(
            bone_group_props,
            "show_expanded",
            icon="TRIA_DOWN" if bone_group_props.show_expanded else "TRIA_RIGHT",
            emboss=False,
            text=text,
            translate=False,
        )
        if not bone_group_props.show_expanded:
            continue

        box = bone_groups_box.box()
        row = box.row()
        box.prop(bone_group_props, "comment", icon="BOOKMARKS")
        box.prop(bone_group_props, "stiffiness", icon="RIGID_BODY_CONSTRAINT")
        box.prop(bone_group_props, "drag_force", icon="FORCE_DRAG")
        box.separator()
        box.prop(bone_group_props, "gravity_power", icon="OUTLINER_OB_FORCE_FIELD")
        box.prop(bone_group_props, "gravity_dir", icon="OUTLINER_OB_FORCE_FIELD")
        box.separator()
        box.prop_search(
            bone_group_props.center,
            "value",
            data,
            "bones",
            icon="PIVOT_MEDIAN",
            text="Center Bone",
        )
        box.prop(
            bone_group_props,
            "hit_radius",
            icon="MOD_PHYSICS",
        )
        box.separator()
        row = box.row()
        row.alignment = "LEFT"
        row.prop(
            bone_group_props,
            "show_expanded_bones",
            icon="TRIA_DOWN" if bone_group_props.show_expanded_bones else "TRIA_RIGHT",
            emboss=False,
        )
        if bone_group_props.show_expanded_bones:
            for bone_index, bone in enumerate(bone_group_props.bones):
                bone_row = box.split(align=True, factor=0.7)
                bone_row.prop_search(bone, "value", data, "bones", text="")
                remove_bone_op = bone_row.operator(
                    vrm0_operator.VRM_OT_remove_vrm0_secondary_animation_group_bone.bl_idname,
                    icon="REMOVE",
                    text="Remove",
                )
                remove_bone_op.armature_name = armature.name
                remove_bone_op.bone_group_index = bone_group_index
                remove_bone_op.bone_index = bone_index
            add_bone_op = box.operator(
                vrm0_operator.VRM_OT_add_vrm0_secondary_animation_group_bone.bl_idname,
                icon="ADD",
            )
            add_bone_op.armature_name = armature.name
            add_bone_op.bone_group_index = bone_group_index

        row = box.row()
        row.alignment = "LEFT"
        row.prop(
            bone_group_props,
            "show_expanded_collider_groups",
            icon="TRIA_DOWN"
            if bone_group_props.show_expanded_collider_groups
            else "TRIA_RIGHT",
            emboss=False,
        )
        if bone_group_props.show_expanded_collider_groups:
            for collider_group_index, collider_group in enumerate(
                bone_group_props.collider_groups
            ):
                collider_group_row = box.split(align=True, factor=0.7)
                collider_group_row.prop_search(
                    collider_group,
                    "value",
                    secondary_animation,
                    "collider_groups",
                    text="",
                )
                remove_collider_group_op = collider_group_row.operator(
                    vrm0_operator.VRM_OT_remove_vrm0_secondary_animation_group_collider_group.bl_idname,
                    icon="REMOVE",
                    text="Remove",
                )
                remove_collider_group_op.armature_name = armature.name
                remove_collider_group_op.bone_group_index = bone_group_index
                remove_collider_group_op.collider_group_index = collider_group_index
            add_collider_group_op = box.operator(
                vrm0_operator.VRM_OT_add_vrm0_secondary_animation_group_collider_group.bl_idname,
                icon="ADD",
            )
            add_collider_group_op.armature_name = armature.name
            add_collider_group_op.bone_group_index = bone_group_index

        remove_bone_group_op = box.operator(
            vrm0_operator.VRM_OT_remove_vrm0_secondary_animation_group.bl_idname,
            icon="REMOVE",
        )
        remove_bone_group_op.armature_name = armature.name
        remove_bone_group_op.bone_group_index = bone_group_index
    add_bone_group_op = bone_groups_box.operator(
        vrm0_operator.VRM_OT_add_vrm0_secondary_animation_group.bl_idname, icon="ADD"
    )
    add_bone_group_op.armature_name = armature.name

    collider_groups_box = layout.box()
    collider_groups_box.label(text="Collider Groups", icon="SPHERE")
    for collider_group_index, collider_group_props in enumerate(
        secondary_animation.collider_groups
    ):
        row = collider_groups_box.row()
        row.alignment = "LEFT"
        row.prop(
            collider_group_props,
            "show_expanded",
            icon="TRIA_DOWN" if collider_group_props.show_expanded else "TRIA_RIGHT",
            emboss=False,
            text=collider_group_props.name,
            translate=False,
        )
        if not collider_group_props.show_expanded:
            continue

        box = collider_groups_box.box()
        row = box.row()
        box.label(text=collider_group_props.name)
        box.prop_search(collider_group_props.node, "value", armature.data, "bones")

        for collider_index, collider_props in enumerate(collider_group_props.colliders):
            collider_row = box.split(align=True, factor=0.5)
            collider_row.prop(
                collider_props.blender_object, "name", icon="MESH_UVSPHERE", text=""
            )
            collider_row.prop(
                collider_props.blender_object, "empty_display_size", text=""
            )
            remove_collider_op = collider_row.operator(
                vrm0_operator.VRM_OT_remove_vrm0_secondary_animation_collider_group_collider.bl_idname,
                icon="REMOVE",
                text="Remove",
            )
            remove_collider_op.armature_name = armature.name
            remove_collider_op.collider_group_index = collider_group_index
            remove_collider_op.collider_index = collider_index
        add_collider_op = box.operator(
            vrm0_operator.VRM_OT_add_vrm0_secondary_animation_collider_group_collider.bl_idname,
            icon="ADD",
        )
        add_collider_op.armature_name = armature.name
        add_collider_op.collider_group_index = collider_group_index
        add_collider_op.bone_name = collider_group_props.node.value

        remove_collider_group_op = box.operator(
            vrm0_operator.VRM_OT_remove_vrm0_secondary_animation_collider_group.bl_idname,
            icon="REMOVE",
        )
        remove_collider_group_op.armature_name = armature.name
        remove_collider_group_op.collider_group_index = collider_group_index
    add_collider_group_op = collider_groups_box.operator(
        vrm0_operator.VRM_OT_add_vrm0_secondary_animation_collider_group.bl_idname,
        icon="ADD",
    )
    add_collider_group_op.armature_name = armature.name


class VRM_PT_vrm0_secondary_animation_armature_object_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm0_secondary_animation_armature_object_property"
    bl_label = "VRM 0.x Spring Bone"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            context.active_object
            and context.active_object.type == "ARMATURE"
            and hasattr(context.active_object.data, "vrm_addon_extension")
        )

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="PHYSICS")

    def draw(self, context: bpy.types.Context) -> None:
        ext = context.active_object.data.vrm_addon_extension
        if isinstance(ext, VrmAddonArmatureExtensionPropertyGroup):
            draw_vrm0_secondary_animation_layout(
                context.active_object, self.layout, ext.vrm0.secondary_animation
            )


class VRM_PT_vrm0_secondary_animation_ui(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm0_secondary_animation_ui"
    bl_label = "VRM 0.x Spring Bone"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.armature_exists(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="PHYSICS")

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
            draw_vrm0_secondary_animation_layout(
                armature,
                self.layout,
                armature.data.vrm_addon_extension.vrm0.secondary_animation,
            )


def draw_vrm0_meta_layout(
    armature: bpy.types.Object,
    context: bpy.types.Context,
    layout: bpy.types.UILayout,
    meta_props: Vrm0MetaPropertyGroup,
) -> None:
    migrate(armature.name, defer=True)
    blend_data = context.blend_data

    layout.prop_search(meta_props, "texture", blend_data, "images", text="Thumbnail")

    layout.prop(meta_props, "title", icon="FILE_BLEND")
    layout.prop(meta_props, "version", icon="LINENUMBERS_ON")
    layout.prop(meta_props, "author", icon="USER")
    layout.prop(meta_props, "contact_information", icon="URL")
    layout.prop(meta_props, "reference", icon="URL")
    layout.prop(meta_props, "allowed_user_name", icon="MATCLOTH")
    layout.prop(
        meta_props,
        "violent_ussage_name",
        icon="ORPHAN_DATA",
    )
    layout.prop(meta_props, "sexual_ussage_name", icon="HEART")
    layout.prop(
        meta_props,
        "commercial_ussage_name",
        icon="SOLO_OFF",
    )
    layout.prop(meta_props, "other_permission_url", icon="URL")
    layout.prop(meta_props, "license_name", icon="COMMUNITY")
    if meta_props.license_name == Vrm0MetaPropertyGroup.LICENSE_NAME_OTHER:
        layout.prop(meta_props, "other_license_url", icon="URL")


class VRM_PT_vrm0_meta_armature_object_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm0_meta_armature_object_property"
    bl_label = "VRM 0.x Meta"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = VRM_PT_vrm_armature_object_property.bl_idname

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            context.active_object
            and context.active_object.type == "ARMATURE"
            and hasattr(context.active_object.data, "vrm_addon_extension")
        )

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="FILE_BLEND")

    def draw(self, context: bpy.types.Context) -> None:
        ext = context.active_object.data.vrm_addon_extension
        if isinstance(ext, VrmAddonArmatureExtensionPropertyGroup):
            draw_vrm0_meta_layout(
                context.active_object, context, self.layout, ext.vrm0.meta
            )


class VRM_PT_vrm0_meta_ui(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm0_meta_ui"
    bl_label = "VRM 0.x Meta"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return search.armature_exists(context)

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="FILE_BLEND")

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
            draw_vrm0_meta_layout(
                armature,
                context,
                self.layout,
                armature.data.vrm_addon_extension.vrm0.meta,
            )
