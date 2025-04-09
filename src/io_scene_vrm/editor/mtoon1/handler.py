# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import sys
from dataclasses import dataclass, field
from typing import Optional

import bpy
from bpy.app.handlers import persistent
from bpy.types import Mesh

from ...common.logger import get_logger
from ...common.micro_task import MicroTask, RunState, add_micro_task
from ..extension import get_material_extension
from . import migration
from .ops import VRM_OT_refresh_mtoon1_outline

logger = get_logger(__name__)

HAS_AUTO_SMOOTH = tuple(bpy.app.version) < (4, 1)


@dataclass
class ComparisonMaterial:
    name: str


@dataclass
class ComparisonObject:
    use_auto_smooth: Optional[bool] = None
    comparison_materials: list[Optional[ComparisonMaterial]] = field(
        default_factory=list
    )


@dataclass
class OutlineUpdateTask(MicroTask):
    comparison_objects: list[ComparisonObject] = field(default_factory=list)

    object_index: int = 0
    comparison_object_index: int = 0
    material_slot_index: int = 0

    def run(self) -> RunState:
        """オブジェクトへのマテリアルの割り当て変更を検知し、アウトラインを割り当て."""
        context = bpy.context
        blend_data = context.blend_data

        # この値がゼロになったらPREEMPTを返して処理を中断。
        # 変更を検知したら実質無限の値を設定して最後まで処理が進むようにする。
        preempt_countdown = 15

        changed = False

        if not blend_data.objects:
            return RunState.FINISH

        # オブジェクトの数が前回の状態よりも減っていてインデックス範囲を超える場合、
        # 先頭からやり直す
        if self.object_index >= len(blend_data.objects):
            self.object_index = 0

        # オブジェクトを走査して、比較用オブジェクトと差分がないかを調査
        for object_index in range(self.object_index, len(blend_data.objects)):
            self.object_index = object_index
            obj = blend_data.objects[object_index]

            preempt_countdown -= 1
            if preempt_countdown <= 0:
                return RunState.PREEMPT

            # メッシュオブジェクトのみが調査対象。
            # メッシュオブジェクトでない場合はスキップ
            obj_data = obj.data
            if not isinstance(obj_data, Mesh):
                continue
            mesh = obj_data

            # 比較用オブジェクトの数が足りない場合は、比較用オブジェクトを新規追加
            while self.comparison_object_index >= len(self.comparison_objects):
                self.comparison_objects.append(ComparisonObject())

            # 比較用オブジェクトを得る
            comparison_object = self.comparison_objects[self.comparison_object_index]

            # use_auto_smoothの比較
            if HAS_AUTO_SMOOTH and (
                (use_auto_smooth := comparison_object.use_auto_smooth) is None
                or (use_auto_smooth != mesh.use_auto_smooth)
            ):
                changed, preempt_countdown = True, sys.maxsize
                # 変更差分を解消
                comparison_object.use_auto_smooth = mesh.use_auto_smooth

            # MaterialSlotの数が前回の状態よりも減っていてインデックス範囲を超える場合、
            # 先頭からやり直す
            if self.material_slot_index >= len(obj.material_slots):
                self.material_slot_index = 0

            # MaterialSlotの数と比較用Materialの数を同一化
            while len(obj.material_slots) > len(comparison_object.comparison_materials):
                comparison_object.comparison_materials.append(None)
            while len(obj.material_slots) < len(comparison_object.comparison_materials):
                comparison_object.comparison_materials.pop()

            # MaterialSlotを走査して、比較用Materialと差分がないかを調査
            for material_slot_index in range(
                self.material_slot_index, len(obj.material_slots)
            ):
                self.material_slot_index = material_slot_index
                material_slot = obj.material_slots[material_slot_index]

                preempt_countdown -= 1
                if preempt_countdown <= 0:
                    return RunState.PREEMPT

                # 比較用オブジェクトの数が足りない場合は、比較用オブジェクトを新規追加
                while material_slot_index >= len(
                    comparison_object.comparison_materials
                ):
                    comparison_object.comparison_materials.append(None)
                comparison_material = comparison_object.comparison_materials[
                    material_slot_index
                ]

                # 差分チェック
                if (
                    (material_slot_material := material_slot.material)
                    and (
                        material := blend_data.materials.get(
                            material_slot_material.name
                        )
                    )
                    and get_material_extension(material).mtoon1.get_enabled_in_material(
                        material
                    )
                ):
                    if (
                        not comparison_material
                        or comparison_material.name != material.name
                    ):
                        # material slotのマテリアルのMToonが有効状態だが、
                        # 比較用オブジェクトが存在しないか、名前不一致の場合、変更検知
                        changed, preempt_countdown = True, sys.maxsize
                        # 変更差分を解消
                        comparison_object.comparison_materials[material_slot_index] = (
                            ComparisonMaterial(material.name)
                        )
                elif comparison_material is not None:
                    # material slotのマテリアルのMToonが無効状態だが、
                    # 比較用オブジェクトが有効状態の場合、変更検知
                    changed, preempt_countdown = True, sys.maxsize
                    # 変更差分を解消
                    comparison_object.comparison_materials[material_slot_index] = None

            # MaterialSlotの走査が完了したので、
            # 次の走査のインデックスを0に戻す。
            self.material_slot_index = 0

            # 次のオブジェクトの走査をする前に、
            # 次の比較用オブジェクトのインデックスを進める。
            self.comparison_object_index += 1

        # self.comparison_objectsの要素数が不必要なサイズになる場合があるため、
        # 十分なサイズまで縮小
        while len(self.comparison_objects) > self.comparison_object_index:
            self.comparison_objects.pop()

        if not changed:
            return RunState.FINISH

        VRM_OT_refresh_mtoon1_outline.refresh(bpy.context, create_modifier=False)
        return RunState.FINISH

    def create_fast_path_performance_test_objects(self) -> None:
        context = bpy.context
        blend_data = context.blend_data

        for i in range(100):
            blend_data.materials.new(f"Material#{i}")

        for i in range(100):
            mesh = blend_data.meshes.new(f"Mesh#{i}")
            blend_data.objects.new(f"Object#{i}", mesh)
            for k in range(50):
                material = blend_data.materials[(k * 3) % len(blend_data.materials)]
                mesh.materials.append(material)
                if k % 5 == 0:
                    get_material_extension(material).mtoon1.enabled = True

    def reset_run_progress(self) -> None:
        self.object_index = 0
        self.comparison_object_index = 0
        self.material_slot_index = 0


@persistent
def depsgraph_update_pre(_unused: object) -> None:
    if bpy.app.version < (3, 3):
        return
    add_micro_task(OutlineUpdateTask)


@persistent
def load_post(_unsed: object) -> None:
    migration.state.material_blender_4_2_warning_shown = False
