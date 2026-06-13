# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from dataclasses import dataclass

from bpy.types import Armature, Context
from mathutils import Vector

from ...common import ops
from ...common.logger import get_logger
from ...common.scene_watcher import RunState, SceneWatcher
from ..extension_accessor import get_armature_extension
from .property_group import Vrm1LookAtPropertyGroup

_logger = get_logger(__name__)


@dataclass
class LookAtPreviewUpdater(SceneWatcher):
    object_index: int = 0

    def reset_run_progress(self) -> None:
        self.object_index = 0

    def run(self, context: Context) -> RunState:
        """Detect updates to the target object of Look At and update the state."""
        if not context.blend_data.armatures:
            return RunState.FINISH
        objects = context.visible_objects
        if not objects:
            return RunState.FINISH

        count = 50

        objects_len = len(objects)
        if self.object_index >= objects_len:
            self.object_index = 0

        start_object_index = self.object_index
        end_object_index = min(self.object_index + count, objects_len)
        for obj in objects[start_object_index:end_object_index]:
            if obj.type != "ARMATURE":
                continue
            armature_data = obj.data
            if not isinstance(armature_data, Armature):
                continue
            ext = get_armature_extension(armature_data)
            if not ext.is_vrm1():
                continue
            look_at = ext.vrm1.look_at
            if not look_at.enable_preview:
                continue
            preview_target_bpy_object = look_at.preview_target_bpy_object
            if not preview_target_bpy_object:
                continue
            if (
                Vector(look_at.previous_preview_target_bpy_object_location)
                - preview_target_bpy_object.location
            ).length_squared > 0:
                Vrm1LookAtPropertyGroup.update_all_previews(context)
                return RunState.FINISH

        self.object_index += count

        if end_object_index < objects_len:
            return RunState.PREEMPT

        return RunState.FINISH

    def create_fast_path_performance_test_objects(self, context: Context) -> None:
        blend_data = context.blend_data

        for i in range(300):
            if i % 3 != 0:
                mesh = blend_data.meshes.new(f"Mesh#{i}")
                obj = blend_data.objects.new(f"Object#{i}", mesh)
                context.scene.collection.objects.link(obj)
                continue

            ops.icyp.make_basic_armature()
            active_object = context.active_object
            if not active_object:
                message = f"Not an armature: {active_object}"
                raise ValueError(message)
            armature = active_object.data
            if not isinstance(armature, Armature):
                raise TypeError

            ext = get_armature_extension(armature)
            ext.spec_version = ext.SPEC_VERSION_VRM1
            look_at = ext.vrm1.look_at
            look_at.type = ext.vrm1.look_at.TYPE_BONE.identifier
            look_at.preview_target_bpy_object = blend_data.objects[
                i * 5 % len(blend_data.objects)
            ]
            ext.vrm1.look_at.enable_preview = True
