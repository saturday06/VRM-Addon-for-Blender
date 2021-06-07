import contextlib
import os
from typing import Any, Set, cast

import bpy
from bpy_extras.io_utils import ImportHelper

from .. import lang
from ..preferences import (
    use_experimental_vrm_component_ui,
    use_legacy_importer_exporter,
)
from . import blend_model
from .py_model import LicenseConfirmationRequired, PyModel


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
                py_model = PyModel(
                    addon.filepath,
                    addon.extract_textures_into_folder,
                    addon.make_new_texture_folder,
                    license_check=license_check,
                    legacy_importer=legacy_importer,
                )
                blend_model.BlendModel(
                    context,
                    py_model,
                    addon.extract_textures_into_folder,
                    addon.make_new_texture_folder,
                    legacy_importer=legacy_importer,
                    use_experimental_vrm_component_ui=use_experimental_vrm_component_ui(
                        context
                    ),
                )
                return {"FINISHED"}

        py_model = PyModel(
            addon.filepath,
            addon.extract_textures_into_folder,
            addon.make_new_texture_folder,
            license_check=license_check,
            legacy_importer=True,
        )
        blend_model.BlendModel(
            context,
            py_model,
            addon.extract_textures_into_folder,
            addon.make_new_texture_folder,
            legacy_importer=True,
            use_experimental_vrm_component_ui=use_experimental_vrm_component_ui(
                context
            ),
        )
    finally:
        if has_ui_localization and ui_localization:
            bpy.context.preferences.view.use_international_fonts = ui_localization

    return {"FINISHED"}


def menu_import(
    import_op: bpy.types.Operator, context: bpy.types.Context
) -> None:  # Same as test/blender_io.py for now
    import_op.layout.operator(ImportVRM.bl_idname, text="VRM (.vrm)")


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
                    text=lang.support(
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
            text=lang.support("Import anyway", "インポートします"),
        )
