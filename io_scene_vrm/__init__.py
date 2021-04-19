"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import contextlib
import os
from typing import Any, Set, cast

import bpy
from bpy.app.handlers import persistent
from bpy_extras.io_utils import ExportHelper, ImportHelper

from . import vrm_types
from .importer import blend_model, vrm_load
from .misc import (
    detail_mesh_maker,
    glb_factory,
    glsl_drawer,
    make_armature,
    mesh_from_bone_envelopes,
    version,
    vrm_helper,
)
from .misc.glsl_drawer import GlslDrawObj
from .misc.preferences import get_preferences

addon_package_name = ".".join(__name__.split(".")[:-1])


class VrmAddonPreferences(bpy.types.AddonPreferences):  # type: ignore[misc]
    bl_idname = addon_package_name

    export_invisibles: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export invisible objects",  # noqa: F722
        default=False,
    )
    export_only_selections: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export only selections",  # noqa: F722
        default=False,
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.prop(self, "export_invisibles")
        layout.prop(self, "export_only_selections")


class LicenseConfirmation(bpy.types.PropertyGroup):  # type: ignore[misc]
    message: bpy.props.StringProperty()  # type: ignore[valid-type]
    url: bpy.props.StringProperty()  # type: ignore[valid-type]
    json_key: bpy.props.StringProperty()  # type: ignore[valid-type]


class ImportVRM(bpy.types.Operator, ImportHelper):  # type: ignore[misc]
    bl_idname = "import_scene.vrm"
    bl_label = "Import VRM"
    bl_description = "Import VRM"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".vrm"
    filter_glob: bpy.props.StringProperty(  # type: ignore[valid-type]
        default="*.vrm", options={"HIDDEN"}  # noqa: F722,F821
    )

    extract_textures_into_folder: bpy.props.BoolProperty(  # type: ignore[valid-type]
        default=False, name="Extract texture images into the folder"  # noqa: F722
    )
    make_new_texture_folder: bpy.props.BoolProperty(  # type: ignore[valid-type]
        default=True,
        name="Don't overwrite existing texture folder (limit:100,000)",  # noqa: F722
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        license_error = None
        try:
            return create_blend_model(
                self,
                context,
                license_check=True,
            )
        except vrm_load.LicenseConfirmationRequired as e:
            license_error = e  # Prevent traceback dump on another exception

        print(license_error.description())

        execution_context = "INVOKE_DEFAULT"
        import_anyway = False
        if os.environ.get("BLENDER_VRM_AUTOMATIC_LICENSE_CONFIRMATION") == "true":
            execution_context = "EXEC_DEFAULT"
            import_anyway = True

        return cast(
            Set[str],
            bpy.ops.wm.vrm_license_warning(
                execution_context,
                import_anyway=import_anyway,
                license_confirmations=license_error.license_confirmations(),
                filepath=self.filepath,
                extract_textures_into_folder=self.extract_textures_into_folder,
                make_new_texture_folder=self.make_new_texture_folder,
            ),
        )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        if not use_legacy_importer_exporter() and "gltf" not in dir(
            bpy.ops.import_scene
        ):
            return cast(
                Set[str],
                bpy.ops.wm.gltf2_addon_disabled_warning(
                    "INVOKE_DEFAULT",
                ),
            )
        return cast(Set[str], ImportHelper.invoke(self, context, event))


def create_blend_model(
    addon: Any,
    context: bpy.types.Context,
    license_check: bool,
) -> Set[str]:
    legacy_importer = use_legacy_importer_exporter()
    has_ui_localization = bpy.app.version < (2, 83)
    ui_localization = False
    if has_ui_localization:
        ui_localization = bpy.context.preferences.view.use_international_fonts
    try:
        if not legacy_importer:
            with contextlib.suppress(blend_model.RetryUsingLegacyImporter):
                vrm_pydata = vrm_load.read_vrm(
                    addon.filepath,
                    addon.extract_textures_into_folder,
                    addon.make_new_texture_folder,
                    license_check=license_check,
                    legacy_importer=legacy_importer,
                )
                blend_model.BlendModel(
                    context,
                    vrm_pydata,
                    addon.extract_textures_into_folder,
                    addon.make_new_texture_folder,
                    legacy_importer=legacy_importer,
                )
                return {"FINISHED"}

        vrm_pydata = vrm_load.read_vrm(
            addon.filepath,
            addon.extract_textures_into_folder,
            addon.make_new_texture_folder,
            license_check=license_check,
            legacy_importer=True,
        )
        blend_model.BlendModel(
            context,
            vrm_pydata,
            addon.extract_textures_into_folder,
            addon.make_new_texture_folder,
            legacy_importer=True,
        )
    finally:
        if has_ui_localization and ui_localization:
            bpy.context.preferences.view.use_international_fonts = ui_localization

    return {"FINISHED"}


def use_legacy_importer_exporter() -> bool:
    return bool(bpy.app.version < (2, 83))


def menu_import(
    import_op: bpy.types.Operator, context: bpy.types.Context
) -> None:  # Same as test/blender_io.py for now
    import_op.layout.operator(ImportVRM.bl_idname, text="VRM (.vrm)")


def export_vrm_update_addon_preferences(
    export_op: bpy.types.Operator, context: bpy.types.Context
) -> None:
    preferences = get_preferences(context)
    if not preferences:
        return
    if bool(preferences.export_invisibles) != bool(export_op.export_invisibles):
        preferences.export_invisibles = export_op.export_invisibles
    if bool(preferences.export_only_selections) != bool(
        export_op.export_only_selections
    ):
        preferences.export_only_selections = export_op.export_only_selections


class ExportVRM(bpy.types.Operator, ExportHelper):  # type: ignore[misc]
    bl_idname = "export_scene.vrm"
    bl_label = "Export VRM"
    bl_description = "Export VRM"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".vrm"
    filter_glob: bpy.props.StringProperty(  # type: ignore[valid-type]
        default="*.vrm", options={"HIDDEN"}  # noqa: F722,F821
    )

    # vrm_version : bpy.props.EnumProperty(name="VRM version" ,items=(("0.0","0.0",""),("1.0","1.0","")))
    export_invisibles: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export invisible objects",  # noqa: F722
        update=export_vrm_update_addon_preferences,
    )
    export_only_selections: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export only selections",  # noqa: F722
        update=export_vrm_update_addon_preferences,
    )

    errors: bpy.props.CollectionProperty(type=vrm_helper.VrmValidationError)  # type: ignore[valid-type]

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if not self.filepath:
            return {"CANCELLED"}
        filepath: str = self.filepath

        try:
            glb_obj = glb_factory.GlbObj(
                bool(self.export_invisibles), bool(self.export_only_selections)
            )
        except glb_factory.GlbObj.ValidationError:
            return {"CANCELLED"}
        # vrm_bin =  glb_obj().convert_bpy2glb(self.vrm_version)
        vrm_bin = glb_obj.convert_bpy2glb("0.0")
        if vrm_bin is None:
            return {"CANCELLED"}
        with open(filepath, "wb") as f:
            f.write(vrm_bin)
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        preferences = get_preferences(context)
        if preferences:
            self.export_invisibles = bool(preferences.export_invisibles)
            self.export_only_selections = bool(preferences.export_only_selections)
        if not use_legacy_importer_exporter() and "gltf" not in dir(
            bpy.ops.export_scene
        ):
            return cast(
                Set[str],
                bpy.ops.wm.gltf2_addon_disabled_warning(
                    "INVOKE_DEFAULT",
                ),
            )
        return cast(Set[str], ExportHelper.invoke(self, context, event))

    def draw(self, context: bpy.types.Context) -> None:
        pass  # Is needed to get panels available


class VRM_IMPORTER_PT_export_error_messages(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_parent_id = "FILE_PT_operator"
    bl_label = ""
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return (
            str(context.space_data.active_operator.bl_idname) == "EXPORT_SCENE_OT_vrm"
        )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        operator = context.space_data.active_operator

        layout.prop(operator, "export_invisibles")
        layout.prop(operator, "export_only_selections")

        vrm_helper.WM_OT_vrmValidator.detect_errors_and_warnings(
            context, operator.errors, False, layout
        )


def menu_export(export_op: bpy.types.Operator, context: bpy.types.Context) -> None:
    export_op.layout.operator(ExportVRM.bl_idname, text="VRM (.vrm)")


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
                vrm_helper.WM_OT_vrmValidator.bl_idname,
                text=vrm_helper.lang_support("Validate VRM model", "VRMモデルのチェック"),
                icon='VIEWZOOM'
            )
            preferences = get_preferences(context)
            if preferences:
                layout.prop(
                    preferences,
                    "export_invisibles",
                    text=vrm_helper.lang_support(
                        "Export invisible objects", "非表示オブジェクトを含める"
                    )
                )
                layout.prop(
                    preferences,
                    "export_only_selections",
                    text=vrm_helper.lang_support(
                        "Export only selections", "選択されたオブジェクトのみ"
                    )
                )

            vrm_validator_prop.show_successful_message = True
            # vrm_validator_prop.errors = []  # これはできない
            layout.separator()
            layout.label(text="MToon preview")

            if GlslDrawObj.draw_objs:
                layout.operator(
                    glsl_drawer.ICYP_OT_Remove_Draw_Model.bl_idname,
                    icon='SHADING_RENDERED',
                    depress=True)
            else:
                if [obj for obj in bpy.data.objects if obj.type == "LIGHT"]:
                    layout.operator(glsl_drawer.ICYP_OT_Draw_Model.bl_idname,
                                    icon='SHADING_RENDERED',
                                    depress=False)
                else:
                    layout.box().label(
                        icon="INFO",
                        text=vrm_helper.lang_support("A light is required", "ライトが必要です"))
            if object_type == "MESH":
                layout.separator()
                layout.operator(vrm_helper.Vroid2VRC_lipsync_from_json_recipe.bl_idname,
                                icon="EXPERIMENTAL")
        if mode == "EDIT_MESH":
            layout.operator(bpy.ops.mesh.symmetry_snap.idname_py(),
                            icon='MOD_MIRROR')
        # endregion draw_main


class VRM_IMPORTER_PT_amature_controller(bpy.types.Panel):
    bl_idname = "VRM_IMPORTER_PT_amature_controller"
    bl_label = "VRM Amature Helper"
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

        def show_ui(parent, bone, icon):
            parent.prop_search(
                data, f'["{bone}"]', data, "bones", text=bone, icon=icon
            )

        def show_add_require(parent, bone):
            parent.operator(
                vrm_helper.Add_VRM_require_humanbone_custom_property.bl_idname,
                text=f"Add {bone} property",
                icon="ADD",
            )

        def show_add_defined(parent, bone):
            parent.operator(
                vrm_helper.Add_VRM_defined_humanbone_custom_property.bl_idname,
                text=f"Add {bone} property",
                icon="ADD",
            )

        armature_box = layout
        armature_box.operator(vrm_helper.Add_VRM_extensions_to_armature.bl_idname,
                              icon='MOD_BUILD')

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
        armature_box.operator(vrm_helper.Bones_rename.bl_idname,
                              icon="EXPERIMENTAL")


class WM_OT_gltf2AddonDisabledWarning(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_label = "glTF 2.0 add-on is disabled"
    bl_idname = "wm.gltf2_addon_disabled_warning"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        return cast(
            Set[str], context.window_manager.invoke_props_dialog(self, width=500)
        )

    def draw(self, context: bpy.types.Context) -> None:
        self.layout.label(
            text='Official add-on "glTF 2.0 format" is required. Please enable it.'
        )


class WM_OT_licenseConfirmation(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_label = "License confirmation"
    bl_idname = "wm.vrm_license_warning"
    bl_options = {"REGISTER", "UNDO"}

    filepath: bpy.props.StringProperty()  # type: ignore[valid-type]

    license_confirmations: bpy.props.CollectionProperty(type=LicenseConfirmation)  # type: ignore[valid-type]
    import_anyway: bpy.props.BoolProperty()  # type: ignore[valid-type]

    extract_textures_into_folder: bpy.props.BoolProperty()  # type: ignore[valid-type]
    make_new_texture_folder: bpy.props.BoolProperty()  # type: ignore[valid-type]

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if not self.import_anyway:
            return {"CANCELLED"}
        return create_blend_model(
            self,
            context,
            license_check=False,
        )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        return cast(
            Set[str], context.window_manager.invoke_props_dialog(self, width=600)
        )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(text=self.filepath)
        for license_confirmation in self.license_confirmations:
            for line in license_confirmation.message.split("\n"):
                layout.label(text=line)
            if license_confirmation.json_key:
                layout.label(
                    text=vrm_helper.lang_support(
                        "For more information please check following URL.",
                        "詳しくは下記のURLを確認してください。",
                    )
                )
                layout.prop(
                    license_confirmation,
                    "url",
                    text=license_confirmation.json_key,
                    translate=False,
                )
        layout.prop(
            self,
            "import_anyway",
            text=vrm_helper.lang_support("Import anyway", "インポートします"),
        )


class VRM_IMPORTER_PT_vrm_humanoid_params(bpy.types.Panel):
    bl_idname = "VRM_IMPORTER_PT_vrm_humanoid_params"
    bl_label = "VRM Humanoid Params"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        exist = context.object is not None
        armature = context.object.type == "ARMATURE"
        return exist and armature

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="ARMATURE_DATA")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        testing = layout.box()
        testing.label(text='Testing',
                      icon='EXPERIMENTAL')
        active_object = context.active_object
        layout.label(text='Arm', icon="VIEW_PAN")
        layout.prop(
            active_object.vrm_props.humanoid_params,
            "arm_stretch",
        )
        layout.prop(
            active_object.vrm_props.humanoid_params,
            "upper_arm_twist"
        )
        layout.prop(
            active_object.vrm_props.humanoid_params,
            "lower_arm_twist"
        )
        layout.separator()
        layout.label(text='Leg', icon="MOD_DYNAMICPAINT")
        layout.prop(
            active_object.vrm_props.humanoid_params,
            "leg_stretch"
        )
        layout.prop(
            active_object.vrm_props.humanoid_params,
            "upper_leg_twist"
        )
        layout.prop(
            active_object.vrm_props.humanoid_params,
            "lower_leg_twist"
        )
        layout.prop(
            active_object.vrm_props.humanoid_params,
            "feet_spacing"
        )
        layout.separator()
        layout.prop(
            active_object.vrm_props.humanoid_params,
            "has_translation_dof"
        )


class VRM_IMPORTER_PT_vrm_firstPerson_params(bpy.types.Panel):
    bl_idname = "VRM_IMPORTER_PT_vrm_firstPerson_params"
    bl_label = "VRM FirstPerson Params"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        exist = context.object is not None
        armature = context.object.type == "ARMATURE"
        return exist and armature

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="HIDE_OFF")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        testing = layout.box()
        testing.label(text='Testing',
                      icon='EXPERIMENTAL')
        active_object = context.active_object
        data = active_object.data
        blend_data = context.blend_data
        props = active_object.vrm_props.first_person_params
        layout.prop_search(props,
                           "first_person_bone",
                           data,
                           "bones")
        layout.prop(
            props,
            "first_person_bone_offset",
            icon='BONE_DATA'
        )
        layout.prop(
            props,
            "look_at_type_name"
        )
        for item in props.mesh_annotations:
            box = layout.row()
            box.prop_search(
                item,
                "mesh",
                blend_data,
                "meshes")
            box.prop(
                item,
                "first_person_flag"
            )
        box = layout.box()
        box.label(text='Look At Horizontal Inner',
                  icon='FULLSCREEN_EXIT')
        box.prop(
            props.look_at_horizontal_inner,
            "curve"
        )
        box.prop(
            props.look_at_horizontal_inner,
            "x_range"
        )
        box.prop(
            props.look_at_horizontal_inner,
            "y_range"
        )
        box = layout.box()
        box.label(text='Look At Horizontal Outer',
                  icon='FULLSCREEN_ENTER')
        box.prop(
            props.look_at_horizontal_outer,
            "curve"
        )
        box.prop(
            props.look_at_horizontal_outer,
            "x_range"
        )
        box.prop(
            props.look_at_horizontal_outer,
            "y_range"
        )
        box = layout.box()
        box.label(text='Look At Vertical Up',
                  icon='ANCHOR_TOP')
        box.prop(
            props.look_at_vertical_up,
            "curve"
        )
        box.prop(
            props.look_at_vertical_up,
            "x_range"
        )
        box.prop(
            props.look_at_vertical_up,
            "y_range"
        )
        box = layout.box()
        box.label(text='Look At Vertical Down',
                  icon='ANCHOR_BOTTOM')
        box.prop(
            props.look_at_vertical_down,
            "curve"
        )
        box.prop(
            props.look_at_vertical_down,
            "x_range"
        )
        box.prop(
            props.look_at_vertical_down,
            "y_range"
        )


class VRM_IMPORTER_PT_vrm_blendshape_group(bpy.types.Panel):
    bl_idname = "VRM_IMPORTER_PT_vrm_blendshape_group"
    bl_label = "VRM Blendshape Group"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        exist = context.object is not None
        armature = context.object.type == "ARMATURE"
        return exist and armature

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="SHAPEKEY_DATA")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        testing = layout.box()
        testing.label(text='Testing',
                      icon='EXPERIMENTAL')
        active_object = context.active_object
        blend_data = context.blend_data
        for blendshape in active_object.vrm_props.blendshape_group:
            box = layout.box()
            box.prop(
                blendshape,
                "name"
            )
            box.prop(
                blendshape,
                "preset_name"
            )

            box.prop(
                blendshape,
                "is_binary",
                icon='IPO_CONSTANT'
            )
            box.separator()
            row = box.row()
            row.prop(
                blendshape,
                "show_expanded_binds",
                icon='TRIA_DOWN' if blendshape.show_expanded_binds else 'TRIA_RIGHT',
                icon_only=True,
                emboss=False
            )
            row.label(text="Binds")
            if blendshape.show_expanded_binds:
                for bind in blendshape.binds:
                    box.prop_search(
                        bind,
                        "mesh",
                        blend_data,
                        "meshes"
                    )
                    box.prop(
                        bind,
                        "index"
                    )
                    box.prop(
                        bind,
                        "weight"
                    )
                    box.separator()
            box.label(text="materialValues is yet")


class VRM_IMPORTER_PT_vrm_spring_bone(bpy.types.Panel):
    bl_idname = "VRM_IMPORTER_PT_vrm_spring_bone"
    bl_label = "VRM Spring Bones"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        exist = context.object is not None
        armature = context.object.type == "ARMATURE"
        return exist and armature

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="RIGID_BODY_CONSTRAINT")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        testing = layout.box()
        testing.label(text='Testing',
                      icon='EXPERIMENTAL')
        active_object = context.active_object
        data = context.active_object.data
        spring_bones = active_object.vrm_props.spring_bones

        for spring_bone in spring_bones:
            box = layout.box()
            row = box.row()
            row.label(icon='REMOVE')
            # row.alignment = 'RIGHT'
            box.prop(
                spring_bone,
                "comment",
                icon='BOOKMARKS'
            )
            box.prop(
                spring_bone,
                "stiffiness",
                icon='RIGID_BODY_CONSTRAINT'
            )
            box.prop(
                spring_bone,
                "drag_force",
                icon='FORCE_DRAG'
            )
            box.separator()
            box.prop(
                spring_bone,
                "gravity_power",
                icon='OUTLINER_OB_FORCE_FIELD'
            )
            box.prop(
                spring_bone,
                "gravity_dir",
                icon='OUTLINER_OB_FORCE_FIELD'
            )
            box.separator()
            box.prop_search(spring_bone,
                            "center",
                            data,
                            "bones",
                            icon='PIVOT_MEDIAN')
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
                icon='TRIA_DOWN' if spring_bone.show_expanded_bones else 'TRIA_RIGHT',
                icon_only=True,
                emboss=False
            )
            row.label(text='Bones')
            if spring_bone.show_expanded_bones:
                for bone in spring_bone.bones:
                    box.prop_search(bone,
                                    "name",
                                    data,
                                    "bones")
            row = box.row()
            row.prop(
                spring_bone,
                "show_expanded_collider_groups",
                icon='TRIA_DOWN' if spring_bone.show_expanded_collider_groups else 'TRIA_RIGHT',
                icon_only=True,
                emboss=False
            )
            row.label(text='Collider Group')
            if spring_bone.show_expanded_collider_groups:
                for collider_group in spring_bone.collider_groups:
                    box.prop_search(collider_group,
                                    "name",
                                    data,
                                    "bones")


class VRM_IMPORTER_PT_vrm_metas(bpy.types.Panel):
    bl_idname = "VRM_IMPORTER_PT_vrm_metas"
    bl_label = "VRM Metas"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        exist = context.object is not None
        armature = context.object.type == "ARMATURE"
        return exist and armature

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="FILE_BLEND")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        testing = layout.box()
        testing.label(text='Testing',
                      icon='EXPERIMENTAL')
        active_object = context.active_object
        layout.prop(
            active_object.vrm_props.metas,
            "author",
            icon='USER'
        )
        layout.prop(
            active_object.vrm_props.metas,
            "contact_information",
            icon='URL'
        )
        layout.separator()
        layout.prop(
            active_object.vrm_props.metas,
            "title",
            icon='FILE_BLEND'
        )
        layout.prop(
            active_object.vrm_props.metas,
            "version",
            icon='LINENUMBERS_ON'
        )
        layout.prop(
            active_object.vrm_props.metas,
            "reference",
            icon='URL'
        )
        layout.separator()
        box = layout.box()
        box.prop(
            active_object.vrm_props.required_metas,
            "allowed_user_name",
            icon='MATCLOTH'
        )
        box.prop(
            active_object.vrm_props.required_metas,
            "violent_ussage_name",
            icon='ORPHAN_DATA'
        )
        box.prop(
            active_object.vrm_props.required_metas,
            "sexual_ussage_name",
            icon='FUND'
        )
        box.prop(
            active_object.vrm_props.required_metas,
            "commercial_ussage_name",
            icon='SOLO_OFF'
        )
        box.prop(
            active_object.vrm_props.required_metas,
            "license_name",
            icon='COMMUNITY'
        )
        if active_object.vrm_props.required_metas.license_name == REQUIRED_METAS.LICENSENAME_OTHER:
            layout.prop(
                active_object.vrm_props.metas,
                "other_license_url",
                icon='URL'
            )
        layout.prop(
            active_object.vrm_props.metas,
            "other_permission_url",
            icon='URL'
        )


class HUMANOID_PARAMS(bpy.types.PropertyGroup):
    arm_stretch: bpy.props.FloatProperty(name='Arm Stretch')
    leg_stretch: bpy.props.FloatProperty(name='Leg Stretch')
    upper_arm_twist: bpy.props.FloatProperty(name='Upper Arm Twist')
    lower_arm_twist: bpy.props.FloatProperty(name='Lower Arm Twist')
    upper_leg_twist: bpy.props.FloatProperty(name='Upper Leg Twist')
    lower_leg_twist: bpy.props.FloatProperty(name='Lower Leg Twist')
    feet_spacing: bpy.props.IntProperty(name='Feet Spacing')
    has_translation_dof: bpy.props.BoolProperty(name='Has Translation DoF')


class LOOKAT_CURVE(bpy.types.PropertyGroup):
    curve: bpy.props.FloatVectorProperty(size=8, name='Curve')
    x_range: bpy.props.IntProperty(name='X Range')
    y_range: bpy.props.IntProperty(name='Y Range')


class MESH_ANNOTATION(bpy.types.PropertyGroup):
    mesh: bpy.props.StringProperty(name='Mesh')
    first_person_flag_items = [
        ("Auto", "Auto", "", 0),
        ("FirstPersonOnly", "FirstPersonOnly", "", 1),
        ("ThirdPersonOnly", "ThirdPersonOnly", "", 2),
        ("Both", "Both", "", 3),
    ]
    first_person_flag: bpy.props.EnumProperty(items=first_person_flag_items,
                                              name='First Person Flag')


class FIRSTPERSON_PARAMS(bpy.types.PropertyGroup):
    first_person_bone: bpy.props.StringProperty(name='First Person Bone')
    first_person_bone_offset: bpy.props.FloatVectorProperty(size=3,
                                                            name='first Person Bone Offset',
                                                            subtype='TRANSLATION',
                                                            unit='LENGTH')
    mesh_annotations: bpy.props.CollectionProperty(name="Mesh Annotations", type=MESH_ANNOTATION)
    look_at_type_name_items = [
        ("Bone", "Bone", "Bone", "BONE_DATA", 0),
        ("BlendShape", "BlendShape", "BlendShape", "SHAPEKEY_DATA", 1)
    ]
    look_at_type_name: bpy.props.EnumProperty(items=look_at_type_name_items,
                                              name='Look At Type Name')
    look_at_horizontal_inner: bpy.props.PointerProperty(type=LOOKAT_CURVE, name='Look At Horizontal Inner')
    look_at_horizontal_outer: bpy.props.PointerProperty(type=LOOKAT_CURVE, name='Look At Horizontal Outer')
    look_at_vertical_down: bpy.props.PointerProperty(type=LOOKAT_CURVE, name='Look At Vertical Down')
    look_at_vertical_up: bpy.props.PointerProperty(type=LOOKAT_CURVE, name='lookAt Vertical Up')


class BLENDSHAPE_BIND(bpy.types.PropertyGroup):
    mesh: bpy.props.StringProperty(name='Mesh')
    index: bpy.props.StringProperty(name='Index')
    weight: bpy.props.FloatProperty(name='Weight')


class BLENDSHAPE_MATERIAL_BIND(bpy.types.PropertyGroup):
    material_name: bpy.props.StringProperty(name='Material Name')
    property_name: bpy.props.StringProperty(name='Property Name')
    targetValue = None   # Dummy


class BLENDSHAPE_GROUP(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name='Name')
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
        ("blink_r", "blink_r", "", "HIDE_ON", 17)
    ]
    preset_name: bpy.props.EnumProperty(items=preset_name_items,
                                        name='Preset')
    binds: bpy.props.CollectionProperty(type=BLENDSHAPE_BIND, name="Binds")
    material_values = bpy.props.CollectionProperty(type=BLENDSHAPE_MATERIAL_BIND, name="Material Values")
    is_binary: bpy.props.BoolProperty(name='Is Binary')
    show_expanded_binds: bpy.props.BoolProperty(name='Show Expanded Binds')


class COLLIDER_GROUP(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name='Name')


class BONE_GROUP(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name='Name')


class SPRING_BONE_GROUP(bpy.types.PropertyGroup):
    comment: bpy.props.StringProperty(name='Comment')
    stiffiness: bpy.props.IntProperty(name='Stiffiness')
    gravity_power: bpy.props.IntProperty(name='Gravity Power')
    gravity_dir: bpy.props.FloatVectorProperty(size=3, name='Gravity Dir')
    drag_force: bpy.props.FloatProperty(name='DragForce')
    center: bpy.props.StringProperty(name='Center')
    hit_radius: bpy.props.FloatProperty(name='Hit Radius')
    bones: bpy.props.CollectionProperty(name="Bones", type=BONE_GROUP)
    collider_groups: bpy.props.CollectionProperty(name="Collider Groups", type=COLLIDER_GROUP)
    show_expanded_bones: bpy.props.BoolProperty(name='Show Expanded Bones')    
    show_expanded_collider_groups: bpy.props.BoolProperty(name='Show Expanded Collider Groups')


class METAS(bpy.types.PropertyGroup):
    def get_version(self):
        key = "version"
        return self.id_data[key] if key in self.id_data else ""

    def set_version(self, value):
        key = "version"
        if key in self.id_data:
            self.id_data[key] = value

    def get_author(self):
        key = "author"
        return self.id_data[key] if key in self.id_data else ""

    def set_author(self, value):
        key = "author"
        if key in self.id_data:
            self.id_data[key] = value

    def get_contact_information(self):
        key = "contactInformation"
        return self.id_data[key] if key in self.id_data else ""

    def set_contact_information(self, value):
        key = "contactInformation"
        if key in self.id_data:
            self.id_data[key] = value

    def get_reference(self):
        key = "reference"
        return self.id_data[key] if key in self.id_data else ""

    def set_reference(self, value):
        key = "reference"
        if key in self.id_data:
            self.id_data[key] = value

    def get_title(self):
        key = "title"
        return self.id_data[key] if key in self.id_data else ""

    def set_title(self, value):
        key = "title"
        if key in self.id_data:
            self.id_data[key] = value

    def get_other_permission_url(self):
        key = "otherPermissionUrl"
        return self.id_data[key] if key in self.id_data else ""

    def set_other_permission_url(self, value):
        key = "otherPermissionUrl"
        if key in self.id_data:
            self.id_data[key] = value

    def get_other_license_url(self):
        key = "otherLicenseUrl"
        return self.id_data[key] if key in self.id_data else ""

    def set_other_license_url(self, value):
        key = "otherLicenseUrl"
        if key in self.id_data:
            self.id_data[key] = value

    version: bpy.props.StringProperty(name='Version',
                                      get=get_version,
                                      set=set_version)
    author: bpy.props.StringProperty(name='Author',
                                     get=get_author,
                                     set=set_author)
    contact_information: bpy.props.StringProperty(name='ContactInformation',
                                                  get=get_contact_information,
                                                  set=set_contact_information)
    reference: bpy.props.StringProperty(name='Reference',
                                        get=get_reference,
                                        set=set_reference)
    title: bpy.props.StringProperty(name='Title',
                                    get=get_title,
                                    set=set_title)
    other_permission_url: bpy.props.StringProperty(name='Other Permission Url',
                                                   get=get_other_permission_url,
                                                   set=set_other_permission_url)
    other_license_url: bpy.props.StringProperty(name='Other License Url',
                                                get=get_other_license_url,
                                                set=set_other_license_url)


class REQUIRED_METAS(bpy.types.PropertyGroup):
    INDEX_ID = 0
    INDEX_NUMBER = 3
    LICENSENAME_OTHER = "Other"
    allowed_user_name_items = [
        ("OnlyAuthor", "OnlyAuthor", "", 0),
        ("ExplicitlyLicensedPerson", "ExplicitlyLicensedPerson", "", 1),
        ("Everyone", "Everyone", "", 2)
    ]
    violent_ussage_name_items = [
        ("Disallow", "Disallow", "", 0),
        ("Allow", "Allow", "", 1)
    ]
    sexual_ussage_name_items = [
        ("Disallow", "Disallow", "", 0),
        ("Allow", "Allow", "", 1)
    ]
    commercial_ussage_name_items = [
        ("Disallow", "Disallow", "", 0),
        ("Allow", "Allow", "", 1)
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
        (LICENSENAME_OTHER, LICENSENAME_OTHER, "", 8),
    ]

    def get_allowed_user_name(self):
        key = "allowedUserName"
        if key in self.id_data:
            v = self.id_data[key]
            ret = 0
            for item in self.allowed_user_name_items:
                if item[self.INDEX_ID] == v:
                    ret = item[self.INDEX_NUMBER]
            return ret
        else:
            return 0

    def set_allowed_user_name(self, value):
        key = "allowedUserName"
        if key in self.id_data:
            self.id_data[key] = self.allowed_user_name_items[value][self.INDEX_ID]

    def get_violent_ussage_name(self):
        key = "violentUssageName"
        if key in self.id_data:
            v = self.id_data[key]
            ret = 0
            for item in self.violent_ussage_name_items:
                if item[self.INDEX_ID] == v:
                    ret = item[self.INDEX_NUMBER]
            return ret
        else:
            return 0

    def set_violent_ussage_name(self, value):
        key = "violentUssageName"
        if key in self.id_data:
            self.id_data[key] = self.violent_ussage_name_items[value][self.INDEX_ID]

    def get_sexual_ussage_name(self):
        key = "sexualUssageName"
        if key in self.id_data:
            v = self.id_data[key]
            ret = 0
            for item in self.sexual_ussage_name_items:
                if item[self.INDEX_ID] == v:
                    ret = item[self.INDEX_NUMBER]
            return ret
        else:
            return 0

    def set_sexual_ussage_name(self, value):
        key = "sexualUssageName"
        if key in self.id_data:
            self.id_data[key] = self.sexual_ussage_name_items[value][self.INDEX_ID]

    def get_commercial_ussage_name(self):
        key = "commercialUssageName"
        if key in self.id_data:
            v = self.id_data[key]
            ret = 0
            for item in self.commercial_ussage_name_items:
                if item[self.INDEX_ID] == v:
                    ret = item[self.INDEX_NUMBER]
            return ret
        else:
            return 0

    def set_commercial_ussage_name(self, value):
        key = "commercialUssageName"
        if key in self.id_data:
            self.id_data[key] = self.commercial_ussage_name_items[value][self.INDEX_ID]

    def get_license_name(self):
        key = "licenseName"
        if key in self.id_data:
            v = self.id_data[key]
            ret = 0
            for item in self.license_name_items:
                if item[self.INDEX_ID] == v:
                    ret = item[self.INDEX_NUMBER]
            return ret
        else:
            return 0

    def set_license_name(self, value):
        key = "licenseName"
        if key in self.id_data:
            self.id_data[key] = self.license_name_items[value][self.INDEX_ID]

    allowed_user_name: bpy.props.EnumProperty(items=allowed_user_name_items,
                                              get=get_allowed_user_name,
                                              set=set_allowed_user_name,
                                              name='Allowed User')
    violent_ussage_name: bpy.props.EnumProperty(items=violent_ussage_name_items,
                                                get=get_violent_ussage_name,
                                                set=set_violent_ussage_name,
                                                name='Violent Ussage')
    sexual_ussage_name: bpy.props.EnumProperty(items=sexual_ussage_name_items,
                                               get=get_sexual_ussage_name,
                                               set=set_sexual_ussage_name,
                                               name='Sexual Ussage')
    commercial_ussage_name: bpy.props.EnumProperty(items=commercial_ussage_name_items,
                                                   get=get_commercial_ussage_name,
                                                   set=set_commercial_ussage_name,
                                                   name='Commercial Ussage')
    license_name: bpy.props.EnumProperty(items=license_name_items,
                                         get=get_license_name,
                                         set=set_license_name,
                                         name='License')


class VRMProps(bpy.types.PropertyGroup):
    humanoid_params: bpy.props.PointerProperty(name="Humanoid Params", type=HUMANOID_PARAMS)
    first_person_params: bpy.props.PointerProperty(name="FirstPerson Params", type=FIRSTPERSON_PARAMS)
    blendshape_group: bpy.props.CollectionProperty(name="Blendshape Group", type=BLENDSHAPE_GROUP)
    spring_bones: bpy.props.CollectionProperty(name="Spring Bones", type=SPRING_BONE_GROUP)
    metas: bpy.props.PointerProperty(name="Metas", type=METAS)
    required_metas: bpy.props.PointerProperty(name="Required Metas", type=REQUIRED_METAS)


if persistent:  # for fake-bpy-modules

    @persistent  # type: ignore[misc]
    def add_shaders(self: Any) -> None:
        filedir = os.path.join(
            os.path.dirname(__file__), "resources", "material_node_groups.blend"
        )
        with bpy.data.libraries.load(filedir, link=False) as (data_from, data_to):
            for nt in data_from.node_groups:
                if nt not in bpy.data.node_groups:
                    data_to.node_groups.append(nt)


classes = [
    VrmAddonPreferences,
    LicenseConfirmation,
    WM_OT_licenseConfirmation,
    WM_OT_gltf2AddonDisabledWarning,
    vrm_helper.Bones_rename,
    vrm_helper.Add_VRM_extensions_to_armature,
    vrm_helper.Add_VRM_require_humanbone_custom_property,
    vrm_helper.Add_VRM_defined_humanbone_custom_property,
    vrm_helper.Vroid2VRC_lipsync_from_json_recipe,
    vrm_helper.VrmValidationError,
    vrm_helper.WM_OT_vrmValidator,
    ImportVRM,
    ExportVRM,
    VRM_IMPORTER_PT_export_error_messages,
    VRM_IMPORTER_PT_controller,
    make_armature.ICYP_OT_MAKE_ARMATURE,
    glsl_drawer.ICYP_OT_Draw_Model,
    glsl_drawer.ICYP_OT_Remove_Draw_Model,
    # detail_mesh_maker.ICYP_OT_DETAIL_MESH_MAKER,
    # blend_model.ICYP_OT_select_helper,
    # mesh_from_bone_envelopes.ICYP_OT_MAKE_MESH_FROM_BONE_ENVELOPES
    VRM_IMPORTER_PT_amature_controller,
    HUMANOID_PARAMS,
    LOOKAT_CURVE,
    MESH_ANNOTATION,
    FIRSTPERSON_PARAMS,
    BLENDSHAPE_BIND,
    BLENDSHAPE_MATERIAL_BIND,
    BLENDSHAPE_GROUP,
    COLLIDER_GROUP,
    BONE_GROUP,
    SPRING_BONE_GROUP,
    METAS,
    REQUIRED_METAS,
    VRMProps,
    VRM_IMPORTER_PT_vrm_humanoid_params,
    VRM_IMPORTER_PT_vrm_firstPerson_params,
    VRM_IMPORTER_PT_vrm_blendshape_group,
    VRM_IMPORTER_PT_vrm_spring_bone,
    VRM_IMPORTER_PT_vrm_metas
]

translation_dictionary = {
    "ja_JP": {
        ("*", "Export invisible objects"): "非表示のオブジェクトも含める",
        ("*", "Export only selections"): "選択されたオブジェクトのみ",
        ("*", "MToon preview"): "MToonのプレビュー",
        ("*", "No error. Ready for export VRM"): "エラーはありませんでした。VRMのエクスポートをすることができます",
        ("*", "VRM Export"): "VRMエクスポート",
        ("*", "Validate VRM model"): "VRMモデルのチェック",
        ("*", "Extract texture images into the folder"): "テクスチャ画像をフォルダに展開",
        (
            "*",
            'Official add-on "glTF 2.0 format" is required. Please enable it.',
        ): "公式アドオン「glTF 2.0 format」が必要です。有効化してください。",
    }
}


# アドオン有効化時の処理
def register(init_version: Any) -> None:
    # Sanity check
    if init_version != version.version():
        raise Exception(f"Version mismatch: {init_version} != {version.version()}")

    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_export)
    bpy.types.VIEW3D_MT_armature_add.append(add_armature)
    # bpy.types.VIEW3D_MT_mesh_add.append(make_mesh)
    bpy.app.handlers.load_post.append(add_shaders)
    bpy.app.translations.register(addon_package_name, translation_dictionary)
    bpy.types.Object.vrm_props = \
        bpy.props.PointerProperty(type=VRMProps)


# アドオン無効化時の処理
def unregister() -> None:
    del bpy.types.Object.vrm_props
    bpy.app.translations.unregister(addon_package_name)
    bpy.app.handlers.load_post.remove(add_shaders)
    bpy.types.VIEW3D_MT_armature_add.remove(add_armature)
    # bpy.types.VIEW3D_MT_mesh_add.remove(make_mesh)
    bpy.types.TOPBAR_MT_file_import.remove(menu_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_export)
    for cls in classes:
        bpy.utils.unregister_class(cls)
