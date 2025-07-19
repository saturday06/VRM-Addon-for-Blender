# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol, TypedDict, Union

from bpy.app.translations import pgettext
from bpy.props import BoolProperty, IntVectorProperty
from bpy.types import AddonPreferences, Context, Operator, UILayout

from . import version
from .logger import get_logger

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
    enable_mtoon_outline_preview: bool


class ImportPreferencesDict(TypedDict):
    extract_textures_into_folder: bool
    make_new_texture_folder: bool
    set_shading_type_to_material_on_import: bool
    set_view_transform_to_standard_on_import: bool
    set_armature_display_to_wire: bool
    set_armature_display_to_show_in_front: bool
    set_armature_bone_shape_to_default: bool
    enable_mtoon_outline_preview: bool


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
        "enable_mtoon_outline_preview": source.enable_mtoon_outline_preview,
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
        destination.enable_mtoon_outline_preview,
    ) = (
        source.extract_textures_into_folder,
        source.make_new_texture_folder,
        source.set_shading_type_to_material_on_import,
        source.set_view_transform_to_standard_on_import,
        source.set_armature_display_to_wire,
        source.set_armature_display_to_show_in_front,
        source.set_armature_bone_shape_to_default,
        source.enable_mtoon_outline_preview,
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
    layout.prop(preferences, "enable_mtoon_outline_preview")


class ExportPreferencesProtocol(Protocol):
    export_invisibles: bool
    export_only_selections: bool
    enable_advanced_preferences: bool
    export_all_influences: bool
    export_lights: bool
    export_gltf_animations: bool
    export_try_sparse_sk: bool


def copy_export_preferences(
    *, source: ExportPreferencesProtocol, destination: ExportPreferencesProtocol
) -> None:
    (
        destination.export_invisibles,
        destination.export_only_selections,
        destination.enable_advanced_preferences,
        destination.export_all_influences,
        destination.export_lights,
        destination.export_gltf_animations,
        destination.export_try_sparse_sk,
    ) = (
        source.export_invisibles,
        source.export_only_selections,
        source.enable_advanced_preferences,
        source.export_all_influences,
        source.export_lights,
        source.export_gltf_animations,
        source.export_try_sparse_sk,
    )


def draw_advanced_options_description(
    preferences: Union[AddonPreferences, Operator],
    property_name: str,
    layout: UILayout,
    description: str,
) -> None:
    column = layout.box().column(align=True)
    column.prop(preferences, property_name)
    description_column = column.box().column(align=True)
    for i, line in enumerate(description.splitlines()):
        icon = "ERROR" if i == 0 else "NONE"
        description_column.label(text=line, translate=False, icon=icon)


def draw_export_preferences_layout(
    preferences: ExportPreferencesProtocol,
    layout: UILayout,
    *,
    show_vrm1_options: bool,
) -> None:
    if not isinstance(preferences, (AddonPreferences, Operator)):
        return

    layout.prop(preferences, "export_invisibles")
    layout.prop(preferences, "export_only_selections")

    if not show_vrm1_options:
        return

    layout.prop(preferences, "enable_advanced_preferences")
    if not preferences.enable_advanced_preferences:
        return

    advanced_options_column = layout.box().column()

    # UniVRM 0.115.0 doesn't support `export_try_sparse_sk`
    # https://github.com/saturday06/VRM-Addon-for-Blender/issues/381#issuecomment-1838365762
    draw_advanced_options_description(
        preferences,
        "export_try_sparse_sk",
        advanced_options_column,
        pgettext(
            "The file size will be reduced,\n"
            + "but it will no longer be readable by\n"
            + "older apps with UniVRM 0.115.0 or\n"
            + "earlier."
        ),
    )

    # The upstream says that Models may appear incorrectly in many viewers.
    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/356b3dda976303d3ecce8b3bd1591245e576db38/addons/io_scene_gltf2/__init__.py#L760
    draw_advanced_options_description(
        preferences,
        "export_all_influences",
        advanced_options_column,
        pgettext(
            "By default, 4 bone influences\n"
            + "are exported for each vertex. Many\n"
            + "apps truncate to 4. Increasing it\n"
            + "may cause jagged meshes."
        ),
    )

    draw_advanced_options_description(
        preferences,
        "export_lights",
        advanced_options_column,
        pgettext(
            "There is no consensus on how\n"
            + "to handle lights in VRM, so it is\n"
            + "impossible to predict what the\n"
            + "outcome will be."
        ),
    )

    draw_advanced_options_description(
        preferences,
        "export_gltf_animations",
        advanced_options_column,
        pgettext(
            "UniVRM does not export\n"
            + "glTF Animations, so it is disabled\n"
            + "by default. Please consider using\n"
            + "VRM Animation."
        ),
    )


class VrmAddonPreferences(AddonPreferences):
    bl_idname = addon_package_name

    INITIAL_ADDON_VERSION: tuple[int, int, int] = (0, 0, 0)

    addon_version: IntVectorProperty(  # type: ignore[valid-type]
        size=3,
        default=INITIAL_ADDON_VERSION,
    )

    add_mtoon_shader_node_group_automatically: BoolProperty(  # type: ignore[valid-type]
        name="Add MToon shader node group automatically",
        default=True,
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

    enable_mtoon_outline_preview: BoolProperty(  # type: ignore[valid-type]
        name="Enable MToon Outline Preview",
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
    export_all_influences: BoolProperty(  # type: ignore[valid-type]
        name="Export All Bone Influences",
    )
    export_lights: BoolProperty(  # type: ignore[valid-type]
        name="Export Lights",
    )
    export_gltf_animations: BoolProperty(  # type: ignore[valid-type]
        name="Export glTF Animations",
    )
    export_try_sparse_sk: BoolProperty(  # type: ignore[valid-type]
        name="Use Sparse Accessors",
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

        layout.prop(self, "add_mtoon_shader_node_group_automatically")

        import_box = layout.box()
        import_box.label(text="Import", icon="IMPORT")
        draw_import_preferences_layout(self, import_box)

        export_box = layout.box()
        export_box.label(text="Export", icon="EXPORT")
        draw_export_preferences_layout(self, export_box, show_vrm1_options=True)

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        addon_version: Sequence[int]  # type: ignore[no-redef]
        add_mtoon_shader_node_group_automatically: bool  # type: ignore[no-redef]
        extract_textures_into_folder: bool  # type: ignore[no-redef]
        make_new_texture_folder: bool  # type: ignore[no-redef]
        set_shading_type_to_material_on_import: bool  # type: ignore[no-redef]
        set_view_transform_to_standard_on_import: bool  # type: ignore[no-redef]
        set_armature_display_to_wire: bool  # type: ignore[no-redef]
        set_armature_display_to_show_in_front: bool  # type: ignore[no-redef]
        set_armature_bone_shape_to_default: bool  # type: ignore[no-redef]
        enable_mtoon_outline_preview: bool  # type: ignore[no-redef]
        export_invisibles: bool  # type: ignore[no-redef]
        export_only_selections: bool  # type: ignore[no-redef]
        enable_advanced_preferences: bool  # type: ignore[no-redef]
        export_all_influences: bool  # type: ignore[no-redef]
        export_lights: bool  # type: ignore[no-redef]
        export_gltf_animations: bool  # type: ignore[no-redef]
        export_try_sparse_sk: bool  # type: ignore[no-redef]


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
