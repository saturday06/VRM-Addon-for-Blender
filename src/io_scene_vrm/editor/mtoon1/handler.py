# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import time
from dataclasses import dataclass, field
from typing import Optional

import bpy
from bpy.app.handlers import persistent
from bpy.types import Mesh, ShaderNodeGroup, ShaderNodeOutputMaterial

from ...common import ops
from ...common.logging import get_logger
from ..extension import get_material_extension
from . import migration
from .ops import VRM_OT_refresh_mtoon1_outline

logger = get_logger(__name__)


@dataclass
class OutlineUpdateState:
    object_state: list[tuple[bool, list[Optional[str]]]] = field(default_factory=list)
    material_state: list[bool] = field(default_factory=list)


outline_update_state = OutlineUpdateState()


def update_mtoon1_outline() -> Optional[float]:
    context = bpy.context

    compare_start_time = time.perf_counter()

    # Optimize appropriately.
    has_auto_smooth = tuple(bpy.app.version) < (4, 1)
    object_state = [
        (
            has_auto_smooth and obj.data.use_auto_smooth,
            [
                material_ref.name if (material_ref := material_slot.material) else None
                for material_slot in obj.material_slots
            ],
        )
        for obj in context.blend_data.objects
        if isinstance(obj.data, Mesh)
    ]
    material_state = [
        get_material_extension(material).mtoon1.get_enabled_in_material(material)
        for material in [
            context.blend_data.materials.get(material_name)
            for material_name in {
                material_name
                for _, material_names in object_state
                for material_name in material_names
                if material_name is not None
            }
        ]
        if material is not None
    ]

    not_changed = (
        outline_update_state.object_state,
        outline_update_state.material_state,
    ) == (object_state, material_state)

    compare_end_time = time.perf_counter()

    logger.debug(
        "The duration to determine material updates is %.9f seconds",
        compare_end_time - compare_start_time,
    )

    if not_changed:
        return None

    outline_update_state.object_state = object_state
    outline_update_state.material_state = material_state

    VRM_OT_refresh_mtoon1_outline.refresh(bpy.context, create_modifier=False)
    return None


def trigger_update_mtoon1_outline() -> None:
    if bpy.app.version < (3, 3):
        return
    if bpy.app.timers.is_registered(update_mtoon1_outline):
        return
    bpy.app.timers.register(update_mtoon1_outline, first_interval=0.2)


@dataclass
class WatchAutoSetupMtoon1ShaderContinuation:
    last_material_index: int = 0
    last_node_index: int = 0


watch_auto_setup_mtoon1_shader_continuation = WatchAutoSetupMtoon1ShaderContinuation()


def watch_auto_setup_mtoon1_shader() -> Optional[float]:
    """MToon自動セットアップノードグループの出現を監視し、発見したら自動セットアップを行う.

    この関数は高頻度で呼ばれるので、処理は軽量にし、IOやGC Allocationを最小にするように
    気を付ける。
    """
    context = bpy.context
    interval_seconds = 0.5
    # この値が0以下になったら処理を中断して、次のインターバルで再開する。
    search_tick = 50

    materials = context.blend_data.materials

    # マテリアルの検索開始位置を前回の状態から復元する。
    end_material_index = len(materials)
    start_material_index = (
        watch_auto_setup_mtoon1_shader_continuation.last_material_index
    )
    if start_material_index >= end_material_index:
        start_material_index = 0

    for material_index in range(start_material_index, end_material_index):
        watch_auto_setup_mtoon1_shader_continuation.last_material_index = material_index

        if search_tick <= 0:
            return interval_seconds
        search_tick -= 1

        material = materials[material_index]
        if not material.use_nodes:
            continue
        node_tree = material.node_tree
        if node_tree is None:
            continue

        nodes = node_tree.nodes

        # ノードの検索開始位置を前回の状態から復元する。
        end_node_index = len(nodes)
        start_node_index = watch_auto_setup_mtoon1_shader_continuation.last_node_index
        if start_node_index >= end_node_index:
            start_node_index = 0

        for node_index in range(start_node_index, end_node_index):
            watch_auto_setup_mtoon1_shader_continuation.last_node_index = node_index

            if search_tick <= 0:
                return interval_seconds
            search_tick -= 1

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
                    search_tick -= 1
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
        watch_auto_setup_mtoon1_shader_continuation.last_node_index = 0
    watch_auto_setup_mtoon1_shader_continuation.last_material_index = 0

    return interval_seconds


def trigger_watch_auto_setup_mtoon1_shader() -> None:
    if bpy.app.timers.is_registered(watch_auto_setup_mtoon1_shader):
        return
    bpy.app.timers.register(watch_auto_setup_mtoon1_shader, first_interval=0.5)


@persistent
def save_pre(_unused: object) -> None:
    update_mtoon1_outline()


@persistent
def depsgraph_update_pre(_unused: object) -> None:
    trigger_update_mtoon1_outline()


@persistent
def load_post(_unsed: object) -> None:
    migration.state.material_blender_4_2_warning_shown = False
