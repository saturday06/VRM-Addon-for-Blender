from typing import Optional

import bpy


def get_preferences(context: bpy.types.Context) -> Optional[bpy.types.AddonPreferences]:
    addon_name = ".".join(__name__.split(".")[:-3])
    addon = context.preferences.addons.get(addon_name)
    if addon:
        return addon.preferences
    print(f"WARNING: Failed to read addon preferences for {addon_name}")
    return None
