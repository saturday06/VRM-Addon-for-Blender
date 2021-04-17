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
            preferences = get_preferences(context)
            if preferences:
                layout.prop(
                    preferences,
                    "export_invisibles",
                    text=vrm_helper.lang_support(
                        "Export invisible objects", "非表示オブジェクトを含める"
                    ),
                )
                layout.prop(
                    preferences,
                    "export_only_selections",
                    text=vrm_helper.lang_support(
                        "Export only selections", "選択されたオブジェクトのみ"
                    ),
                )
            vrm_validator_prop = layout.operator(
                vrm_helper.WM_OT_vrmValidator.bl_idname,
                text=vrm_helper.lang_support("Validate VRM model", "VRMモデルのチェック"),
                icon='VIEWZOOM'
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
        armature_box.operator(vrm_helper.Add_VRM_extensions_to_armature.bl_idname)
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
            icon = "HANDLE_AUTO"
            if req in data:
                show_ui(column, req, icon)
            else:
                show_add_require(column, req)
        column = row.column()
        for req in vrm_types.HumanBones.left_leg_req:
            icon = "HANDLE_AUTO"
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
            icon = "HANDLE_AUTO"
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
            icon = "HANDLE_AUTO"
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
            "armStretch",
        )
        layout.prop(
            active_object.vrm_props.humanoid_params,
            "upperArmTwist"
        )
        layout.prop(
            active_object.vrm_props.humanoid_params,
            "lowerArmTwist"
        )
        layout.separator()
        layout.label(text='Leg', icon="HANDLE_AUTO")
        layout.prop(
            active_object.vrm_props.humanoid_params,
            "legStretch"
        )
        layout.prop(
            active_object.vrm_props.humanoid_params,
            "upperLegTwist"
        )
        layout.prop(
            active_object.vrm_props.humanoid_params,
            "lowerLegTwist"
        )
        layout.prop(
            active_object.vrm_props.humanoid_params,
            "feetSpacing"
        )
        layout.prop(
            active_object.vrm_props.humanoid_params,
            "hasTranslationDoF"
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
        layout.prop(
            active_object.vrm_props.firstPerson_params,
            "firstPersonBone",
            icon='BONE_DATA'
        )
        layout.prop(
            active_object.vrm_props.firstPerson_params,
            "firstPersonBoneOffset",
            icon='BONE_DATA'
        )
        layout.prop(
            active_object.vrm_props.firstPerson_params,
            "lookAtTypeName"
        )
        # layout.prop(
        #     active_object.vrm_props.firstPerson_params,
        #     "meshAnnotations"
        # )
        box = layout.box()
        box.label(text='Look At Horizontal Inner',
                  icon='FULLSCREEN_EXIT')
        box.prop(
            active_object.vrm_props.firstPerson_params.lookAtHorizontalInner,
            "curve"
        )
        box.prop(
            active_object.vrm_props.firstPerson_params.lookAtHorizontalInner,
            "xRange"
        )
        box.prop(
            active_object.vrm_props.firstPerson_params.lookAtHorizontalInner,
            "yRange"
        )
        box = layout.box()
        box.label(text='Look At Horizontal Outer',
                  icon='FULLSCREEN_ENTER')
        box.prop(
            active_object.vrm_props.firstPerson_params.lookAtHorizontalOuter,
            "curve"
        )
        box.prop(
            active_object.vrm_props.firstPerson_params.lookAtHorizontalOuter,
            "xRange"
        )
        box.prop(
            active_object.vrm_props.firstPerson_params.lookAtHorizontalOuter,
            "yRange"
        )
        box = layout.box()
        box.label(text='Look At Vertical Down',
                  icon='TRIA_UP')
        box.prop(
            active_object.vrm_props.firstPerson_params.lookAtVerticalDown,
            "curve"
        )
        box.prop(
            active_object.vrm_props.firstPerson_params.lookAtVerticalDown,
            "xRange"
        )
        box.prop(
            active_object.vrm_props.firstPerson_params.lookAtVerticalDown,
            "yRange"
        )
        box = layout.box()
        box.label(text='Look At Vertical Up',
                  icon='TRIA_UP')
        box.prop(
            active_object.vrm_props.firstPerson_params.lookAtVerticalUp,
            "curve"
        )
        box.prop(
            active_object.vrm_props.firstPerson_params.lookAtVerticalUp,
            "xRange"
        )
        box.prop(
            active_object.vrm_props.firstPerson_params.lookAtVerticalUp,
            "yRange"
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
        layout.prop(
            active_object.vrm_props,
            "blendshape_group"
        )


class VRM_IMPORTER_PT_vrm_spring_bone(bpy.types.Panel):
    bl_idname = "VRM_IMPORTER_PT_vrm_spring_bone"
    bl_label = "VRM Spring Bone"
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
        layout.prop(
            active_object.vrm_props,
            "spring_bone",
        )


class VRM_IMPORTER_PT_vrm_metas(bpy.types.Panel):
    bl_idname = "VRM_IMPORTER_PT_vrm_metas"
    bl_label = "VRM Metas"
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
            "contactInformation",
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
            "allowedUserName",
            icon='MATCLOTH'
        )
        box.prop(
            active_object.vrm_props.required_metas,
            "violentUssageName",
            icon='ORPHAN_DATA'
        )
        box.prop(
            active_object.vrm_props.required_metas,
            "sexualUssageName",
            icon='HEART'
        )
        box.prop(
            active_object.vrm_props.required_metas,
            "commercialUssageName",
            icon='SOLO_OFF'
        )
        box.prop(
            active_object.vrm_props.required_metas,
            "licenseName",
            icon='COMMUNITY'
        )
        layout.prop(
            active_object.vrm_props.metas,
            "otherPermissionUrl",
            icon='URL'
        )
        if active_object.vrm_props.required_metas.licenseName == REQUIRED_METAS.LICENSENAME_OTHER:
            layout.prop(
                active_object.vrm_props.metas,
                "otherLicenseUrl",
                icon='URL'
            )


class HUMANOID_PARAMS(bpy.types.PropertyGroup):
    armStretch: bpy.props.FloatProperty(name='Arm Stretch')
    legStretch: bpy.props.FloatProperty(name='Leg Stretch')
    upperArmTwist: bpy.props.FloatProperty(name='Upper Arm Twist')
    lowerArmTwist: bpy.props.FloatProperty(name='Lower Arm Twist')
    upperLegTwist: bpy.props.FloatProperty(name='Upper Leg Twist')
    lowerLegTwist: bpy.props.FloatProperty(name='Lower Leg Twist')
    feetSpacing: bpy.props.IntProperty(name='Feet Spacing')
    hasTranslationDoF: bpy.props.BoolProperty(name='Has Translation DoF')


class LOOKAT_CURVE(bpy.types.PropertyGroup):
    curve: bpy.props.FloatVectorProperty(size=8, name='Curve')
    xRange: bpy.props.IntProperty(name='X Range')
    yRange: bpy.props.IntProperty(name='Y Range')


class FIRSTPERSON_PARAMS(bpy.types.PropertyGroup):
    firstPersonBone: bpy.props.StringProperty(name='First Person Bone')
    firstPersonBoneOffset: bpy.props.FloatVectorProperty(size=3, name='first Person Bone Offset')
    meshAnnotations = None  # Dummy
    lookAtTypeName: bpy.props.StringProperty(name='Look At Type Name')
    lookAtHorizontalInner: bpy.props.PointerProperty(type=LOOKAT_CURVE, name='Look At Horizontal Inner')
    lookAtHorizontalOuter: bpy.props.PointerProperty(type=LOOKAT_CURVE, name='Look At Horizontal Outer')
    lookAtVerticalDown: bpy.props.PointerProperty(type=LOOKAT_CURVE, name='Look At Vertical Down')
    lookAtVerticalUp: bpy.props.PointerProperty(type=LOOKAT_CURVE, name='lookAt Vertical Up')


class BLENDSHAPE_GROUP(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name='Name')
    presetName: bpy.props.StringProperty(name='Preset Name')
    binds = None  # Dummy
    materialValues = None  # Dummy
    isBinary: bpy.props.BoolProperty(name='Is Binary')


class SPRING_BONE(bpy.types.PropertyGroup):
    comment: bpy.props.StringProperty(name='Comment')
    stiffiness: bpy.props.IntProperty(name='stiffiness')
    gravityPower: bpy.props.IntProperty(name='Gravity Power')
    gravityDir: bpy.props.FloatVectorProperty(size=3, name='Gravity Dir')
    dragForce: bpy.props.FloatProperty(name='DragForce')
    center: bpy.props.IntProperty(name='Center')
    hitRadius: bpy.props.FloatProperty(name='Hit Radius')
    bones = None  # Dummy
    colliderGroups = None  # Dummy


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

    def get_contactInformation(self):
        key = "contactInformation"
        return self.id_data[key] if key in self.id_data else ""

    def set_contactInformation(self, value):
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

    def get_otherPermissionUrl(self):
        key = "otherPermissionUrl"
        return self.id_data[key] if key in self.id_data else ""

    def set_otherPermissionUrl(self, value):
        key = "otherPermissionUrl"
        if key in self.id_data:
            self.id_data[key] = value

    def get_otherLicenseUrl(self):
        key = "otherLicenseUrl"
        return self.id_data[key] if key in self.id_data else ""

    def set_otherLicenseUrl(self, value):
        key = "otherLicenseUrl"
        if key in self.id_data:
            self.id_data[key] = value

    version: bpy.props.StringProperty(name='Version',
                                      get=get_version,
                                      set=set_version)
    author: bpy.props.StringProperty(name='Author',
                                     get=get_author,
                                     set=set_author)
    contactInformation: bpy.props.StringProperty(name='ContactInformation',
                                                 get=get_contactInformation,
                                                 set=set_contactInformation)
    reference: bpy.props.StringProperty(name='Reference',
                                        get=get_reference,
                                        set=set_reference)
    title: bpy.props.StringProperty(name='Title',
                                    get=get_title,
                                    set=set_title)
    otherPermissionUrl: bpy.props.StringProperty(name='Other Permission Url',
                                                 get=get_otherPermissionUrl,
                                                 set=set_otherPermissionUrl)
    otherLicenseUrl: bpy.props.StringProperty(name='Other License Url',
                                              get=get_otherLicenseUrl,
                                              set=set_otherLicenseUrl)


class REQUIRED_METAS(bpy.types.PropertyGroup):
    INDEX_ID = 0
    INDEX_NUMBER = 3
    LICENSENAME_OTHER = "Other"
    allowedUserName_items = [
        ("OnlyAuthor", "OnlyAuthor", "", 0),
        ("ExplicitlyLicensedPerson", "ExplicitlyLicensedPerson", "", 1),
        ("Everyone", "Everyone", "", 2)
    ]
    violentUssageName_items = [
        ("Disallow", "Disallow", "", 0),
        ("Allow", "Allow", "", 1)
    ]
    sexualUssageName_items = [
        ("Disallow", "Disallow", "", 0),
        ("Allow", "Allow", "", 1)
    ]
    commercialUssageName_items = [
        ("Disallow", "Disallow", "", 0),
        ("Allow", "Allow", "", 1)
    ]
    licenseName_items = [
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

    def get_allowedUserName(self):
        key = "allowedUserName"
        if key in self.id_data:
            v = self.id_data[key]
            ret = 0
            for item in self.allowedUserName_items:
                if item[self.INDEX_ID] == v:
                    ret = item[self.INDEX_NUMBER]
            return ret
        else:
            return 0

    def set_allowedUserName(self, value):
        key = "allowedUserName"
        if key in self.id_data:
            self.id_data[key] = self.allowedUserName_items[value][self.INDEX_ID]

    def get_violentUssageName(self):
        key = "violentUssageName"
        if key in self.id_data:
            v = self.id_data[key]
            ret = 0
            for item in self.violentUssageName_items:
                if item[self.INDEX_ID] == v:
                    ret = item[self.INDEX_NUMBER]
            return ret
        else:
            return 0

    def set_violentUssageName(self, value):
        key = "violentUssageName"
        if key in self.id_data:
            self.id_data[key] = self.violentUssageName_items[value][self.INDEX_ID]

    def get_sexualUssageName(self):
        key = "sexualUssageName"
        if key in self.id_data:
            v = self.id_data[key]
            ret = 0
            for item in self.sexualUssageName_items:
                if item[self.INDEX_ID] == v:
                    ret = item[self.INDEX_NUMBER]
            return ret
        else:
            return 0

    def set_sexualUssageName(self, value):
        key = "sexualUssageName"
        if key in self.id_data:
            self.id_data[key] = self.sexualUssageName_items[value][self.INDEX_ID]

    def get_commercialUssageName(self):
        key = "commercialUssageName"
        if key in self.id_data:
            v = self.id_data[key]
            ret = 0
            for item in self.commercialUssageName_items:
                if item[self.INDEX_ID] == v:
                    ret = item[self.INDEX_NUMBER]
            return ret
        else:
            return 0

    def set_commercialUssageName(self, value):
        key = "commercialUssageName"
        if key in self.id_data:
            self.id_data[key] = self.commercialUssageName_items[value][self.INDEX_ID]

    def get_licenseName(self):
        key = "licenseName"
        if key in self.id_data:
            v = self.id_data[key]
            ret = 0
            for item in self.licenseName_items:
                if item[self.INDEX_ID] == v:
                    ret = item[self.INDEX_NUMBER]
            return ret
        else:
            return 0

    def set_licenseName(self, value):
        key = "licenseName"
        if key in self.id_data:
            self.id_data[key] = self.licenseName_items[value][self.INDEX_ID]

    allowedUserName: bpy.props.EnumProperty(items=allowedUserName_items,
                                            get=get_allowedUserName,
                                            set=set_allowedUserName,
                                            name='Allowed User')
    violentUssageName: bpy.props.EnumProperty(items=violentUssageName_items,
                                              get=get_violentUssageName,
                                              set=set_violentUssageName,
                                              name='Violent Ussage')
    sexualUssageName: bpy.props.EnumProperty(items=sexualUssageName_items,
                                             get=get_sexualUssageName,
                                             set=set_sexualUssageName,
                                             name='Sexual Ussage')
    commercialUssageName: bpy.props.EnumProperty(items=commercialUssageName_items,
                                                 get=get_commercialUssageName,
                                                 set=set_commercialUssageName,
                                                 name='Commercial Ussage')
    licenseName: bpy.props.EnumProperty(items=licenseName_items,
                                        get=get_licenseName,
                                        set=set_licenseName,
                                        name='License')


class VRMProps(bpy.types.PropertyGroup):
    humanoid_params: bpy.props.PointerProperty(name="Humanoid Params", type=HUMANOID_PARAMS)
    firstPerson_params: bpy.props.PointerProperty(name="FirstPerson Params", type=FIRSTPERSON_PARAMS)
    blendshape_group: bpy.props.CollectionProperty(name="Blendshape Group", type=BLENDSHAPE_GROUP)
    spring_bone: bpy.props.CollectionProperty(name="Spring Bone", type=SPRING_BONE)
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
    FIRSTPERSON_PARAMS,
    BLENDSHAPE_GROUP,
    SPRING_BONE,
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
