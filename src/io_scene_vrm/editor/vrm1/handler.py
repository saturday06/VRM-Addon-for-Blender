# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from dataclasses import dataclass

import bpy
from bpy.app.handlers import persistent
from bpy.types import Armature
from mathutils import Vector

from ...common import ops
from ...common.logger import get_logger
from ...common.micro_task import MicroTask, RunState, add_micro_task
from ..extension import get_armature_extension
from .property_group import Vrm1ExpressionPropertyGroup, Vrm1LookAtPropertyGroup

logger = get_logger(__name__)


@persistent
def frame_change_pre(_unused: object) -> None:
    Vrm1ExpressionPropertyGroup.frame_change_post_shape_key_updates.clear()


@persistent
def frame_change_post(_unused: object) -> None:
    context = bpy.context

    for (
        shape_key_name,
        key_block_name,
    ), value in Vrm1ExpressionPropertyGroup.frame_change_post_shape_key_updates.items():
        shape_key = context.blend_data.shape_keys.get(shape_key_name)
        if not shape_key:
            continue
        key_blocks = shape_key.key_blocks
        if not key_blocks:
            continue
        key_block = key_blocks.get(key_block_name)
        if not key_block:
            continue
        key_block.value = value
    Vrm1ExpressionPropertyGroup.frame_change_post_shape_key_updates.clear()

    # Update materials
    Vrm1ExpressionPropertyGroup.update_materials(context)


@dataclass
class LookAtPreviewUpdateTask(MicroTask):
    armature_index: int = 0

    def run(self) -> RunState:
        """Look Atの対象オブジェクトの更新を検知し、LookAtの状態を更新."""
        context = bpy.context
        blend_data = context.blend_data

        if not blend_data.armatures:
            return RunState.FINISH

        count = 20

        if self.armature_index >= len(blend_data.armatures):
            self.armature_index = 0

        start_armature_index = self.armature_index
        end_armature_index = min(self.armature_index + count, len(blend_data.armatures))
        armatures = blend_data.armatures[start_armature_index:end_armature_index]
        changed = any(
            True
            for ext in map(get_armature_extension, armatures)
            if ext.is_vrm1()
            and ext.vrm1.look_at.enable_preview
            and ext.vrm1.look_at.preview_target_bpy_object
            and (
                Vector(ext.vrm1.look_at.previous_preview_target_bpy_object_location)
                - ext.vrm1.look_at.preview_target_bpy_object.location
            ).length_squared
            > 0
        )

        if changed:
            Vrm1LookAtPropertyGroup.update_all_previews(context)
            return RunState.FINISH

        self.armature_index += count

        if end_armature_index < len(blend_data.armatures):
            return RunState.PREEMPT

        return RunState.FINISH

    def create_fast_path_performance_test_objects(self) -> None:
        context = bpy.context
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

    def reset_run_progress(self) -> None:
        self.armature_index = 0


@persistent
def depsgraph_update_pre(_unused: object) -> None:
    add_micro_task(LookAtPreviewUpdateTask)
