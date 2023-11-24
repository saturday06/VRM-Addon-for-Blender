from collections.abc import Sequence
from typing import TYPE_CHECKING

import bpy

from . import version
from .logging import get_logger

logger = get_logger(__name__)

addon_package_name = ".".join(__name__.split(".")[:-2])


class VrmAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = addon_package_name

    INITIAL_ADDON_VERSION = (0, 0, 0)

    addon_version: bpy.props.IntVectorProperty(  # type: ignore[valid-type]
        size=3,
        default=INITIAL_ADDON_VERSION,
    )

    set_shading_type_to_material_on_import: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name='Set shading type to "Material"',
        default=True,
    )
    set_view_transform_to_standard_on_import: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name='Set view transform to "Standard"',
        default=True,
    )
    set_armature_display_to_wire: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name='Set an imported armature display to "Wire"',
        default=True,
    )
    set_armature_display_to_show_in_front: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name='Set an imported armature display to show "In-Front"',
        default=True,
    )

    export_invisibles: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export Invisible Objects",
    )
    export_only_selections: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export Only Selections",
    )
    export_only_deform_bones: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export Only Deform Bones",
        default=True,
    )
    export_apply_modifiers: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Apply Modifiers",
        default=True,
    )
    enable_advanced_preferences: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Enable Advanced Options",
    )
    export_fb_ngon_encoding: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Try the FB_ngon_encoding under development"
        + " (Exported meshes can be corrupted)",
    )
    export_all_influences: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export All Bone Influences (Don't limit to 4, most viewers truncate to 4, so bone movement may cause jagged meshes)",
        default=True,
    )
    export_lights: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export Lights",
    )
    use_active_scene: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Use Active Scene",
        default=True,
    )

    def draw(self, _context: bpy.types.Context) -> None:
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
        import_box.prop(self, "set_shading_type_to_material_on_import")
        import_box.prop(self, "set_view_transform_to_standard_on_import")
        import_box.prop(self, "set_armature_display_to_wire")
        import_box.prop(self, "set_armature_display_to_show_in_front")

        export_box = layout.box()
        export_box.label(text="Export", icon="EXPORT")
        export_box.prop(self, "export_invisibles")
        export_box.prop(self, "export_only_selections")
        export_box.prop(self, "export_only_deform_bones")
        export_box.prop(self, "export_apply_modifiers")
        export_box.prop(self, "enable_advanced_preferences")
        if self.enable_advanced_preferences:
            advanced_options_box = export_box.box()
            advanced_options_box.prop(self, "export_fb_ngon_encoding")
            advanced_options_box.prop(self, "export_all_influences")
            advanced_options_box.prop(self, "export_lights")
            advanced_options_box.prop(self, "use_active_scene")

    if TYPE_CHECKING:
        # This code is auto generated.
        # `poetry run ./tools/property_typing.py`
        addon_version: Sequence[int]  # type: ignore[no-redef]
        set_shading_type_to_material_on_import: bool  # type: ignore[no-redef]
        set_view_transform_to_standard_on_import: bool  # type: ignore[no-redef]
        set_armature_display_to_wire: bool  # type: ignore[no-redef]
        set_armature_display_to_show_in_front: bool  # type: ignore[no-redef]
        export_invisibles: bool  # type: ignore[no-redef]
        export_only_selections: bool  # type: ignore[no-redef]
        export_only_deform_bones: bool  # type: ignore[no-redef]
        export_apply_modifiers: bool  # type: ignore[no-redef]
        enable_advanced_preferences: bool  # type: ignore[no-redef]
        export_fb_ngon_encoding: bool  # type: ignore[no-redef]
        export_all_influences: bool  # type: ignore[no-redef]
        export_lights: bool  # type: ignore[no-redef]
        use_active_scene: bool  # type: ignore[no-redef]


def get_preferences(context: bpy.types.Context) -> VrmAddonPreferences:
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
