# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from __future__ import annotations

from typing import Any, Final, cast

import bpy
from bpy.app.handlers import persistent
from bpy.types import Scene

from ..common import animation
from ..common.logger import get_logger
from ..common.preferences import is_development_mode_enabled
from . import render_bake

logger = get_logger(__name__)


_TEMP_RENDER_LAYERS_NODE_KEY: Final[str] = "vrm_addon_temp_render_layers"
_temp_render_layers_scene_pointers: Final[set[int]] = set()


def _ensure_render_layers_node(scene: Scene) -> None:
    if not scene.use_nodes:
        return
    node_tree = scene.node_tree
    if not node_tree:
        return

    for node in node_tree.nodes:
        if node.type == "R_LAYERS":
            return

    render_layers_node = node_tree.nodes.new("CompositorNodeRLayers")
    cast("Any", render_layers_node)[_TEMP_RENDER_LAYERS_NODE_KEY] = True
    _temp_render_layers_scene_pointers.add(scene.as_pointer())
    logger.info("Added temporary Render Layers node to ensure render handlers run.")


def _remove_temp_render_layers_node(scene: Scene) -> None:
    if scene.as_pointer() not in _temp_render_layers_scene_pointers:
        return
    node_tree = scene.node_tree
    if not node_tree:
        _temp_render_layers_scene_pointers.discard(scene.as_pointer())
        return

    for node in list(node_tree.nodes):
        if cast("Any", node).get(_TEMP_RENDER_LAYERS_NODE_KEY):
            node_tree.nodes.remove(node)
            break

    _temp_render_layers_scene_pointers.discard(scene.as_pointer())


@persistent
def render_init(scene: Scene) -> None:
    if not is_development_mode_enabled(bpy.context):
        return

    logger.info(
        "Render init: frame=%s use_nodes=%s",
        scene.frame_current,
        scene.use_nodes,
    )
    animation.state.during_animation_playback = False
    render_bake.state.render_active = True
    _ensure_render_layers_node(scene)
    _ensure_render_restore_timer()
    if not render_bake.state.active:
        logger.info("Auto-bake VRM expressions before render")
        if not render_bake.bake_for_render(bpy.context):
            logger.error("Auto-bake failed; render may not include expressions")


@persistent
def render_complete(scene: Scene) -> None:
    if not is_development_mode_enabled(bpy.context):
        return

    logger.info("Render complete: frame=%s", scene.frame_current)
    animation.state.during_animation_playback = False
    _remove_temp_render_layers_node(scene)
    if render_bake.state.restore_pending:
        render_bake.restore_after_render(bpy.context)
    render_bake.state.render_active = False


@persistent
def render_cancel(scene: Scene) -> None:
    if not is_development_mode_enabled(bpy.context):
        return

    logger.info("Render cancel: frame=%s", scene.frame_current)
    animation.state.during_animation_playback = False
    _remove_temp_render_layers_node(scene)
    if render_bake.state.restore_pending:
        render_bake.restore_after_render(bpy.context)
    render_bake.state.render_active = False


def _ensure_render_restore_timer() -> None:
    if bpy.app.timers.is_registered(_render_restore_timer):
        return
    bpy.app.timers.register(_render_restore_timer, first_interval=1.0)


def _render_restore_timer() -> float | None:
    if render_bake.state.restore_pending:
        if not bpy.app.is_job_running("RENDER"):
            render_bake.restore_after_render(bpy.context)
            return None
        return 1.0
    if render_bake.state.render_active and not bpy.app.is_job_running("RENDER"):
        render_bake.state.render_active = False
    return None
