import bpy

from .. import lang, vrm_types
from ..preferences import get_preferences
from . import (
    detail_mesh_maker,
    glsl_drawer,
    make_armature,
    mesh_from_bone_envelopes,
    validation,
    vrm_helper,
)
from .glsl_drawer import GlslDrawObj


def add_armature(
    add_armature_op: bpy.types.Operator, context: bpy.types.Context
) -> None:
    add_armature_op.layout.operator(
        make_armature.ICYP_OT_MAKE_ARMATURE.bl_idname,
        text="VRM Humanoid",
        icon="OUTLINER_OB_ARMATURE",
    )


def make_mesh(make_mesh_op: bpy.types.Operator, context: bpy.types.Context) -> None:
    make_mesh_op.layout.separator()
    make_mesh_op.layout.operator(
        mesh_from_bone_envelopes.ICYP_OT_MAKE_MESH_FROM_BONE_ENVELOPES.bl_idname,
        text="Mesh from selected armature",
        icon="PLUGIN",
    )
    make_mesh_op.layout.operator(
        detail_mesh_maker.ICYP_OT_DETAIL_MESH_MAKER.bl_idname,
        text="(WIP)Face mesh from selected armature and bound mesh",
        icon="PLUGIN",
    )


class VRM_IMPORTER_PT_controller(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "ICYP_PT_ui_controller"
    bl_label = "VRM Helper"
    # どこに置くかの定義
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.active_object)

    def draw(self, context: bpy.types.Context) -> None:
        active_object = context.active_object
        mode = context.mode
        layout = self.layout
        object_type = active_object.type

        # region draw_main
        if mode == "OBJECT":
            # object_mode_box = layout.box()
            vrm_validator_prop = layout.operator(
                validation.WM_OT_vrmValidator.bl_idname,
                text=lang.support("Validate VRM model", "VRMモデルのチェック"),
                icon="VIEWZOOM",
            )
            preferences = get_preferences(context)
            if preferences:
                layout.prop(
                    preferences,
                    "export_invisibles",
                    text=lang.support("Export invisible objects", "非表示オブジェクトを含める"),
                )
                layout.prop(
                    preferences,
                    "export_only_selections",
                    text=lang.support("Export only selections", "選択されたオブジェクトのみ"),
                )

            vrm_validator_prop.show_successful_message = True
            # vrm_validator_prop.errors = []  # これはできない
            layout.separator()
            layout.label(text="MToon preview")

            if GlslDrawObj.draw_objs:
                layout.operator(
                    glsl_drawer.ICYP_OT_Remove_Draw_Model.bl_idname,
                    icon="SHADING_RENDERED",
                    depress=True,
                )
            else:
                if [obj for obj in bpy.data.objects if obj.type == "LIGHT"]:
                    layout.operator(
                        glsl_drawer.ICYP_OT_Draw_Model.bl_idname,
                        icon="SHADING_RENDERED",
                        depress=False,
                    )
                else:
                    layout.box().label(
                        icon="INFO",
                        text=lang.support("A light is required", "ライトが必要です"),
                    )
            if object_type == "MESH":
                layout.separator()
                layout.operator(
                    vrm_helper.Vroid2VRC_lipsync_from_json_recipe.bl_idname,
                    icon="EXPERIMENTAL",
                )
        if mode == "EDIT_MESH":
            layout.operator(bpy.ops.mesh.symmetry_snap.idname_py(), icon="MOD_MIRROR")
        # endregion draw_main


class VRM_IMPORTER_PT_armature_controller(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_IMPORTER_PT_armature_controller"
    bl_label = "VRM Armature Helper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VRM"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.active_object) and context.active_object.type == "ARMATURE"

    def draw(self, context: bpy.types.Context) -> None:
        active_object = context.active_object
        layout = self.layout
        data = active_object.data

        def show_ui(parent: bpy.types.UILayout, bone: str, icon: str) -> None:
            parent.prop_search(data, f'["{bone}"]', data, "bones", text=bone, icon=icon)

        def show_add_require(parent: bpy.types.UILayout, bone: str) -> None:
            parent.operator(
                vrm_helper.Add_VRM_require_humanbone_custom_property.bl_idname,
                text=f"Add {bone} property",
                icon="ADD",
            )

        def show_add_defined(parent: bpy.types.UILayout, bone: str) -> None:
            parent.operator(
                vrm_helper.Add_VRM_defined_humanbone_custom_property.bl_idname,
                text=f"Add {bone} property",
                icon="ADD",
            )

        armature_box = layout
        armature_box.operator(
            vrm_helper.Add_VRM_extensions_to_armature.bl_idname, icon="MOD_BUILD"
        )

        layout.separator()
        requires_box = armature_box.box()
        requires_box.label(text="VRM Required Bones", icon="ARMATURE_DATA")
        for req in vrm_types.HumanBones.center_req[::-1]:
            icon = "USER"
            if req in data:
                show_ui(requires_box, req, icon)
            else:
                show_add_require(requires_box, req)
        row = requires_box.row()
        column = row.column()
        for req in vrm_types.HumanBones.right_arm_req:
            icon = "VIEW_PAN"
            if req in data:
                show_ui(column, req, icon)
            else:
                show_add_require(column, req)
        column = row.column()
        for req in vrm_types.HumanBones.left_arm_req:
            icon = "VIEW_PAN"
            if req in data:
                show_ui(column, req, icon)
            else:
                show_add_require(column, req)
        row = requires_box.row()
        column = row.column()
        for req in vrm_types.HumanBones.right_leg_req:
            icon = "MOD_DYNAMICPAINT"
            if req in data:
                show_ui(column, req, icon)
            else:
                show_add_require(column, req)
        column = row.column()
        for req in vrm_types.HumanBones.left_leg_req:
            icon = "MOD_DYNAMICPAINT"
            if req in data:
                show_ui(column, req, icon)
            else:
                show_add_require(column, req)
        defines_box = armature_box.box()
        defines_box.label(text="VRM Optional Bones", icon="BONE_DATA")
        row = defines_box.row()
        for defs in ["rightEye"]:
            icon = "HIDE_OFF"
            if defs in data:
                show_ui(row, defs, icon)
            else:
                show_add_defined(row, defs)
        for defs in ["leftEye"]:
            icon = "HIDE_OFF"
            if defs in data:
                show_ui(row, defs, icon)
            else:
                show_add_defined(row, defs)
        for defs in vrm_types.HumanBones.center_def[::-1]:
            icon = "USER"
            if defs in data:
                show_ui(defines_box, defs, icon)
            else:
                show_add_defined(defines_box, defs)
        defines_box.separator()
        for defs in vrm_types.HumanBones.right_arm_def:
            icon = "VIEW_PAN"
            if defs in data:
                show_ui(defines_box, defs, icon)
            else:
                show_add_defined(defines_box, defs)
        for defs in vrm_types.HumanBones.right_leg_def:
            icon = "MOD_DYNAMICPAINT"
            if defs in data:
                show_ui(defines_box, defs, icon)
            else:
                show_add_defined(defines_box, defs)
        defines_box.separator()
        for defs in vrm_types.HumanBones.left_arm_def:
            icon = "VIEW_PAN"
            if defs in data:
                show_ui(defines_box, defs, icon)
            else:
                show_add_defined(defines_box, defs)
        for defs in vrm_types.HumanBones.left_leg_def:
            icon = "MOD_DYNAMICPAINT"
            if defs in data:
                show_ui(defines_box, defs, icon)
            else:
                show_add_defined(defines_box, defs)
        armature_box.separator()
        armature_box.operator(vrm_helper.Bones_rename.bl_idname, icon="EXPERIMENTAL")


class VRM_IMPORTER_PT_vrm_humanoid_params(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_IMPORTER_PT_vrm_humanoid_params"
    bl_label = "VRM Humanoid Params"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        exist = context.object is not None
        armature = context.object.type == "ARMATURE"
        return exist and armature

    def draw_header(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(icon="ARMATURE_DATA")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        testing = layout.box()
        testing.label(text="Testing", icon="EXPERIMENTAL")
        active_object = context.active_object
        layout.label(text="Arm", icon="VIEW_PAN")
        layout.prop(
            active_object.vrm_props.humanoid_params,
            "arm_stretch",
        )
        layout.prop(active_object.vrm_props.humanoid_params, "upper_arm_twist")
        layout.prop(active_object.vrm_props.humanoid_params, "lower_arm_twist")
        layout.separator()
        layout.label(text="Leg", icon="MOD_DYNAMICPAINT")
        layout.prop(active_object.vrm_props.humanoid_params, "leg_stretch")
        layout.prop(active_object.vrm_props.humanoid_params, "upper_leg_twist")
        layout.prop(active_object.vrm_props.humanoid_params, "lower_leg_twist")
        layout.prop(active_object.vrm_props.humanoid_params, "feet_spacing")
        layout.separator()
        layout.prop(active_object.vrm_props.humanoid_params, "has_translation_dof")


class VRM_IMPORTER_PT_vrm_firstPerson_params(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_IMPORTER_PT_vrm_firstPerson_params"
    bl_label = "VRM FirstPerson Params"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        exist = context.object is not None
        armature = context.object.type == "ARMATURE"
        return exist and armature

    def draw_header(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(icon="HIDE_OFF")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        testing = layout.box()
        testing.label(text="Testing", icon="EXPERIMENTAL")
        active_object = context.active_object
        data = active_object.data
        blend_data = context.blend_data
        props = active_object.vrm_props.first_person_params
        layout.prop_search(props, "first_person_bone", data, "bones")
        layout.prop(props, "first_person_bone_offset", icon="BONE_DATA")
        layout.prop(props, "look_at_type_name")
        for item in props.mesh_annotations:
            box = layout.row()
            box.prop_search(item, "mesh", blend_data, "meshes")
            box.prop(item, "first_person_flag")
        box = layout.box()
        box.label(text="Look At Horizontal Inner", icon="FULLSCREEN_EXIT")
        box.prop(props.look_at_horizontal_inner, "curve")
        box.prop(props.look_at_horizontal_inner, "x_range")
        box.prop(props.look_at_horizontal_inner, "y_range")
        box = layout.box()
        box.label(text="Look At Horizontal Outer", icon="FULLSCREEN_ENTER")
        box.prop(props.look_at_horizontal_outer, "curve")
        box.prop(props.look_at_horizontal_outer, "x_range")
        box.prop(props.look_at_horizontal_outer, "y_range")
        box = layout.box()
        box.label(text="Look At Vertical Up", icon="ANCHOR_TOP")
        box.prop(props.look_at_vertical_up, "curve")
        box.prop(props.look_at_vertical_up, "x_range")
        box.prop(props.look_at_vertical_up, "y_range")
        box = layout.box()
        box.label(text="Look At Vertical Down", icon="ANCHOR_BOTTOM")
        box.prop(props.look_at_vertical_down, "curve")
        box.prop(props.look_at_vertical_down, "x_range")
        box.prop(props.look_at_vertical_down, "y_range")


class VRM_IMPORTER_PT_vrm_blendshape_group(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_IMPORTER_PT_vrm_blendshape_group"
    bl_label = "VRM Blendshape Group"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        exist = context.object is not None
        armature = context.object.type == "ARMATURE"
        return exist and armature

    def draw_header(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(icon="SHAPEKEY_DATA")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        testing = layout.box()
        testing.label(text="Testing", icon="EXPERIMENTAL")
        active_object = context.active_object
        blend_data = context.blend_data
        for blendshape in active_object.vrm_props.blendshape_group:
            box = layout.box()
            box.prop(blendshape, "name")
            box.prop(blendshape, "preset_name")

            box.prop(blendshape, "is_binary", icon="IPO_CONSTANT")
            box.separator()
            row = box.row()
            row.prop(
                blendshape,
                "show_expanded_binds",
                icon="TRIA_DOWN" if blendshape.show_expanded_binds else "TRIA_RIGHT",
                icon_only=True,
                emboss=False,
            )
            row.label(text="Binds")
            if blendshape.show_expanded_binds:
                for bind in blendshape.binds:
                    box.prop_search(bind, "mesh", blend_data, "meshes")
                    box.prop(bind, "index")
                    box.prop(bind, "weight")
                    box.separator()
            box.label(text="materialValues is yet")


class VRM_IMPORTER_PT_vrm_spring_bone(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_IMPORTER_PT_vrm_spring_bone"
    bl_label = "VRM Spring Bones"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        exist = context.object is not None
        armature = context.object.type == "ARMATURE"
        return exist and armature

    def draw_header(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(icon="RIGID_BODY_CONSTRAINT")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        testing = layout.box()
        testing.label(text="Testing", icon="EXPERIMENTAL")
        active_object = context.active_object
        data = context.active_object.data
        spring_bones = active_object.vrm_props.spring_bones

        for spring_bone in spring_bones:
            box = layout.box()
            row = box.row()
            row.label(icon="REMOVE")
            # row.alignment = 'RIGHT'
            box.prop(spring_bone, "comment", icon="BOOKMARKS")
            box.prop(spring_bone, "stiffiness", icon="RIGID_BODY_CONSTRAINT")
            box.prop(spring_bone, "drag_force", icon="FORCE_DRAG")
            box.separator()
            box.prop(spring_bone, "gravity_power", icon="OUTLINER_OB_FORCE_FIELD")
            box.prop(spring_bone, "gravity_dir", icon="OUTLINER_OB_FORCE_FIELD")
            box.separator()
            box.prop_search(spring_bone, "center", data, "bones", icon="PIVOT_MEDIAN")
            box.prop(
                spring_bone,
                "hit_radius",
                icon="MOD_PHYSICS",
            )
            box.separator()
            row = box.row()
            row.prop(
                spring_bone,
                "show_expanded_bones",
                icon="TRIA_DOWN" if spring_bone.show_expanded_bones else "TRIA_RIGHT",
                icon_only=True,
                emboss=False,
            )
            row.label(text="Bones")
            if spring_bone.show_expanded_bones:
                for bone in spring_bone.bones:
                    box.prop_search(bone, "name", data, "bones")
            row = box.row()
            row.prop(
                spring_bone,
                "show_expanded_collider_groups",
                icon="TRIA_DOWN"
                if spring_bone.show_expanded_collider_groups
                else "TRIA_RIGHT",
                icon_only=True,
                emboss=False,
            )
            row.label(text="Collider Group")
            if spring_bone.show_expanded_collider_groups:
                for collider_group in spring_bone.collider_groups:
                    box.prop_search(collider_group, "name", data, "bones")


class VRM_IMPORTER_PT_vrm_metas(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_IMPORTER_PT_vrm_metas"
    bl_label = "VRM Metas"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        exist = context.object is not None
        armature = context.object.type == "ARMATURE"
        return exist and armature

    def draw_header(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(icon="FILE_BLEND")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        testing = layout.box()
        testing.label(text="Testing", icon="EXPERIMENTAL")
        active_object = context.active_object
        layout.prop(active_object.vrm_props.metas, "author", icon="USER")
        layout.prop(active_object.vrm_props.metas, "contact_information", icon="URL")
        layout.separator()
        layout.prop(active_object.vrm_props.metas, "title", icon="FILE_BLEND")
        layout.prop(active_object.vrm_props.metas, "version", icon="LINENUMBERS_ON")
        layout.prop(active_object.vrm_props.metas, "reference", icon="URL")
        layout.separator()
        box = layout.box()
        box.prop(
            active_object.vrm_props.required_metas, "allowed_user_name", icon="MATCLOTH"
        )
        box.prop(
            active_object.vrm_props.required_metas,
            "violent_ussage_name",
            icon="ORPHAN_DATA",
        )
        box.prop(
            active_object.vrm_props.required_metas, "sexual_ussage_name", icon="FUND"
        )
        box.prop(
            active_object.vrm_props.required_metas,
            "commercial_ussage_name",
            icon="SOLO_OFF",
        )
        box.prop(
            active_object.vrm_props.required_metas, "license_name", icon="COMMUNITY"
        )
        if (
            active_object.vrm_props.required_metas.license_name
            == REQUIRED_METAS.LICENSE_NAME_OTHER
        ):
            layout.prop(active_object.vrm_props.metas, "other_license_url", icon="URL")
        layout.prop(active_object.vrm_props.metas, "other_permission_url", icon="URL")


class HUMANOID_PARAMS(bpy.types.PropertyGroup):  # type: ignore[misc] # noqa: N801
    arm_stretch: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Arm Stretch"  # noqa: F722
    )
    leg_stretch: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Leg Stretch"  # noqa: F722
    )
    upper_arm_twist: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Upper Arm Twist"  # noqa: F722
    )
    lower_arm_twist: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Lower Arm Twist"  # noqa: F722
    )
    upper_leg_twist: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Upper Leg Twist"  # noqa: F722
    )
    lower_leg_twist: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Lower Leg Twist"  # noqa: F722
    )
    feet_spacing: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="Feet Spacing"  # noqa: F722
    )
    has_translation_dof: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Has Translation DoF"  # noqa: F722
    )


class LOOKAT_CURVE(bpy.types.PropertyGroup):  # type: ignore[misc] # noqa: N801
    curve: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=8, name="Curve"  # noqa: F821
    )
    x_range: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="X Range"  # noqa: F722
    )
    y_range: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="Y Range"  # noqa: F722
    )


class MESH_ANNOTATION(bpy.types.PropertyGroup):  # type: ignore[misc] # noqa: N801
    mesh: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Mesh"  # noqa: F821
    )
    first_person_flag_items = [
        ("Auto", "Auto", "", 0),
        ("FirstPersonOnly", "FirstPersonOnly", "", 1),
        ("ThirdPersonOnly", "ThirdPersonOnly", "", 2),
        ("Both", "Both", "", 3),
    ]
    first_person_flag: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=first_person_flag_items, name="First Person Flag"  # noqa: F722
    )


class FIRSTPERSON_PARAMS(bpy.types.PropertyGroup):  # type: ignore[misc] # noqa: N801
    first_person_bone: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="First Person Bone"  # noqa: F722
    )
    first_person_bone_offset: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3,
        name="first Person Bone Offset",  # noqa: F722
        subtype="TRANSLATION",  # noqa: F821
        unit="LENGTH",  # noqa: F821
    )
    mesh_annotations: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Mesh Annotations", type=MESH_ANNOTATION  # noqa: F722
    )
    look_at_type_name_items = [
        ("Bone", "Bone", "Bone", "BONE_DATA", 0),
        ("BlendShape", "BlendShape", "BlendShape", "SHAPEKEY_DATA", 1),
    ]
    look_at_type_name: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=look_at_type_name_items, name="Look At Type Name"  # noqa: F722
    )
    look_at_horizontal_inner: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=LOOKAT_CURVE, name="Look At Horizontal Inner"  # noqa: F722
    )
    look_at_horizontal_outer: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=LOOKAT_CURVE, name="Look At Horizontal Outer"  # noqa: F722
    )
    look_at_vertical_down: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=LOOKAT_CURVE, name="Look At Vertical Down"  # noqa: F722
    )
    look_at_vertical_up: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=LOOKAT_CURVE, name="lookAt Vertical Up"  # noqa: F722
    )


class BLENDSHAPE_BIND(bpy.types.PropertyGroup):  # type: ignore[misc] # noqa: N801
    mesh: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Mesh"  # noqa: F821
    )
    index: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Index"  # noqa: F821
    )
    weight: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Weight"  # noqa: F821
    )


class BLENDSHAPE_MATERIAL_BIND(bpy.types.PropertyGroup):  # type: ignore[misc] # noqa: N801
    material_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Material Name"  # noqa: F722
    )
    property_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Property Name"  # noqa: F722
    )
    target_value = None  # Dummy


class BLENDSHAPE_GROUP(bpy.types.PropertyGroup):  # type: ignore[misc] # noqa: N801
    name: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Name"  # noqa: F821
    )
    preset_name_items = [
        ("unknown", "unknown", "", "NONE", 0),
        ("neutral", "neutral", "", "NONE", 1),
        ("a", "a", "", "EVENT_A", 2),
        ("i", "i", "", "EVENT_I", 3),
        ("u", "u", "", "EVENT_U", 4),
        ("e", "e", "", "EVENT_E", 5),
        ("o", "o", "", "EVENT_O", 6),
        ("blink", "blink", "", "HIDE_ON", 7),
        ("joy", "joy", "", "HEART", 8),
        ("angry", "angry", "", "ORPHAN_DATA", 9),
        ("sorrow", "sorrow", "", "MOD_FLUIDSIM", 10),
        ("fun", "fun", "", "LIGHT_SUN", 11),
        ("lookup", "lookup", "", "ANCHOR_TOP", 12),
        ("lookdown", "lookdown", "", "ANCHOR_BOTTOM", 13),
        ("lookleft", "lookleft", "", "ANCHOR_RIGHT", 14),
        ("lookright", "lookright", "", "ANCHOR_LEFT", 15),
        ("blink_l", "blink_l", "", "HIDE_ON", 16),
        ("blink_r", "blink_r", "", "HIDE_ON", 17),
    ]
    preset_name: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=preset_name_items, name="Preset"  # noqa: F821
    )
    binds: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=BLENDSHAPE_BIND, name="Binds"  # noqa: F821
    )
    material_values = bpy.props.CollectionProperty(
        type=BLENDSHAPE_MATERIAL_BIND, name="Material Values"
    )
    is_binary: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Is Binary"  # noqa: F722
    )
    show_expanded_binds: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Show Expanded Binds"  # noqa: F722
    )


class COLLIDER_GROUP(bpy.types.PropertyGroup):  # type: ignore[misc] # noqa: N801
    name: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Name"  # noqa: F821
    )


class BONE_GROUP(bpy.types.PropertyGroup):  # type: ignore[misc] # noqa: N801
    name: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Name"  # noqa: F821
    )


class SPRING_BONE_GROUP(bpy.types.PropertyGroup):  # type: ignore[misc] # noqa: N801
    comment: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Comment"  # noqa: F821
    )
    stiffiness: bpy.props.IntProperty(  # type: ignore[valid-type] # noqa: SC200
        name="Stiffiness"  # noqa: F821
    )
    gravity_power: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="Gravity Power"  # noqa: F722
    )
    gravity_dir: bpy.props.FloatVectorProperty(  # type: ignore[valid-type]
        size=3, name="Gravity Dir"  # noqa: F722
    )
    drag_force: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="DragForce"  # noqa: F821
    )
    center: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Center"  # noqa: F821
    )
    hit_radius: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Hit Radius"  # noqa: F722
    )
    bones: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Bones", type=BONE_GROUP  # noqa: F821
    )
    collider_groups: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Collider Groups", type=COLLIDER_GROUP  # noqa: F722
    )
    show_expanded_bones: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Show Expanded Bones"  # noqa: F722
    )
    show_expanded_collider_groups: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Show Expanded Collider Groups"  # noqa: F722
    )


class METAS(bpy.types.PropertyGroup):  # type: ignore[misc] # noqa: N801
    def get_version(self) -> str:
        key = "version"
        return str(self.id_data[key] if key in self.id_data else "")

    def set_version(self, value: str) -> None:
        key = "version"
        if key in self.id_data:
            self.id_data[key] = value

    def get_author(self) -> str:
        key = "author"
        return str(self.id_data[key] if key in self.id_data else "")

    def set_author(self, value: str) -> None:
        key = "author"
        if key in self.id_data:
            self.id_data[key] = value

    def get_contact_information(self) -> str:
        key = "contactInformation"
        return str(self.id_data[key] if key in self.id_data else "")

    def set_contact_information(self, value: str) -> None:
        key = "contactInformation"
        if key in self.id_data:
            self.id_data[key] = value

    def get_reference(self) -> str:
        key = "reference"
        return str(self.id_data[key] if key in self.id_data else "")

    def set_reference(self, value: str) -> None:
        key = "reference"
        if key in self.id_data:
            self.id_data[key] = value

    def get_title(self) -> str:
        key = "title"
        return str(self.id_data[key] if key in self.id_data else "")

    def set_title(self, value: str) -> None:
        key = "title"
        if key in self.id_data:
            self.id_data[key] = value

    def get_other_permission_url(self) -> str:
        key = "otherPermissionUrl"
        return str(self.id_data[key] if key in self.id_data else "")

    def set_other_permission_url(self, value: str) -> None:
        key = "otherPermissionUrl"
        if key in self.id_data:
            self.id_data[key] = value

    def get_other_license_url(self) -> str:
        key = "otherLicenseUrl"
        return str(self.id_data[key] if key in self.id_data else "")

    def set_other_license_url(self, value: str) -> None:
        key = "otherLicenseUrl"
        if key in self.id_data:
            self.id_data[key] = value

    version: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Version", get=get_version, set=set_version  # noqa: F821
    )
    author: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Author", get=get_author, set=set_author  # noqa: F821
    )
    contact_information: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="ContactInformation",  # noqa: F821
        get=get_contact_information,
        set=set_contact_information,
    )
    reference: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Reference", get=get_reference, set=set_reference  # noqa: F821
    )
    title: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Title", get=get_title, set=set_title  # noqa: F821
    )
    other_permission_url: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Other Permission Url",  # noqa: F722
        get=get_other_permission_url,
        set=set_other_permission_url,
    )
    other_license_url: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Other License Url",  # noqa: F722
        get=get_other_license_url,
        set=set_other_license_url,
    )


class REQUIRED_METAS(bpy.types.PropertyGroup):  # type: ignore[misc] # noqa: N801
    INDEX_ID = 0
    INDEX_NUMBER = 3
    LICENSE_NAME_OTHER = "Other"
    allowed_user_name_items = [
        ("OnlyAuthor", "OnlyAuthor", "", 0),
        ("ExplicitlyLicensedPerson", "ExplicitlyLicensedPerson", "", 1),
        ("Everyone", "Everyone", "", 2),
    ]
    violent_ussage_name_items = [  # noqa: SC200
        ("Disallow", "Disallow", "", 0),
        ("Allow", "Allow", "", 1),
    ]
    sexual_ussage_name_items = [  # noqa: SC200
        ("Disallow", "Disallow", "", 0),
        ("Allow", "Allow", "", 1),
    ]
    commercial_ussage_name_items = [  # noqa: SC200
        ("Disallow", "Disallow", "", 0),
        ("Allow", "Allow", "", 1),
    ]
    license_name_items = [
        ("Redistribution_Prohibited", "Redistribution_Prohibited", "", 0),
        ("CC0", "CC0", "", 1),
        ("CC_BY", "CC_BY", "", 2),
        ("CC_BY_NC", "CC_BY_NC", "", 3),
        ("CC_BY_SA", "CC_BY_SA", "", 4),
        ("CC_BY_NC_SA", "CC_BY_NC_SA", "", 5),
        ("CC_BY_ND", "CC_BY_ND", "", 6),
        ("CC_BY_NC_ND", "CC_BY_NC_ND", "", 7),
        (LICENSE_NAME_OTHER, LICENSE_NAME_OTHER, "", 8),
    ]

    def get_allowed_user_name(self) -> int:
        key = "allowedUserName"
        if key in self.id_data:
            v = self.id_data[key]
            for item in self.allowed_user_name_items:
                if item[self.INDEX_ID] == v:
                    return int(item[self.INDEX_NUMBER])
        return 0

    def set_allowed_user_name(self, value: int) -> None:
        key = "allowedUserName"
        if key in self.id_data:
            self.id_data[key] = self.allowed_user_name_items[value][self.INDEX_ID]

    def get_violent_ussage_name(self) -> int:  # noqa: SC200
        key = "violentUssageName"
        if key in self.id_data:
            v = self.id_data[key]
            for item in self.violent_ussage_name_items:  # noqa: SC200
                if item[self.INDEX_ID] == v:
                    return int(item[self.INDEX_NUMBER])
        return 0

    def set_violent_ussage_name(self, value: int) -> None:  # noqa: SC200
        key = "violentUssageName"
        if key in self.id_data:
            self.id_data[key] = self.violent_ussage_name_items[value][  # noqa: SC200
                self.INDEX_ID
            ]

    def get_sexual_ussage_name(self) -> int:  # noqa: SC200
        key = "sexualUssageName"
        if key in self.id_data:
            v = self.id_data[key]
            for item in self.sexual_ussage_name_items:  # noqa: SC200
                if item[self.INDEX_ID] == v:
                    return int(item[self.INDEX_NUMBER])
        return 0

    def set_sexual_ussage_name(self, value: int) -> None:  # noqa: SC200
        key = "sexualUssageName"
        if key in self.id_data:
            self.id_data[key] = self.sexual_ussage_name_items[value][  # noqa: SC200
                self.INDEX_ID
            ]

    def get_commercial_ussage_name(self) -> int:  # noqa: SC200
        key = "commercialUssageName"
        if key in self.id_data:
            v = self.id_data[key]
            for item in self.commercial_ussage_name_items:  # noqa: SC200
                if item[self.INDEX_ID] == v:
                    return int(item[self.INDEX_NUMBER])
        return 0

    def set_commercial_ussage_name(self, value: int) -> None:  # noqa: SC200
        key = "commercialUssageName"
        if key in self.id_data:
            self.id_data[key] = self.commercial_ussage_name_items[value][  # noqa: SC200
                self.INDEX_ID
            ]

    def get_license_name(self) -> int:
        key = "licenseName"
        if key in self.id_data:
            v = self.id_data[key]
            for item in self.license_name_items:
                if item[self.INDEX_ID] == v:
                    return int(item[self.INDEX_NUMBER])
        return 0

    def set_license_name(self, value: int) -> None:
        key = "licenseName"
        if key in self.id_data:
            self.id_data[key] = self.license_name_items[value][self.INDEX_ID]

    allowed_user_name: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=allowed_user_name_items,
        get=get_allowed_user_name,
        set=set_allowed_user_name,
        name="Allowed User",  # noqa: F722
    )
    violent_ussage_name: bpy.props.EnumProperty(  # type: ignore[valid-type] # noqa: SC200
        items=violent_ussage_name_items,  # noqa: SC200
        get=get_violent_ussage_name,  # noqa: SC200
        set=set_violent_ussage_name,  # noqa: SC200
        name="Violent Ussage",  # noqa: F722
    )
    sexual_ussage_name: bpy.props.EnumProperty(  # type: ignore[valid-type] # noqa: SC200
        items=sexual_ussage_name_items,  # noqa: SC200
        get=get_sexual_ussage_name,  # noqa: SC200
        set=set_sexual_ussage_name,  # noqa: SC200
        name="Sexual Ussage",  # noqa: F722
    )
    commercial_ussage_name: bpy.props.EnumProperty(  # type: ignore[valid-type] # noqa: SC200
        items=commercial_ussage_name_items,  # noqa: SC200
        get=get_commercial_ussage_name,  # noqa: SC200
        set=set_commercial_ussage_name,  # noqa: SC200
        name="Commercial Ussage",  # noqa: F722
    )
    license_name: bpy.props.EnumProperty(  # type: ignore[valid-type]
        items=license_name_items,
        get=get_license_name,
        set=set_license_name,
        name="License",  # noqa: F821
    )


class VRMProps(bpy.types.PropertyGroup):  # type: ignore[misc] # noqa: N801
    humanoid_params: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Humanoid Params", type=HUMANOID_PARAMS  # noqa: F722
    )
    first_person_params: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="FirstPerson Params", type=FIRSTPERSON_PARAMS  # noqa: F722
    )
    blendshape_group: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Blendshape Group", type=BLENDSHAPE_GROUP  # noqa: F722
    )
    spring_bones: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        name="Spring Bones", type=SPRING_BONE_GROUP  # noqa: F722
    )
    metas: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Metas", type=METAS  # noqa: F821
    )
    required_metas: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Required Metas", type=REQUIRED_METAS  # noqa: F722
    )
