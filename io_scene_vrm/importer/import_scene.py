import contextlib
import os
from typing import Set, Union, cast

import bpy
from bpy.app.translations import pgettext
from bpy_extras.io_utils import ImportHelper

from ..common import version
from ..common.logging import get_logger
from ..common.preferences import get_preferences, use_legacy_importer_exporter
from ..editor.ops import VRM_OT_open_url_in_web_browser
from .gltf2_addon_vrm_importer import Gltf2AddonVrmImporter, RetryUsingLegacyVrmImporter
from .legacy_vrm_importer import LegacyVrmImporter
from .license_validation import LicenseConfirmationRequired
from .vrm_parser import VrmParser

logger = get_logger(__name__)


class LicenseConfirmation(bpy.types.PropertyGroup):  # type: ignore[misc]
    message: bpy.props.StringProperty()  # type: ignore[valid-type]
    url: bpy.props.StringProperty()  # type: ignore[valid-type]
    json_key: bpy.props.StringProperty()  # type: ignore[valid-type]


def import_vrm_update_addon_preferences(
    import_op: bpy.types.Operator, context: bpy.types.Context
) -> None:
    preferences = get_preferences(context)

    if bool(preferences.set_shading_type_to_material_on_import) != bool(
        import_op.set_shading_type_to_material_on_import
    ):
        preferences.set_shading_type_to_material_on_import = (
            import_op.set_shading_type_to_material_on_import
        )

    if bool(preferences.set_view_transform_to_standard_on_import) != bool(
        import_op.set_view_transform_to_standard_on_import
    ):
        preferences.set_view_transform_to_standard_on_import = (
            import_op.set_view_transform_to_standard_on_import
        )

    if bool(preferences.set_armature_display_to_wire) != bool(
        import_op.set_armature_display_to_wire
    ):
        preferences.set_armature_display_to_wire = (
            import_op.set_armature_display_to_wire
        )

    if bool(preferences.set_armature_display_to_show_in_front) != bool(
        import_op.set_armature_display_to_show_in_front
    ):
        preferences.set_armature_display_to_show_in_front = (
            import_op.set_armature_display_to_show_in_front
        )


class IMPORT_SCENE_OT_vrm(bpy.types.Operator, ImportHelper):  # type: ignore[misc]
    bl_idname = "import_scene.vrm"
    bl_label = "Import VRM"
    bl_description = "Import VRM"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".vrm"
    filter_glob: bpy.props.StringProperty(  # type: ignore[valid-type]
        default="*.vrm", options={"HIDDEN"}  # noqa: F722,F821
    )

    extract_textures_into_folder: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Extract texture images into the folder",  # noqa: F722
        default=False,
    )
    make_new_texture_folder: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Don't overwrite existing texture folder (limit:100,000)",  # noqa: F722
        default=True,
    )
    set_shading_type_to_material_on_import: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name='Set shading type to "Material"',  # noqa: F722
        update=import_vrm_update_addon_preferences,
        default=True,
    )
    set_view_transform_to_standard_on_import: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name='Set view transform to "Standard"',  # noqa: F722
        update=import_vrm_update_addon_preferences,
        default=True,
    )
    set_armature_display_to_wire: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name='Set an imported armature display to "Wire"',  # noqa: F722
        update=import_vrm_update_addon_preferences,
        default=True,
    )
    set_armature_display_to_show_in_front: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name='Set an imported armature display to show "In-Front"',  # noqa: F722
        update=import_vrm_update_addon_preferences,
        default=True,
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        license_error = None
        try:
            return create_blend_model(
                self,
                context,
                license_validation=True,
            )
        except LicenseConfirmationRequired as e:
            license_error = e  # Prevent traceback dump on another exception

        logger.warning(license_error.description())

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
        preferences = get_preferences(context)
        (
            self.set_shading_type_to_material_on_import,
            self.set_view_transform_to_standard_on_import,
            self.set_armature_display_to_wire,
            self.set_armature_display_to_show_in_front,
        ) = (
            preferences.set_shading_type_to_material_on_import,
            preferences.set_view_transform_to_standard_on_import,
            preferences.set_armature_display_to_wire,
            preferences.set_armature_display_to_show_in_front,
        )

        if not use_legacy_importer_exporter() and "gltf" not in dir(
            bpy.ops.import_scene
        ):
            return cast(
                Set[str],
                bpy.ops.wm.vrm_gltf2_addon_disabled_warning(
                    "INVOKE_DEFAULT",
                ),
            )
        return cast(Set[str], ImportHelper.invoke(self, context, event))


class VRM_PT_import_unsupported_blender_version_warning(bpy.types.Panel):  # type: ignore[misc]
    bl_idname = "VRM_PT_import_unsupported_blender_version_warning"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_parent_id = "FILE_PT_operator"
    bl_label = ""
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return (
            str(context.space_data.active_operator.bl_idname) == "IMPORT_SCENE_OT_vrm"
            and not version.supported()
        )

    def draw(self, _context: bpy.types.Context) -> None:
        box = self.layout.box()
        warning_column = box.column()
        warning_message = pgettext(
            "The installed VRM add-on is\nnot compatible with Blender {blender_version}.\n"
            + "Please upgrade the add-on."
        ).format(blender_version=".".join(map(str, bpy.app.version[:2])))
        for index, warning_line in enumerate(warning_message.splitlines()):
            warning_column.label(
                text=warning_line,
                translate=False,
                icon="NONE" if index else "ERROR",
            )


class WM_OT_vrm_license_confirmation(bpy.types.Operator):  # type: ignore[misc]
    bl_label = "VRM License Confirmation"
    bl_idname = "wm.vrm_license_warning"
    bl_options = {"REGISTER", "UNDO"}

    filepath: bpy.props.StringProperty()  # type: ignore[valid-type]

    license_confirmations: bpy.props.CollectionProperty(type=LicenseConfirmation)  # type: ignore[valid-type]
    import_anyway: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Import Anyway",  # noqa: F722
    )

    extract_textures_into_folder: bpy.props.BoolProperty()  # type: ignore[valid-type]
    make_new_texture_folder: bpy.props.BoolProperty()  # type: ignore[valid-type]

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if not self.import_anyway:
            return {"CANCELLED"}
        return create_blend_model(
            self,
            context,
            license_validation=False,
        )

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> Set[str]:
        return cast(
            Set[str], context.window_manager.invoke_props_dialog(self, width=600)
        )

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(text=self.filepath, translate=False)
        for license_confirmation in self.license_confirmations:
            box = layout.box()
            for line in license_confirmation.message.split("\n"):
                box.label(text=line, translate=False, icon="INFO")
            if license_confirmation.json_key:
                box.label(
                    text=pgettext("For more information please check following URL.")
                )
                if VRM_OT_open_url_in_web_browser.supported(license_confirmation.url):
                    split = box.split(factor=0.85)
                    split.prop(
                        license_confirmation,
                        "url",
                        text=license_confirmation.json_key,
                        translate=False,
                    )
                    op = split.operator(VRM_OT_open_url_in_web_browser.bl_idname)
                    op.url = license_confirmation.url
                else:
                    box.prop(
                        license_confirmation,
                        "url",
                        text=license_confirmation.json_key,
                        translate=False,
                    )

        layout.prop(self, "import_anyway")


def create_blend_model(
    addon: Union[IMPORT_SCENE_OT_vrm, WM_OT_vrm_license_confirmation],
    context: bpy.types.Context,
    license_validation: bool,
) -> Set[str]:
    legacy_importer = use_legacy_importer_exporter()
    has_ui_localization = bpy.app.version < (2, 83)
    ui_localization = False
    if has_ui_localization:
        ui_localization = context.preferences.view.use_international_fonts
    try:
        if not legacy_importer:
            with contextlib.suppress(RetryUsingLegacyVrmImporter):
                parse_result = VrmParser(
                    addon.filepath,
                    addon.extract_textures_into_folder,
                    addon.make_new_texture_folder,
                    license_validation=license_validation,
                    legacy_importer=False,
                ).parse()

                Gltf2AddonVrmImporter(
                    context,
                    parse_result,
                    addon.extract_textures_into_folder,
                    addon.make_new_texture_folder,
                ).import_vrm()
                return {"FINISHED"}

        parse_result = VrmParser(
            addon.filepath,
            addon.extract_textures_into_folder,
            addon.make_new_texture_folder,
            license_validation=license_validation,
            legacy_importer=True,
        ).parse()
        LegacyVrmImporter(
            context,
            parse_result,
            addon.extract_textures_into_folder,
            addon.make_new_texture_folder,
        ).import_vrm()
    finally:
        if has_ui_localization and ui_localization:
            context.preferences.view.use_international_fonts = ui_localization

    return {"FINISHED"}


def menu_import(
    import_op: bpy.types.Operator, _context: bpy.types.Context
) -> None:  # Same as test/blender_io.py for now
    import_op.layout.operator(IMPORT_SCENE_OT_vrm.bl_idname, text="VRM (.vrm)")
