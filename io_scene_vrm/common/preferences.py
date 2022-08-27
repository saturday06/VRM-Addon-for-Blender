from typing import Any, Optional

import bpy
from bpy.app.translations import pgettext

from . import version
from .logging import get_logger

logger = get_logger(__name__)

addon_package_name_temp = ".".join(__name__.split(".")[:-2])
if not addon_package_name_temp:
    addon_package_name_temp = "VRM_Addon_for_Blender_fallback_key"
    logger.warning(f"Failed to detect add-on package name from __name__={__name__}")

if "addon_package_name" not in globals():
    addon_package_name = addon_package_name_temp
elif globals()["addon_package_name"] != addon_package_name_temp:
    logger.warning(
        "Accidentally package name is changed? addon_package_name: "
        + str(globals()["addon_package_name"])
        + f" => {addon_package_name_temp}, __name__: "
        + str(globals().get("previous_package_name"))
        + f" => {__name__}"
    )

previous_package_name = __name__


class VrmAddonPreferences(bpy.types.AddonPreferences):  # type: ignore[misc]
    bl_idname = addon_package_name

    export_invisibles: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export Invisible Objects",  # noqa: F722
        default=False,
    )
    export_only_selections: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export Only Selections",  # noqa: F722
        default=False,
    )
    show_experimental_features: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Show Experimetal Features",  # noqa: F722
        default=False,
    )

    def __get_export_fb_ngon_encoding(self) -> bool:
        return bool(self.show_experimental_features) and bool(
            self.get("hooked_export_fb_ngon_encoding")
        )

    def __set_export_fb_ngon_encoding(self, value: Any) -> None:
        self["hooked_export_fb_ngon_encoding"] = bool(value)

    export_fb_ngon_encoding: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Try the FB_ngon_encoding under development (Exported meshes can be corrupted)",  # noqa: F722
        get=__get_export_fb_ngon_encoding,
        set=__set_export_fb_ngon_encoding,
    )

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout

        if not version.supported():
            box = layout.box()
            warning_column = box.column()
            warning_message = pgettext(
                "The installed VRM add-on is not compatible with Blender {blender_version}. "
                + "Please upgrade the add-on."
            ).format(blender_version=".".join(map(str, bpy.app.version[:2])))
            for index, warning_line in enumerate(warning_message.splitlines()):
                warning_column.label(
                    text=warning_line,
                    translate=False,
                    icon="NONE" if index else "ERROR",
                )

        layout.prop(self, "export_invisibles")
        layout.prop(self, "export_only_selections")
        layout.prop(self, "show_experimental_features")
        if self.show_experimental_features:
            experimental_features_box = layout.box()
            experimental_features_box.prop(self, "export_fb_ngon_encoding")


def use_legacy_importer_exporter() -> bool:
    return tuple(bpy.app.version) < (2, 83)


def get_preferences(context: bpy.types.Context) -> Optional[bpy.types.AddonPreferences]:
    addon = context.preferences.addons.get(addon_package_name)
    if addon:
        return addon.preferences
    logger.warning(f"Failed to read add-on preferences for {addon_package_name}")
    return None
