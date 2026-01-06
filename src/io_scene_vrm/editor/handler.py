# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from typing import Final

import bpy
from bpy.app.handlers import persistent
from bpy.types import Depsgraph, Scene

from ..common.logger import get_logger
from . import migration
from .extension import get_scene_extension

logger = get_logger(__name__)


last_scene_state: Final[list[int]] = []


@persistent
def load_pre(_unused: object) -> None:
    last_scene_state.clear()


@persistent
def load_post(_unsed: object) -> None:
    migration.state.blend_file_compatibility_warning_shown = False
    migration.state.blend_file_addon_compatibility_warning_shown = False


@persistent
def depsgraph_update_post(_scene: Scene, depsgraph: Depsgraph) -> None:
    if depsgraph.id_type_updated("SCENE"):
        context = bpy.context
        scenes = context.blend_data.scenes
        scene_state = [scene.as_pointer() for scene in scenes]
        if last_scene_state != scene_state:
            last_scene_state.clear()
            last_scene_state.extend(scene_state)
            # Be careful as this can easily cause recursive calls
            for scene in scenes:
                get_scene_extension(scene).update_vrm0_material_property_names(context)
