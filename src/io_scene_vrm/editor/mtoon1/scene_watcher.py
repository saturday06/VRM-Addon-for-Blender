# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import sys
from dataclasses import dataclass, field
from typing import Optional

import bpy
from bpy.types import Context, Mesh, ShaderNodeGroup, ShaderNodeOutputMaterial

from ...common import ops
from ...common.logger import get_logger
from ...common.scene_watcher import RunState, SceneWatcher
from ..extension import get_material_extension
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
        default_factory=list[Optional[ComparisonMaterial]]
    )


@dataclass
class OutlineUpdater(SceneWatcher):
    comparison_objects: list[ComparisonObject] = field(
        default_factory=list[ComparisonObject]
    )

    object_index: int = 0
    comparison_object_index: int = 0
    material_slot_index: int = 0

    def reset_run_progress(self) -> None:
        self.object_index = 0
        self.comparison_object_index = 0
        self.material_slot_index = 0

    def run(self, context: Context) -> RunState:
        """オブジェクトへのマテリアルの割り当て変更を検知し、アウトラインを割り当て."""
        blend_data = context.blend_data

        # この値がゼロになったらPREEMPTを返して処理を中断。
        # 変更を検知したら実質無限の値を設定して最後まで処理が進むようにする。
        preempt_countdown = 15

        changed = False

        create_modifier = False

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
                        # オブジェクトにMToon有効状態のマテリアルが新たに割り当てられた
                        # ので、アウトラインのモディファイアが必要な場合新規作成する。
                        # 本来はオブジェクトとマテリアルのペアごとにTrue/Falseを
                        # 設定するべきだが、現状は、実用上固定で問題ないと思う。
                        create_modifier = True
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

        VRM_OT_refresh_mtoon1_outline.refresh(context, create_modifier=create_modifier)
        return RunState.FINISH

    def create_fast_path_performance_test_objects(self, context: Context) -> None:
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


@dataclass
class MToon1AutoSetup(SceneWatcher):
    last_material_index: int = 0
    last_node_index: int = 0

    def reset_run_progress(self) -> None:
        self.last_material_index: int = 0
        self.last_node_index: int = 0

    def run(self, context: Context) -> RunState:
        """MToon自動セットアップノードグループの出現を監視し、発見したら自動でセットアップ.

        この関数は高頻度で呼ばれるので、処理は軽量にし、IOやGC Allocationを
        最小にするように気を付ける。
        """
        # この値が0以下になったら処理を中断
        search_preempt_countdown = 100

        materials = context.blend_data.materials

        # マテリアルの巡回開始位置を前回中断した状態から復元する。
        end_material_index = len(materials)
        start_material_index = self.last_material_index
        if start_material_index >= end_material_index:
            self.last_material_index = 0
            self.last_node_index = 0
            start_material_index = 0

        # マテリアルを巡回し、MToonを有効化する必要がある場合は有効化する。
        for material_index in range(start_material_index, end_material_index):
            self.last_material_index = material_index

            search_preempt_countdown -= 1
            if search_preempt_countdown <= 0:
                return RunState.PREEMPT

            material = materials[material_index]
            if not material.use_nodes:
                continue
            node_tree = material.node_tree
            if node_tree is None:
                continue

            nodes = node_tree.nodes

            # ノードの巡回開始位置を前回中断した状態から復元する。
            end_node_index = len(nodes)
            start_node_index = self.last_node_index
            if start_node_index >= end_node_index:
                start_node_index = 0

            # ノードを巡回し、MToonのプレースホルダのノードがShaderNodeOutputMaterialに
            # 接続されていたらマテリアルをMToonに変換する。
            for node_index in range(start_node_index, end_node_index):
                self.last_node_index = node_index

                search_preempt_countdown -= 1
                if search_preempt_countdown <= 0:
                    return RunState.PREEMPT

                node = nodes[node_index]
                if not isinstance(node, ShaderNodeGroup):
                    continue

                group_node_tree = node.node_tree
                if group_node_tree is None:
                    continue

                if not group_node_tree.get("VRM Add-on MToon1 Auto Setup Placeholder"):
                    continue

                found = False
                for output in node.outputs:
                    for link in output.links:
                        if isinstance(link.to_node, ShaderNodeOutputMaterial):
                            found = True
                            break
                    if found:
                        break
                if not found:
                    continue

                mtoon1 = get_material_extension(material).mtoon1
                if mtoon1.enabled:
                    ops.vrm.reset_mtoon1_material_shader_node_group(
                        material_name=material.name
                    )
                else:
                    mtoon1.enabled = True
                break
            self.last_node_index = 0
        self.last_material_index = 0

        return RunState.FINISH

    def create_fast_path_performance_test_objects(self, context: Context) -> None:
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
