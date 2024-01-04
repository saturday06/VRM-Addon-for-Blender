from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol, TypedDict

from bpy.props import BoolProperty, IntVectorProperty
from bpy.types import AddonPreferences, Context, Operator, UILayout

from . import version
from .logging import get_logger

logger = get_logger(__name__)

addon_package_name = ".".join(__name__.split(".")[:-2])


class ImportPreferencesProtocol(Protocol):
    extract_textures_into_folder: bool
    make_new_texture_folder: bool
    set_shading_type_to_material_on_import: bool
    set_view_transform_to_standard_on_import: bool
    set_armature_display_to_wire: bool
    set_armature_display_to_show_in_front: bool
    set_armature_bone_shape_to_default: bool


class ImportPreferencesDict(TypedDict):
    extract_textures_into_folder: bool
    make_new_texture_folder: bool
    set_shading_type_to_material_on_import: bool
    set_view_transform_to_standard_on_import: bool
    set_armature_display_to_wire: bool
    set_armature_display_to_show_in_front: bool
    set_armature_bone_shape_to_default: bool


def create_import_preferences_dict(
    source: ImportPreferencesProtocol,
) -> ImportPreferencesDict:
    return {
        "extract_textures_into_folder": source.extract_textures_into_folder,
        "make_new_texture_folder": source.make_new_texture_folder,
        "set_shading_type_to_material_on_import": (
            source.set_shading_type_to_material_on_import
        ),
        "set_view_transform_to_standard_on_import": (
            source.set_view_transform_to_standard_on_import
        ),
        "set_armature_display_to_wire": (source.set_armature_display_to_wire),
        "set_armature_display_to_show_in_front": (
            source.set_armature_display_to_show_in_front
        ),
        "set_armature_bone_shape_to_default": source.set_armature_bone_shape_to_default,
    }


def copy_import_preferences(
    *, source: ImportPreferencesProtocol, destination: ImportPreferencesProtocol
) -> None:
    (
        destination.extract_textures_into_folder,
        destination.make_new_texture_folder,
        destination.set_shading_type_to_material_on_import,
        destination.set_view_transform_to_standard_on_import,
        destination.set_armature_display_to_wire,
        destination.set_armature_display_to_show_in_front,
        destination.set_armature_bone_shape_to_default,
    ) = (
        source.extract_textures_into_folder,
        source.make_new_texture_folder,
        source.set_shading_type_to_material_on_import,
        source.set_view_transform_to_standard_on_import,
        source.set_armature_display_to_wire,
        source.set_armature_display_to_show_in_front,
        source.set_armature_bone_shape_to_default,
    )


def draw_import_preferences_layout(
    preferences: ImportPreferencesProtocol, layout: UILayout
) -> None:
    if not isinstance(preferences, (AddonPreferences, Operator)):
        return

    layout.prop(preferences, "extract_textures_into_folder")
    layout.prop(preferences, "make_new_texture_folder")
    layout.prop(preferences, "set_shading_type_to_material_on_import")
    layout.prop(preferences, "set_view_transform_to_standard_on_import")
    layout.prop(preferences, "set_armature_display_to_wire")
    layout.prop(preferences, "set_armature_display_to_show_in_front")
    layout.prop(preferences, "set_armature_bone_shape_to_default")


class ExportPreferencesProtocol(Protocol):
    export_invisibles: bool
    export_only_selections: bool
    enable_advanced_preferences: bool
    export_fb_ngon_encoding: bool
    export_all_influences: bool
    export_lights: bool


def copy_export_preferences(
    *, source: ExportPreferencesProtocol, destination: ExportPreferencesProtocol
) -> None:
    (
        destination.export_invisibles,
        destination.export_only_selections,
        destination.enable_advanced_preferences,
        destination.export_fb_ngon_encoding,
        destination.export_all_influences,
        destination.export_lights,
    ) = (
        source.export_invisibles,
        source.export_only_selections,
        source.enable_advanced_preferences,
        source.export_fb_ngon_encoding,
        source.export_all_influences,
        destination.export_lights,
    )


def draw_export_preferences_layout(
    preferences: ExportPreferencesProtocol, layout: UILayout
) -> None:
    if not isinstance(preferences, (AddonPreferences, Operator)):
        return

    layout.prop(preferences, "export_invisibles")
    layout.prop(preferences, "export_only_selections")
    layout.prop(preferences, "enable_advanced_preferences")
    if preferences.enable_advanced_preferences:
        advanced_options_box = layout.box()
        advanced_options_box.prop(preferences, "export_fb_ngon_encoding")
        advanced_options_box.prop(preferences, "export_all_influences")
        advanced_options_box.prop(preferences, "export_lights")


class VrmAddonPreferences(AddonPreferences):
    bl_idname = addon_package_name

    INITIAL_ADDON_VERSION: tuple[int, int, int] = (0, 0, 0)

    addon_version: IntVectorProperty(  # type: ignore[valid-type]
        size=3,
        default=INITIAL_ADDON_VERSION,
    )

    extract_textures_into_folder: BoolProperty(  # type: ignore[valid-type]
        name="Extract texture images into the folder",
        default=False,
    )
    make_new_texture_folder: BoolProperty(  # type: ignore[valid-type]
        name="Don't overwrite existing texture folder",
        default=True,
    )
    set_shading_type_to_material_on_import: BoolProperty(  # type: ignore[valid-type]
        name='Set shading type to "Material"',
        default=True,
    )
    set_view_transform_to_standard_on_import: BoolProperty(  # type: ignore[valid-type]
        name='Set view transform to "Standard"',
        default=True,
    )
    set_armature_display_to_wire: BoolProperty(  # type: ignore[valid-type]
        name='Set an imported armature display to "Wire"',
        default=True,
    )
    set_armature_display_to_show_in_front: BoolProperty(  # type: ignore[valid-type]
        name='Set an imported armature display to show "In-Front"',
        default=True,
    )
    set_armature_bone_shape_to_default: BoolProperty(  # type: ignore[valid-type]
        name="Set an imported bone shape to default",
        default=True,
    )

    export_invisibles: BoolProperty(  # type: ignore[valid-type]
        name="Export Invisible Objects",
    )
    export_only_selections: BoolProperty(  # type: ignore[valid-type]
        name="Export Only Selections",
    )
    enable_advanced_preferences: BoolProperty(  # type: ignore[valid-type]
        name="Enable Advanced Options",
    )
    export_fb_ngon_encoding: BoolProperty(  # type: ignore[valid-type]
        name="Try the FB_ngon_encoding under development"
        + " (Exported meshes can be corrupted)",
    )
    export_all_influences: BoolProperty(  # type: ignore[valid-type]
        name="Export All Bone Influences",
        description="Don't limit to 4, most viewers truncate to 4, "
        + "so bone movement may cause jagged meshes",
        # The upstream says that Models may appear incorrectly in many viewers.
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/356b3dda976303d3ecce8b3bd1591245e576db38/addons/io_scene_gltf2/__init__.py#L760
        default=False,
    )
    export_lights: BoolProperty(  # type: ignore[valid-type]
        name="Export Lights",
    )

    def draw(self, _context: Context) -> None:
        layout = self.layout

        warning_message = version.preferences_warning_message()
        if warning_message:
            box = layout.box()
            warning_column = box.column()
            for index, warning_line in enumerate(warning_message.splitlines()):
                warning_column.label(
                    text=warning_line,
                    translate=False,
                    icon="NONE" if index else "ERROR",
                )

        import_box = layout.box()
        import_box.label(text="Import", icon="IMPORT")
        draw_import_preferences_layout(self, import_box)

        export_box = layout.box()
        export_box.label(text="Export", icon="EXPORT")
        draw_export_preferences_layout(self, export_box)

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run python tools/property_typing.py`
        addon_version: Sequence[int]  # type: ignore[no-redef]
        extract_textures_into_folder: bool  # type: ignore[no-redef]
        make_new_texture_folder: bool  # type: ignore[no-redef]
        set_shading_type_to_material_on_import: bool  # type: ignore[no-redef]
        set_view_transform_to_standard_on_import: bool  # type: ignore[no-redef]
        set_armature_display_to_wire: bool  # type: ignore[no-redef]
        set_armature_display_to_show_in_front: bool  # type: ignore[no-redef]
        set_armature_bone_shape_to_default: bool  # type: ignore[no-redef]
        export_invisibles: bool  # type: ignore[no-redef]
        export_only_selections: bool  # type: ignore[no-redef]
        enable_advanced_preferences: bool  # type: ignore[no-redef]
        export_fb_ngon_encoding: bool  # type: ignore[no-redef]
        export_all_influences: bool  # type: ignore[no-redef]
        export_lights: bool  # type: ignore[no-redef]


def get_preferences(context: Context) -> VrmAddonPreferences:
    addon = context.preferences.addons.get(addon_package_name)
    if not addon:
        message = f"No add-on preferences for {addon_package_name}"
        raise AssertionError(message)

    preferences = addon.preferences
    if not isinstance(preferences, VrmAddonPreferences):
        raise TypeError(
            f"Add-on preferences for {addon_package_name} is not a VrmAddonPreferences"
            + f" but {type(preferences)}"
        )

    return preferences
