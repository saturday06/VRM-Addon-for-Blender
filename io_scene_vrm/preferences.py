from typing import Callable, Optional

import bpy

addon_package_name = ".".join(__name__.split(".")[:-2])
if not addon_package_name:
    addon_package_name = "VRM_Addon_for_Blender_fallback_key"


class VrmAddonPreferences(bpy.types.AddonPreferences):  # type: ignore[misc]
    bl_idname = addon_package_name

    set_use_experimental_vrm_component_ui_callback: Callable[[bool], None]

    def get_use_experimental_vrm_component_ui(self) -> bool:
        return bool(self.get("use_experimental_vrm_component_ui", False))

    def set_use_experimental_vrm_component_ui(self, value: bool) -> None:
        key = "use_experimental_vrm_component_ui"
        if self.get(key) == value:
            return
        self[key] = value
        VrmAddonPreferences.set_use_experimental_vrm_component_ui_callback(value)

    export_invisibles: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export invisible objects",  # noqa: F722
        default=False,
    )
    export_only_selections: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Export only selections",  # noqa: F722
        default=False,
    )
    use_experimental_vrm_component_ui: bpy.props.BoolProperty(  # type: ignore[valid-type]
        name="Try experimental VRM component UI",  # noqa: F722
        default=False,
        get=get_use_experimental_vrm_component_ui,
        set=set_use_experimental_vrm_component_ui,
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.prop(self, "export_invisibles")
        layout.prop(self, "export_only_selections")

        testing_box = layout.box()
        testing_box.label(text="Testing", icon="EXPERIMENTAL")
        testing_box.prop(self, "use_experimental_vrm_component_ui")


def use_legacy_importer_exporter() -> bool:
    return bool(bpy.app.version < (2, 83))


def get_preferences(context: bpy.types.Context) -> Optional[bpy.types.AddonPreferences]:
    addon = context.preferences.addons.get(addon_package_name)
    if addon:
        return addon.preferences
    print(f"WARNING: Failed to read addon preferences for {addon_package_name}")
    return None


def use_experimental_vrm_component_ui(context: bpy.types.Context) -> bool:
    preferences = get_preferences(context)
    if not preferences:
        return False
    return bool(preferences.use_experimental_vrm_component_ui)
