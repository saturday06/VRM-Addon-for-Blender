# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from dataclasses import dataclass

from bpy.types import Armature, Context
from mathutils import Vector

from ...common import ops
from ...common.logger import get_logger
from ...common.scene_watcher import RunState, SceneWatcher
from ..extension import get_armature_extension
from .property_group import Vrm1LookAtPropertyGroup

logger = get_logger(__name__)


@dataclass
class LookAtPreviewUpdater(SceneWatcher):
    armature_index: int = 0

    def reset_run_progress(self) -> None:
        self.armature_index = 0

    def run(self, context: Context) -> RunState:
        """Look Atの対象オブジェクトの更新を検知し、LookAtの状態を更新."""
        blend_data = context.blend_data

        if not blend_data.armatures:
            return RunState.FINISH

        count = 20

        if self.armature_index >= len(blend_data.armatures):
            self.armature_index = 0

        start_armature_index = self.armature_index
        end_armature_index = min(self.armature_index + count, len(blend_data.armatures))
        changed = False
        for armature in blend_data.armatures[start_armature_index:end_armature_index]:
            ext = get_armature_extension(armature)
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
                changed = True
                break

        if changed:
            Vrm1LookAtPropertyGroup.update_all_previews(context)
            return RunState.FINISH

        self.armature_index += count

        if end_armature_index < len(blend_data.armatures):
            return RunState.PREEMPT

        return RunState.FINISH

    def create_fast_path_performance_test_objects(self, context: Context) -> None:
        blend_data = context.blend_data

        for i in range(300):
            if i % 3 != 0:
                mesh = blend_data.meshes.new(f"Mesh#{i}")
                blend_data.objects.new(f"Object#{i}", mesh)
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
