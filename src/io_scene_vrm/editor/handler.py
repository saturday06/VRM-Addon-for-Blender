# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from bpy.app.handlers import persistent

from . import migration


@persistent
def load_post(_unsed: object) -> None:
    migration.state.blend_file_compatibility_warning_shown = False
    migration.state.blend_file_addon_compatibility_warning_shown = False
