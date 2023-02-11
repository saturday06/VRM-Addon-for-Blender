import bpy
from bpy.app.translations import pgettext

from . import version
from .logging import get_logger

logger = get_logger(__name__)

addon_package_name = ".".join(__name__.split(".")[:-2])


class VrmAddonPreferences(bpy.types.AddonPreferences):  # type: ignore[misc]
    bl_idname = addon_package_name

    INITIAL_ADDON_VERSION = (0, 0, 0)

    addon_version: bpy.props.IntVectorProperty(  # type: ignore[valid-type]
        size=3,  # noqa: F722
        default=INITIAL_ADDON_VERSION,
    )

    set_shading_type_to_material_on_import: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name='Set shading type to "Material"',  # noqa: F722
        default=True,
    )
    set_view_transform_to_standard_on_import: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name='Set view transform to "Standard"',  # noqa: F722
        default=True,
    )
    set_armature_display_to_wire: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name='Set an imported armature display to "Wire"',  # noqa: F722
        default=True,
    )
    set_armature_display_to_show_in_front: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name='Set an imported armature display to show "In-Front"',  # noqa: F722
        default=True,
    )

    export_invisibles: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export Invisible Objects",  # noqa: F722
    )
    export_only_selections: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export Only Selections",  # noqa: F722
    )
    enable_advanced_preferences: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Enable Advanced Options",  # noqa: F722
    )
    export_fb_ngon_encoding: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Try the FB_ngon_encoding under development (Exported meshes can be corrupted)",  # noqa: F722
    )

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout

        warning_message = None
        if version.blender_restart_required():
            warning_message = pgettext(
                "The VRM add-on has been updated. "
                + "Please restart Blender to apply the changes."
            )
        elif not version.supported():
            warning_message = pgettext(
                "The installed VRM add-on is not compatible with Blender {blender_version}. "
                + "Please upgrade the add-on."
            ).format(blender_version=".".join(map(str, bpy.app.version[:2])))

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
        export_box.prop(self, "enable_advanced_preferences")
        if self.enable_advanced_preferences:
            advanced_options_box = export_box.box()
            advanced_options_box.prop(self, "export_fb_ngon_encoding")


def use_legacy_importer_exporter() -> bool:
    return tuple(bpy.app.version) < (2, 83)


def get_preferences(context: bpy.types.Context) -> VrmAddonPreferences:
    addon = context.preferences.addons.get(addon_package_name)
    if not addon:
        raise AssertionError(f"No add-on preferences for {addon_package_name}")

    preferences = addon.preferences
    if not isinstance(preferences, VrmAddonPreferences):
        raise AssertionError(
            f"Add-on preferences for {addon_package_name} is not a VrmAddonPreferences"
            + f" but {type(preferences)}"
        )

    return preferences
