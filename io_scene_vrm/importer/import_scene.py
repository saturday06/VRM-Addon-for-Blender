import contextlib
import os
from typing import Any, Set, cast

import bpy
from bpy.app.translations import pgettext
from bpy_extras.io_utils import ImportHelper

from ..common.preferences import use_legacy_importer_exporter
from .gltf2_addon_vrm_importer import Gltf2AddonVrmImporter, RetryUsingLegacyVrmImporter
from .legacy_vrm_importer import LegacyVrmImporter
from .license_validation import LicenseConfirmationRequired
from .vrm_parser import VrmParser


class LicenseConfirmation(bpy.types.PropertyGroup):  # type: ignore[misc]
    message: bpy.props.StringProperty()  # type: ignore[valid-type]
    url: bpy.props.StringProperty()  # type: ignore[valid-type]
    json_key: bpy.props.StringProperty()  # type: ignore[valid-type]


class IMPORT_SCENE_OT_vrm(bpy.types.Operator, ImportHelper):  # type: ignore[misc] # noqa: N801
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
                license_validation=True,
            )
        except LicenseConfirmationRequired as e:
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
                bpy.ops.wm.vrm_gltf2_addon_disabled_warning(
                    "INVOKE_DEFAULT",
                ),
            )
        return cast(Set[str], ImportHelper.invoke(self, context, event))


def create_blend_model(
    addon: Any,
    context: bpy.types.Context,
    license_validation: bool,
) -> Set[str]:
    legacy_importer = use_legacy_importer_exporter()
    has_ui_localization = bpy.app.version < (2, 83)
    ui_localization = False
    if has_ui_localization:
        ui_localization = bpy.context.preferences.view.use_international_fonts
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
            bpy.context.preferences.view.use_international_fonts = ui_localization

    return {"FINISHED"}


def menu_import(
    import_op: bpy.types.Operator, _context: bpy.types.Context
) -> None:  # Same as test/blender_io.py for now
    import_op.layout.operator(IMPORT_SCENE_OT_vrm.bl_idname, text="VRM (.vrm)")


class WM_OT_license_confirmation(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
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
                box.prop(
                    license_confirmation,
                    "url",
                    text=license_confirmation.json_key,
                    translate=False,
                )
        layout.prop(self, "import_anyway")
