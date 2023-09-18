from os import environ
from pathlib import Path
from typing import TYPE_CHECKING, Union

import bpy
from bpy.app.translations import pgettext
from bpy_extras.io_utils import ImportHelper

from ..common import version
from ..common.logging import get_logger
from ..common.preferences import get_preferences
from ..editor import search
from ..editor.ops import VRM_OT_open_url_in_web_browser, layout_operator
from ..editor.property_group import CollectionPropertyProtocol, StringPropertyGroup
from .gltf2_addon_vrm_importer import Gltf2AddonVrmImporter
from .license_validation import LicenseConfirmationRequired
from .vrm_animation_importer import VrmAnimationImporter
from .vrm_parser import VrmParser

logger = get_logger(__name__)


class LicenseConfirmation(bpy.types.PropertyGroup):
    message: bpy.props.StringProperty()  # type: ignore[valid-type]
    url: bpy.props.StringProperty()  # type: ignore[valid-type]
    json_key: bpy.props.StringProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        message: str  # type: ignore[no-redef]
        url: str  # type: ignore[no-redef]
        json_key: str  # type: ignore[no-redef]


def import_vrm_update_addon_preferences(
    import_op: "IMPORT_SCENE_OT_vrm", context: bpy.types.Context
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


class IMPORT_SCENE_OT_vrm(bpy.types.Operator, ImportHelper):
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
        name="Don't overwrite existing texture folder",  # noqa: F722
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

    def execute(self, context: bpy.types.Context) -> set[str]:
        filepath = Path(self.filepath)
        if not filepath.is_file():
            return {"CANCELLED"}

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
        if environ.get("BLENDER_VRM_AUTOMATIC_LICENSE_CONFIRMATION") == "true":
            execution_context = "EXEC_DEFAULT"
            import_anyway = True

        return bpy.ops.wm.vrm_license_warning(
            execution_context,
            import_anyway=import_anyway,
            license_confirmations=license_error.license_confirmations(),
            filepath=str(filepath),
            extract_textures_into_folder=self.extract_textures_into_folder,
            make_new_texture_folder=self.make_new_texture_folder,
        )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
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

        if "gltf" not in dir(bpy.ops.import_scene):
            return bpy.ops.wm.vrm_gltf2_addon_disabled_warning("INVOKE_DEFAULT")
        return ImportHelper.invoke(self, context, event)

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        filter_glob: str  # type: ignore[no-redef]
        extract_textures_into_folder: bool  # type: ignore[no-redef]
        make_new_texture_folder: bool  # type: ignore[no-redef]
        set_shading_type_to_material_on_import: bool  # type: ignore[no-redef]
        set_view_transform_to_standard_on_import: bool  # type: ignore[no-redef]
        set_armature_display_to_wire: bool  # type: ignore[no-redef]
        set_armature_display_to_show_in_front: bool  # type: ignore[no-redef]


class VRM_PT_import_unsupported_blender_version_warning(bpy.types.Panel):
    bl_idname = "VRM_PT_import_unsupported_blender_version_warning"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_parent_id = "FILE_PT_operator"
    bl_label = ""
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        space_data = context.space_data
        if not isinstance(space_data, bpy.types.SpaceFileBrowser):
            return False
        if space_data.active_operator.bl_idname != "IMPORT_SCENE_OT_vrm":
            return False
        return bool(version.panel_warning_message())

    def draw(self, _context: bpy.types.Context) -> None:
        warning_message = version.panel_warning_message()
        if warning_message is None:
            return

        box = self.layout.box()
        warning_column = box.column(align=True)
        for index, warning_line in enumerate(warning_message.splitlines()):
            warning_column.label(
                text=warning_line,
                translate=False,
                icon="NONE" if index else "ERROR",
            )


class WM_OT_vrm_license_confirmation(bpy.types.Operator):
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

    def execute(self, context: bpy.types.Context) -> set[str]:
        filepath = Path(self.filepath)
        if not filepath.is_file():
            return {"CANCELLED"}
        if not self.import_anyway:
            return {"CANCELLED"}
        return create_blend_model(
            self,
            context,
            license_validation=False,
        )

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self, width=600)

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
                    split = box.split(factor=0.85, align=True)
                    split.prop(
                        license_confirmation,
                        "url",
                        text=license_confirmation.json_key,
                        translate=False,
                    )
                    op = layout_operator(split, VRM_OT_open_url_in_web_browser)
                    op.url = license_confirmation.url
                else:
                    box.prop(
                        license_confirmation,
                        "url",
                        text=license_confirmation.json_key,
                        translate=False,
                    )

        layout.prop(self, "import_anyway")

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        filepath: str  # type: ignore[no-redef]
        license_confirmations: CollectionPropertyProtocol[  # type: ignore[no-redef]
            LicenseConfirmation
        ]
        import_anyway: bool  # type: ignore[no-redef]
        extract_textures_into_folder: bool  # type: ignore[no-redef]
        make_new_texture_folder: bool  # type: ignore[no-redef]


def create_blend_model(
    addon: Union[IMPORT_SCENE_OT_vrm, WM_OT_vrm_license_confirmation],
    context: bpy.types.Context,
    license_validation: bool,
) -> set[str]:
    parse_result = VrmParser(
        Path(addon.filepath),
        addon.extract_textures_into_folder,
        addon.make_new_texture_folder,
        license_validation=license_validation,
    ).parse()

    Gltf2AddonVrmImporter(
        context,
        parse_result,
        addon.extract_textures_into_folder,
        addon.make_new_texture_folder,
    ).import_vrm()
    return {"FINISHED"}


def menu_import(
    menu_op: bpy.types.Operator, _context: bpy.types.Context
) -> None:  # Same as test/blender_io.py for now
    menu_op.layout.operator(IMPORT_SCENE_OT_vrm.bl_idname, text="VRM (.vrm)")
    vrma_import_op = layout_operator(
        menu_op.layout, IMPORT_SCENE_OT_vrma, text="VRM Animation DRAFT (.vrma)"
    )
    vrma_import_op.armature_object_name = ""


class IMPORT_SCENE_OT_vrma(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.vrma"
    bl_label = "Import VRM Animation"
    bl_description = "Import VRM Animation"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".vrma"
    filter_glob: bpy.props.StringProperty(  # type: ignore[valid-type]
        default="*.vrma", options={"HIDDEN"}  # noqa: F722,F821
    )

    armature_object_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        if WM_OT_vrma_import_prerequisite.detect_errors(
            context, self.armature_object_name
        ):
            return {"CANCELLED"}
        if not self.filepath:
            return {"CANCELLED"}
        if not self.armature_object_name:
            armature = search.current_armature(context)
        else:
            armature = context.blend_data.objects.get(self.armature_object_name)
        if not armature:
            return {"CANCELLED"}
        return VrmAnimationImporter.execute(context, Path(self.filepath), armature)

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        if WM_OT_vrma_import_prerequisite.detect_errors(
            context, self.armature_object_name
        ):
            return bpy.ops.wm.vrma_import_prerequisite(
                "INVOKE_DEFAULT",
                armature_object_name=self.armature_object_name,
            )
        return ImportHelper.invoke(self, context, event)

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        filter_glob: str  # type: ignore[no-redef]
        armature_object_name: str  # type: ignore[no-redef]


class WM_OT_vrma_import_prerequisite(bpy.types.Operator):
    bl_label = "VRM Animation Import Prerequisite"
    bl_idname = "wm.vrma_import_prerequisite"
    bl_options = {"REGISTER", "UNDO"}

    armature_object_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    armature_object_name_candidates: bpy.props.CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup,
        options={"HIDDEN"},  # noqa: F821
    )

    @staticmethod
    def detect_errors(
        context: bpy.types.Context, armature_object_name: str
    ) -> list[str]:
        error_messages = []

        if not armature_object_name:
            armature = search.current_armature(context)
        else:
            armature = context.blend_data.objects.get(armature_object_name)

        if not armature:
            error_messages.append(pgettext("Armature not found"))
            return error_messages

        armature_data = armature.data
        if not isinstance(armature_data, bpy.types.Armature):
            error_messages.append(pgettext("Armature not found"))
            return error_messages

        ext = armature_data.vrm_addon_extension
        if armature_data.vrm_addon_extension.is_vrm1():
            humanoid = ext.vrm1.humanoid
            if not bool(humanoid.human_bones.all_required_bones_are_assigned()):
                error_messages.append(pgettext("Please assign required human bones"))
        else:
            error_messages.append(pgettext("Please set the version of VRM to 1.0"))

        return error_messages

    def execute(self, _context: bpy.types.Context) -> set[str]:
        return bpy.ops.import_scene.vrma(
            "INVOKE_DEFAULT", armature_object_name=self.armature_object_name
        )

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        if not self.armature_object_name:
            armature_object = search.current_armature(context)
            if armature_object:
                self.armature_object_name = armature_object.name
        self.armature_object_name_candidates.clear()
        for obj in context.blend_data.objects:
            if obj.type != "ARMATURE":
                continue
            candidate = self.armature_object_name_candidates.add()
            candidate.value = obj.name
        return context.window_manager.invoke_props_dialog(self, width=800)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        layout.label(
            text="VRM Animation import requires a VRM 1.0 armature",
            icon="INFO",
        )

        error_messages = WM_OT_vrma_import_prerequisite.detect_errors(
            context, self.armature_object_name
        )

        layout.prop_search(
            self,
            "armature_object_name",
            self,
            "armature_object_name_candidates",
            icon="OUTLINER_OB_ARMATURE",
            text="Armature to be animated",
        )

        if error_messages:
            error_column = layout.box().column(align=True)
            for error_message in error_messages:
                error_column.label(text=error_message, icon="ERROR", translate=False)

        open_op = layout_operator(
            layout,
            VRM_OT_open_url_in_web_browser,
            icon="URL",
            text="Open help in a Web Browser",
        )
        open_op.url = pgettext("https://vrm-addon-for-blender.info/en/animation/")

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./scripts/property_typing.py`
        armature_object_name: str  # type: ignore[no-redef]
        armature_object_name_candidates: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]
