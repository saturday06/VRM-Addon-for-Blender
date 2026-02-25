# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from typing import Final

import bpy
from bpy.app.handlers import persistent
from bpy.types import Depsgraph, Scene

from ..common import ops
from ..common.logger import get_logger
from . import migration
from .extension import get_armature_extension, get_scene_extension

logger = get_logger(__name__)


last_scene_names: Final[list[str]] = []
last_armature_names: Final[list[str]] = []


@persistent
def depsgraph_update_post(_scene: Scene, depsgraph: Depsgraph) -> None:
    # This callback is invoked very frequently,
    # so please keep the checks for changes as lightweight as possible.
    # Be careful as this can easily cause recursive calls.
    context = bpy.context

    if (
        depsgraph.id_type_updated("SCENE")
        and (True, scenes := context.blend_data.scenes)
        and (
            len(scenes) != len(last_scene_names)
            or any(
                last_scene_name != scene.name
                for last_scene_name, scene in zip(last_scene_names, scenes)
            )
        )
    ):
        new_scenes = [scene for scene in scenes if scene.name not in last_scene_names]
        last_scene_names.clear()
        last_scene_names.extend(scene.name for scene in scenes)
        for new_scene in new_scenes:
            get_scene_extension(new_scene).update_vrm0_material_property_names(context)

    if (
        depsgraph.id_type_updated("ARMATURE")
        and (True, armatures := context.blend_data.armatures)
        and (
            len(armatures) != len(last_armature_names)
            or any(
                last_armature_name != armature.name
                for last_armature_name, armature in zip(last_armature_names, armatures)
            )
        )
    ):
        new_armatures = [
            armature
            for armature in armatures
            if armature.name not in last_armature_names
        ]
        last_armature_names.clear()
        last_armature_names.extend(armature.name for armature in armatures)
        for new_armature in new_armatures:
            ext = get_armature_extension(new_armature)
            expressions = ext.vrm1.expressions
            expressions.fill_missing_expression_names()
            ops.vrm.update_vrm1_expression_ui_list_elements()


def clear_global_variables() -> None:
    migration.state.blend_file_compatibility_warning_shown = False
    migration.state.blend_file_addon_compatibility_warning_shown = False
    last_scene_names.clear()
    last_armature_names.clear()
