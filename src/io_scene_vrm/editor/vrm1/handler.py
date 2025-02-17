# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import time
from typing import Optional

import bpy
from bpy.app.handlers import persistent
from mathutils import Vector

from ...common.logger import get_logger
from ..extension import get_armature_extension
from .property_group import Vrm1ExpressionPropertyGroup, Vrm1LookAtPropertyGroup

logger = get_logger(__name__)

# Import the SPRINGBONE_MODAL_RUNNING flag from the spring bone handler.
from ..spring_bone1.handler import SPRINGBONE_MODAL_RUNNING  # Adjusted relative import

# Global flag to indicate whether a full render is running.
RENDERING = False


@persistent
def frame_change_pre(_unused: object) -> None:
    # Do not clear the update queue here.
    pass


def update_expression_shape_keys() -> None:
    # If the spring bone modal operator is running, skip expression updates to avoid conflicts.
    if SPRINGBONE_MODAL_RUNNING:
        return
    logger.debug("Updating expression shape keys")
    # Iterate over a copy so that clearing doesn't interfere.
    for (shape_key_name, key_block_name), value in list(
        Vrm1ExpressionPropertyGroup.frame_change_post_shape_key_updates.items()
    ):
        # Optionally, you can use evaluated_get on the object that owns the shape key
        # if the shape key value is driven by animated properties.
        shape_key = bpy.data.shape_keys.get(shape_key_name)
        if not shape_key:
            continue
        key_blocks = shape_key.key_blocks
        if not key_blocks:
            continue
        key_block = key_blocks.get(key_block_name)
        if not key_block:
            continue
        key_block.value = value
        # Force the owning mesh to update so Blender recognizes the change.
        if shape_key.id_data:
            shape_key.id_data.update_tag()
    Vrm1ExpressionPropertyGroup.frame_change_post_shape_key_updates.clear()


@persistent
def frame_change_post(_unused: object) -> None:
    # Update materials immediately.
    Vrm1ExpressionPropertyGroup.update_materials(bpy.context)
    # In interactive playback (non-render mode), register a timer to update expression shape keys.
    if not RENDERING and not bpy.app.timers.is_registered(update_expression_shape_keys):
        bpy.app.timers.register(update_expression_shape_keys, first_interval=0.1)


def update_look_at_preview() -> Optional[float]:
    context = bpy.context
    compare_start_time = time.perf_counter()
    # ここは最適化の必要がある
    changed = any(
        True
        for ext in [
            get_armature_extension(armature)
            for armature in context.blend_data.armatures
        ]
        if ext.is_vrm1()
        and ext.vrm1.look_at.enable_preview
        and ext.vrm1.look_at.preview_target_bpy_object
        and (
            Vector(ext.vrm1.look_at.previous_preview_target_bpy_object_location)
            - ext.vrm1.look_at.preview_target_bpy_object.location
        ).length_squared
        > 0
    )
    compare_end_time = time.perf_counter()
    logger.debug(
        "The duration to determine look at preview updates is %.9f seconds",
        compare_end_time - compare_start_time,
    )
    if not changed:
        return None
    Vrm1LookAtPropertyGroup.update_all_previews(context)
    return None


@persistent
def save_pre(_unused: object) -> None:
    update_look_at_preview()


@persistent
def depsgraph_update_pre(_unused: object) -> None:
    # No action needed here for now.
    pass


@persistent
def depsgraph_update_post_expr(depsgraph) -> None:
    # This handler runs after all dependency graph updates.
    # In render mode, force expression updates here.
    if RENDERING:
        update_expression_shape_keys()


@persistent
def render_pre(_unused: object) -> None:
    global RENDERING
    RENDERING = True
    # During a full render, update expression shape keys before each frame is rendered.
    update_expression_shape_keys()
    Vrm1ExpressionPropertyGroup.frame_change_post_shape_key_updates.clear()
    # Force a viewport redraw.
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()
    # Force re-evaluation by toggling a dummy property on the scene.
    scene = bpy.context.scene
    scene["dummy_update"] = not scene.get("dummy_update", False)
    bpy.context.view_layer.update()
    # Workaround: setting the frame twice forces depsgraph evaluation.
    current_frame = scene.frame_current
    scene.frame_set(current_frame)
    scene.frame_set(current_frame)


@persistent
def render_post(_unused: object) -> None:
    global RENDERING
    RENDERING = True
    # During a full render, update expression shape keys after each frame is rendered.
    update_expression_shape_keys()
    Vrm1ExpressionPropertyGroup.frame_change_post_shape_key_updates.clear()
    # Force a viewport redraw.
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()
    # Force re-evaluation by toggling a dummy property on the scene.
    scene = bpy.context.scene
    scene["dummy_update"] = not scene.get("dummy_update", False)
    bpy.context.view_layer.update()
    # Workaround: setting the frame twice forces depsgraph evaluation.
    current_frame = scene.frame_current
    scene.frame_set(current_frame)
    scene.frame_set(current_frame)


@persistent
def render_complete(_unused: object) -> None:
    global RENDERING
    RENDERING = False
    # After render, force a final update and clear any pending updates.
    update_expression_shape_keys()
    Vrm1ExpressionPropertyGroup.frame_change_post_shape_key_updates.clear()
    # Force a viewport redraw.
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()
    # Reinitialize the scene update by resetting the current frame twice.
    scene = bpy.context.scene
    current_frame = scene.frame_current
    scene.frame_set(current_frame)
    scene.frame_set(current_frame)


@persistent
def render_cancel(_unused: object) -> None:
    global RENDERING
    RENDERING = False
    update_expression_shape_keys()
    Vrm1ExpressionPropertyGroup.frame_change_post_shape_key_updates.clear()
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()
    # Reinitialize the scene update by resetting the current frame twice.
    scene = bpy.context.scene
    current_frame = scene.frame_current
    scene.frame_set(current_frame)
    scene.frame_set(current_frame)
