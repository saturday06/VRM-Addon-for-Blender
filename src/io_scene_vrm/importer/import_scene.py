# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Set as AbstractSet
from os import environ
from pathlib import Path
from typing import TYPE_CHECKING

import bpy
from bpy.app.translations import pgettext
from bpy.props import BoolProperty, CollectionProperty, StringProperty
from bpy.types import (
    Armature,
    Context,
    Event,
    Operator,
    Panel,
    PropertyGroup,
    SpaceFileBrowser,
)
from bpy_extras.io_utils import ImportHelper

from ..common import ops, version
from ..common.logger import get_logger
from ..common.preferences import (
    ImportPreferencesProtocol,
    copy_import_preferences,
    create_import_preferences_dict,
    draw_import_preferences_layout,
    get_preferences,
)
from ..editor import search
from ..editor.extension import get_armature_extension
from ..editor.ops import VRM_OT_open_url_in_web_browser, layout_operator
from ..editor.property_group import CollectionPropertyProtocol, StringPropertyGroup
from .abstract_base_vrm_importer import AbstractBaseVrmImporter, parse_vrm_json
from .license_validation import LicenseConfirmationRequiredError
from .vrm0_importer import Vrm0Importer
from .vrm1_importer import Vrm1Importer
from .vrm_animation_importer import VrmAnimationImporter

logger = get_logger(__name__)


class LicenseConfirmation(PropertyGroup):
    message: StringProperty()  # type: ignore[valid-type]
    url: StringProperty()  # type: ignore[valid-type]
    json_key: StringProperty()  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        message: str  # type: ignore[no-redef]
        url: str  # type: ignore[no-redef]
        json_key: str  # type: ignore[no-redef]


def import_vrm_update_addon_preferences(
    import_op: "IMPORT_SCENE_OT_vrm", context: Context
) -> None:
    if import_op.use_addon_preferences:
        copy_import_preferences(source=import_op, destination=get_preferences(context))


class IMPORT_SCENE_OT_vrm(Operator, ImportHelper):
    bl_idname = "import_scene.vrm"
    bl_label = "Open"
    bl_description = "import VRM"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    filename_ext = ".vrm"
    filter_glob: StringProperty(  # type: ignore[valid-type]
        default="*.vrm",
        options={"HIDDEN"},
    )

    use_addon_preferences: BoolProperty(  # type: ignore[valid-type]
        name="Import using add-on preferences",
        description="Import using add-on preferences instead of operator arguments",
    )

    extract_textures_into_folder: BoolProperty(  # type: ignore[valid-type]
        name="Extract texture images into the folder",
        update=import_vrm_update_addon_preferences,
        default=False,
    )
    make_new_texture_folder: BoolProperty(  # type: ignore[valid-type]
        name="Don't overwrite existing texture folder",
        update=import_vrm_update_addon_preferences,
        default=True,
    )
    set_shading_type_to_material_on_import: BoolProperty(  # type: ignore[valid-type]
        name='Set shading type to "Material"',
        update=import_vrm_update_addon_preferences,
        default=True,
    )
    set_view_transform_to_standard_on_import: BoolProperty(  # type: ignore[valid-type]
        name='Set view transform to "Standard"',
        update=import_vrm_update_addon_preferences,
        default=True,
    )
    set_armature_display_to_wire: BoolProperty(  # type: ignore[valid-type]
        name='Set an imported armature display to "Wire"',
        update=import_vrm_update_addon_preferences,
        default=True,
    )
    set_armature_display_to_show_in_front: BoolProperty(  # type: ignore[valid-type]
        name='Set an imported armature display to show "In-Front"',
        update=import_vrm_update_addon_preferences,
        default=True,
    )
    set_armature_bone_shape_to_default: BoolProperty(  # type: ignore[valid-type]
        name="Set an imported bone shape to default",
        update=import_vrm_update_addon_preferences,
        default=True,
    )
    enable_mtoon_outline_preview: BoolProperty(  # type: ignore[valid-type]
        name="Enable MToon Outline Preview",
        default=True,
    )

    def execute(self, context: Context) -> set[str]:
        filepath = Path(self.filepath)
        if not filepath.is_file():
            return {"CANCELLED"}

        if self.use_addon_preferences:
            copy_import_preferences(source=get_preferences(context), destination=self)

        license_error = None
        try:
            return import_vrm(
                filepath,
                self,
                context,
                license_validation=True,
            )
        except LicenseConfirmationRequiredError as e:
            license_error = e  # Prevent traceback dump on another exception

        logger.warning(license_error.description())

        execution_context = "INVOKE_DEFAULT"
        import_anyway = False
        if environ.get("BLENDER_VRM_AUTOMATIC_LICENSE_CONFIRMATION") == "true":
            execution_context = "EXEC_DEFAULT"
            import_anyway = True

        return ops.wm.vrm_license_warning(
            execution_context,
            import_anyway=import_anyway,
            license_confirmations=license_error.license_confirmations(),
            filepath=str(filepath),
            **create_import_preferences_dict(self),
        )

    def invoke(self, context: Context, event: Event) -> set[str]:
        self.use_addon_preferences = True
        copy_import_preferences(source=get_preferences(context), destination=self)

        if "gltf" not in dir(bpy.ops.import_scene):
            return ops.wm.vrm_gltf2_addon_disabled_warning("INVOKE_DEFAULT")
        return ImportHelper.invoke(self, context, event)

    def draw(self, _context: Context) -> None:
        pass  # Is needed to get panels available

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        filter_glob: str  # type: ignore[no-redef]
        use_addon_preferences: bool  # type: ignore[no-redef]
        extract_textures_into_folder: bool  # type: ignore[no-redef]
        make_new_texture_folder: bool  # type: ignore[no-redef]
        set_shading_type_to_material_on_import: bool  # type: ignore[no-redef]
        set_view_transform_to_standard_on_import: bool  # type: ignore[no-redef]
        set_armature_display_to_wire: bool  # type: ignore[no-redef]
        set_armature_display_to_show_in_front: bool  # type: ignore[no-redef]
        set_armature_bone_shape_to_default: bool  # type: ignore[no-redef]
        enable_mtoon_outline_preview: bool  # type: ignore[no-redef]


class VRM_PT_import_file_browser_tool_props(Panel):
    bl_idname = "VRM_PT_import_file_browser_tool_props"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_parent_id = "FILE_PT_operator"
    bl_label = ""
    bl_options: AbstractSet[str] = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        space_data = context.space_data
        if not isinstance(space_data, SpaceFileBrowser):
            return False
        return space_data.active_operator.bl_idname == "IMPORT_SCENE_OT_vrm"

    def draw(self, context: Context) -> None:
        space_data = context.space_data
        if not isinstance(space_data, SpaceFileBrowser):
            return

        operator = space_data.active_operator
        if not isinstance(operator, IMPORT_SCENE_OT_vrm):
            return

        layout = self.layout
        draw_import_preferences_layout(operator, layout)


class VRM_PT_import_unsupported_blender_version_warning(Panel):
    bl_idname = "VRM_PT_import_unsupported_blender_version_warning"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_parent_id = "FILE_PT_operator"
    bl_label = ""
    bl_options: AbstractSet[str] = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        space_data = context.space_data
        if not isinstance(space_data, SpaceFileBrowser):
            return False
        if space_data.active_operator.bl_idname != "IMPORT_SCENE_OT_vrm":
            return False
        return bool(version.panel_warning_message())

    def draw(self, _context: Context) -> None:
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


class WM_OT_vrm_license_confirmation(Operator):
    bl_label = "VRM License Confirmation"
    bl_idname = "wm.vrm_license_warning"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    filepath: StringProperty()  # type: ignore[valid-type]

    license_confirmations: CollectionProperty(type=LicenseConfirmation)  # type: ignore[valid-type]
    import_anyway: BoolProperty(  # type: ignore[valid-type]
        name="Import Anyway",
    )

    extract_textures_into_folder: BoolProperty()  # type: ignore[valid-type]
    make_new_texture_folder: BoolProperty()  # type: ignore[valid-type]
    set_shading_type_to_material_on_import: BoolProperty()  # type: ignore[valid-type]
    set_view_transform_to_standard_on_import: BoolProperty()  # type: ignore[valid-type]
    set_armature_display_to_wire: BoolProperty()  # type: ignore[valid-type]
    set_armature_display_to_show_in_front: BoolProperty()  # type: ignore[valid-type]
    set_armature_bone_shape_to_default: BoolProperty()  # type: ignore[valid-type]
    enable_mtoon_outline_preview: BoolProperty()  # type: ignore[valid-type]

    def execute(self, context: Context) -> set[str]:
        filepath = Path(self.filepath)
        if not filepath.is_file():
            return {"CANCELLED"}
        if not self.import_anyway:
            return {"CANCELLED"}
        return import_vrm(
            filepath,
            self,
            context,
            license_validation=False,
        )

    def invoke(self, context: Context, _event: Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self, width=600)

    def draw(self, _context: Context) -> None:
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
        # To regenerate, run the `uv run tools/property_typing.py` command.
        filepath: str  # type: ignore[no-redef]
        license_confirmations: CollectionPropertyProtocol[  # type: ignore[no-redef]
            LicenseConfirmation
        ]
        import_anyway: bool  # type: ignore[no-redef]
        extract_textures_into_folder: bool  # type: ignore[no-redef]
        make_new_texture_folder: bool  # type: ignore[no-redef]
        set_shading_type_to_material_on_import: bool  # type: ignore[no-redef]
        set_view_transform_to_standard_on_import: bool  # type: ignore[no-redef]
        set_armature_display_to_wire: bool  # type: ignore[no-redef]
        set_armature_display_to_show_in_front: bool  # type: ignore[no-redef]
        set_armature_bone_shape_to_default: bool  # type: ignore[no-redef]
        enable_mtoon_outline_preview: bool  # type: ignore[no-redef]


def import_vrm(
    filepath: Path,
    preferences: ImportPreferencesProtocol,
    context: Context,
    *,
    license_validation: bool,
) -> set[str]:
    parse_result = parse_vrm_json(filepath, license_validation=license_validation)
    if parse_result.spec_version_number >= (1,):
        vrm_importer: AbstractBaseVrmImporter = Vrm1Importer(
            context,
            parse_result,
            preferences,
        )
    else:
        vrm_importer = Vrm0Importer(
            context,
            parse_result,
            preferences,
        )

    vrm_importer.import_vrm()

    return {"FINISHED"}


def menu_import(
    menu_op: Operator, _context: Context
) -> None:  # Same as test/blender_io.py for now
    vrm_import_op = layout_operator(
        menu_op.layout, IMPORT_SCENE_OT_vrm, text="VRM (.vrm)"
    )
    vrm_import_op.use_addon_preferences = True

    vrma_import_op = layout_operator(
        menu_op.layout, IMPORT_SCENE_OT_vrma, text="VRM Animation (.vrma)"
    )
    vrma_import_op.armature_object_name = ""


class IMPORT_SCENE_OT_vrma(Operator, ImportHelper):
    bl_idname = "import_scene.vrma"
    bl_label = "Open"
    bl_description = "Import VRM Animation"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    filename_ext = ".vrma"
    filter_glob: StringProperty(  # type: ignore[valid-type]
        default="*.vrma",
        options={"HIDDEN"},
    )

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    def execute(self, context: Context) -> set[str]:
        if WM_OT_vrma_import_prerequisite.detect_errors(
            context, self.armature_object_name
        ):
            return ops.wm.vrma_import_prerequisite(
                "INVOKE_DEFAULT",
                armature_object_name=self.armature_object_name,
            )

        filepath = Path(self.filepath)
        if not filepath.is_file():
            return {"CANCELLED"}

        armature = None
        if self.armature_object_name:
            armature = context.blend_data.objects.get(self.armature_object_name)
            if not armature:
                return {"CANCELLED"}

        if not armature:
            armature = search.current_armature(context)

        if not armature:
            added = ops.icyp.make_basic_armature()
            if added != {"FINISHED"}:
                return added
            armature = search.current_armature(context)
            if not armature:
                return {"CANCELLED"}
            armature_data = armature.data
            if not isinstance(armature_data, Armature):
                return {"CANCELLED"}
            ext = get_armature_extension(armature_data)
            ext.spec_version = ext.SPEC_VERSION_VRM1

        return VrmAnimationImporter.execute(context, filepath, armature)

    def invoke(self, context: Context, event: Event) -> set[str]:
        if WM_OT_vrma_import_prerequisite.detect_errors(
            context, self.armature_object_name
        ):
            return ops.wm.vrma_import_prerequisite(
                "INVOKE_DEFAULT",
                armature_object_name=self.armature_object_name,
            )
        return ImportHelper.invoke(self, context, event)

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        filter_glob: str  # type: ignore[no-redef]
        armature_object_name: str  # type: ignore[no-redef]


class WM_OT_vrma_import_prerequisite(Operator):
    bl_label = "VRM Animation Import Prerequisite"
    bl_idname = "wm.vrma_import_prerequisite"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    armature_object_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )
    armature_object_name_candidates: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup,
        options={"HIDDEN"},
    )

    @staticmethod
    def detect_errors(context: Context, armature_object_name: str) -> list[str]:
        error_messages: list[str] = []

        if not armature_object_name:
            armature = search.current_armature(context)
        else:
            armature = context.blend_data.objects.get(armature_object_name)

        if not armature:
            return error_messages

        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return error_messages

        ext = get_armature_extension(armature_data)
        if get_armature_extension(armature_data).is_vrm1():
            humanoid = ext.vrm1.humanoid
            if not humanoid.human_bones.all_required_bones_are_assigned():
                error_messages.append(pgettext("Please assign required human bones"))
        else:
            error_messages.append(pgettext("Please set the version of VRM to 1.0"))

        return error_messages

    def execute(self, _context: Context) -> set[str]:
        return ops.import_scene.vrma(
            "INVOKE_DEFAULT", armature_object_name=self.armature_object_name
        )

    def invoke(self, context: Context, _event: Event) -> set[str]:
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

    def draw(self, context: Context) -> None:
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
        # To regenerate, run the `uv run tools/property_typing.py` command.
        armature_object_name: str  # type: ignore[no-redef]
        armature_object_name_candidates: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]
