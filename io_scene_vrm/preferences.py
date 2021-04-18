from typing import Optional

import bpy

addon_package_name = ".".join(__name__.split(".")[:-2])


class VrmAddonPreferences(bpy.types.AddonPreferences):  # type: ignore[misc]
    bl_idname = addon_package_name

    export_invisibles: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export invisible objects",  # noqa: F722
        default=False,
    )
    export_only_selections: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export only selections",  # noqa: F722
        default=False,
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.prop(self, "export_invisibles")
        layout.prop(self, "export_only_selections")


def use_legacy_importer_exporter() -> bool:
    return bool(bpy.app.version < (2, 83))


def get_preferences(context: bpy.types.Context) -> Optional[bpy.types.AddonPreferences]:
    addon = context.preferences.addons.get(addon_package_name)
    if addon:
        return addon.preferences
    print(f"WARNING: Failed to read addon preferences for {addon_package_name}")
    return None
