from typing import Optional

import bpy

addon_package_name_temp = ".".join(__name__.split(".")[:-2])
if not addon_package_name_temp:
    addon_package_name_temp = "VRM_Addon_for_Blender_fallback_key"
    print(f"VRM Add-on: Failed to detect add-on package name from __name__={__name__}")

if "addon_package_name" not in globals():
    addon_package_name = addon_package_name_temp
elif globals()["addon_package_name"] != addon_package_name_temp:
    print(
        "VRM Add-on: Accidentally package name is changed? addon_package_name: "
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
    enable_dangerous_vrm1_beta_features: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Enable Dangerous VRM 1.0 Beta Features",  # noqa: F722
        default=False,
    )

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        layout.prop(self, "export_invisibles")
        layout.prop(self, "export_only_selections")
        layout.prop(self, "enable_dangerous_vrm1_beta_features")


def use_legacy_importer_exporter() -> bool:
    return tuple(bpy.app.version) < (2, 83)


def get_preferences(context: bpy.types.Context) -> Optional[bpy.types.AddonPreferences]:
    addon = context.preferences.addons.get(addon_package_name)
    if addon:
        return addon.preferences
    print(f"WARNING: Failed to read add-on preferences for {addon_package_name}")
    return None
