# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from dataclasses import dataclass, field
from typing import Final

import bpy
from bpy.app.handlers import persistent
from bpy.types import Depsgraph, Scene

from ..common.logger import get_logger
from .extension_accessor import get_armature_extension, get_scene_extension
from .vrm1.ops import update_vrm1_expression_ui_list_elements

_logger = get_logger(__name__)


@dataclass
class State:
    last_scene_names: Final[list[str]] = field(default_factory=list[str])
    last_armature_names: Final[list[str]] = field(default_factory=list[str])

    def clear(self) -> None:
        self.last_scene_names.clear()
        self.last_armature_names.clear()


_state: Final = State()


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
            len(scenes) != len(_state.last_scene_names)
            or any(
                last_scene_name != scene.name
                for last_scene_name, scene in zip(_state.last_scene_names, scenes)
            )
        )
    ):
        new_scenes = [
            scene for scene in scenes if scene.name not in _state.last_scene_names
        ]
        _state.last_scene_names.clear()
        _state.last_scene_names.extend(scene.name for scene in scenes)
        for new_scene in new_scenes:
            get_scene_extension(new_scene).update_vrm0_material_property_names(context)

    if (
        depsgraph.id_type_updated("ARMATURE")
        and (True, armatures := context.blend_data.armatures)
        and (
            len(armatures) != len(_state.last_armature_names)
            or any(
                last_armature_name != armature.name
                for last_armature_name, armature in zip(
                    _state.last_armature_names, armatures
                )
            )
        )
    ):
        new_armatures = [
            armature
            for armature in armatures
            if armature.name not in _state.last_armature_names
        ]
        _state.last_armature_names.clear()
        _state.last_armature_names.extend(armature.name for armature in armatures)
        for new_armature in new_armatures:
            ext = get_armature_extension(new_armature)
            expressions = ext.vrm1.expressions
            expressions.fill_missing_expression_names()
        update_vrm1_expression_ui_list_elements(context)


def clear_global_variables() -> None:
    _state.clear()
