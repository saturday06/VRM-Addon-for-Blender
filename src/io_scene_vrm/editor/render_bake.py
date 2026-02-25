# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from __future__ import annotations

from dataclasses import dataclass, field

import bpy
from bpy.types import Action, Armature, Context

from ..common import animation
from ..common.logger import get_logger
from .extension import get_armature_extension
from .vrm0.property_group import (
    Vrm0BlendShapeGroupPropertyGroup,
    get_armature_vrm0_extension,
)
from .vrm1.property_group import (
    Vrm1ExpressionPropertyGroup,
    get_armature_vrm1_extension,
)

logger = get_logger(__name__)


@dataclass
class _ActionState:
    had_animation_data: bool
    action: Action | None


@dataclass
class _BakeState:
    active: bool = False
    restore_pending: bool = False
    render_active: bool = False
    original_frame: int = 0
    armature_action_state: dict[int, _ActionState] = field(default_factory=dict)
    shapekey_action_state: dict[int, _ActionState] = field(default_factory=dict)
    armature_temp_action: dict[int, Action] = field(default_factory=dict)
    shapekey_temp_action: dict[int, Action] = field(default_factory=dict)
    preview_values: dict[int, dict[str, float]] = field(default_factory=dict)
    temp_actions: list[Action] = field(default_factory=list)


state = _BakeState()


def bake_for_render(context: Context) -> bool:
    if state.active:
        logger.warning("Bake already active")
        return False

    logger.info(
        "Bake start: frames %s-%s step=%s",
        context.scene.frame_start,
        context.scene.frame_end,
        context.scene.frame_step,
    )

    state.active = True
    state.restore_pending = True
    state.original_frame = context.scene.frame_current
    state.armature_action_state.clear()
    state.shapekey_action_state.clear()
    state.armature_temp_action.clear()
    state.shapekey_temp_action.clear()
    state.preview_values.clear()
    state.temp_actions.clear()

    animation.state.during_animation_playback = False

    try:
        _prepare_actions_for_bake(context)
        bake_summary = _bake_frames(context)
        _activate_baked_actions(context)
        context.scene.frame_set(state.original_frame)
        logger.info(
            "Bake summary: vrm1_nonzero=%s vrm1_meshes=%s "
            "vrm0_nonzero=%s vrm0_meshes=%s",
            bake_summary["vrm1_nonzero"],
            bake_summary["vrm1_meshes"],
            bake_summary["vrm0_nonzero"],
            bake_summary["vrm0_meshes"],
        )
        logger.info(
            "Bake completed: frames %s-%s",
            context.scene.frame_start,
            context.scene.frame_end,
        )
    except Exception:
        logger.exception("Bake failed")
        restore_after_render(context)
        return False
    else:
        return True


def restore_after_render(context: Context) -> None:
    if not state.active:
        return

    try:
        for armature_data in context.blend_data.armatures:
            pointer = armature_data.as_pointer()
            action_state = state.armature_action_state.get(pointer)
            if action_state is None:
                continue

            if action_state.had_animation_data:
                armature_data.animation_data.action = action_state.action
            else:
                armature_data.animation_data_clear()

            preview_values = state.preview_values.get(pointer)
            if preview_values:
                expressions = get_armature_vrm1_extension(armature_data).expressions
                for expression in expressions.all_name_to_expression_dict().values():
                    data_path = expression.path_from_id("preview")
                    value = preview_values.get(data_path)
                    if value is None:
                        continue
                    expression["preview"] = value

        for mesh in context.blend_data.meshes:
            shape_keys = mesh.shape_keys
            if not shape_keys:
                continue
            pointer = shape_keys.as_pointer()
            action_state = state.shapekey_action_state.get(pointer)
            if action_state is None:
                continue

            if action_state.had_animation_data:
                shape_keys.animation_data.action = action_state.action
            else:
                shape_keys.animation_data_clear()

        for action in list(state.temp_actions):
            if action.users == 0:
                bpy.data.actions.remove(action)

        context.scene.frame_set(state.original_frame)
        logger.info("Bake restore completed")
    finally:
        state.active = False
        state.restore_pending = False
        state.render_active = False
        state.armature_action_state.clear()
        state.shapekey_action_state.clear()
        state.armature_temp_action.clear()
        state.shapekey_temp_action.clear()
        state.preview_values.clear()
        state.temp_actions.clear()


def _prepare_actions_for_bake(context: Context) -> None:
    for armature_data in context.blend_data.armatures:
        ext = get_armature_extension(armature_data)
        if not (ext.is_vrm0() or ext.is_vrm1()):
            continue

        animation_data = armature_data.animation_data
        had_animation_data = animation_data is not None
        if not animation_data:
            animation_data = armature_data.animation_data_create()
        state.armature_action_state[armature_data.as_pointer()] = _ActionState(
            had_animation_data=had_animation_data,
            action=animation_data.action,
        )

        action = bpy.data.actions.new(f"VRM_Bake_Armature_{armature_data.name}")
        state.temp_actions.append(action)
        state.armature_temp_action[armature_data.as_pointer()] = action

        if ext.is_vrm1():
            expressions = get_armature_vrm1_extension(armature_data).expressions
            preview_values: dict[str, float] = {}
            for expression in expressions.all_name_to_expression_dict().values():
                data_path = expression.path_from_id("preview")
                preview_values[data_path] = float(expression.preview)
            state.preview_values[armature_data.as_pointer()] = preview_values

    for mesh in context.blend_data.meshes:
        shape_keys = mesh.shape_keys
        if not shape_keys:
            continue

        if not _mesh_has_vrm_binds(context, mesh.name):
            continue

        animation_data = shape_keys.animation_data
        had_animation_data = animation_data is not None
        if not animation_data:
            animation_data = shape_keys.animation_data_create()
        state.shapekey_action_state[shape_keys.as_pointer()] = _ActionState(
            had_animation_data=had_animation_data,
            action=animation_data.action,
        )

        action = bpy.data.actions.new(f"VRM_Bake_ShapeKeys_{mesh.name}")
        state.temp_actions.append(action)
        state.shapekey_temp_action[shape_keys.as_pointer()] = action


def _mesh_has_vrm_binds(context: Context, mesh_data_name: str) -> bool:
    for armature_data in context.blend_data.armatures:
        ext = get_armature_extension(armature_data)
        if ext.is_vrm1():
            expressions = get_armature_vrm1_extension(armature_data).expressions
            for expression in expressions.all_name_to_expression_dict().values():
                for bind in expression.morph_target_binds:
                    mesh_object = context.blend_data.objects.get(
                        bind.node.mesh_object_name
                    )
                    if not mesh_object:
                        continue
                    if getattr(mesh_object, "data", None) is None:
                        continue
                    if getattr(mesh_object.data, "name", None) == mesh_data_name:
                        return True
        if ext.is_vrm0():
            blend_shape_groups = get_armature_vrm0_extension(
                armature_data
            ).blend_shape_master.blend_shape_groups
            for blend_shape_group in blend_shape_groups:
                for bind in blend_shape_group.binds:
                    mesh_object = context.blend_data.objects.get(
                        bind.mesh.mesh_object_name
                    )
                    if not mesh_object:
                        continue
                    if getattr(mesh_object, "data", None) is None:
                        continue
                    if getattr(mesh_object.data, "name", None) == mesh_data_name:
                        return True
    return False


def _bake_frames(context: Context) -> dict[str, int]:
    scene = context.scene
    frame_start = scene.frame_start
    frame_end = scene.frame_end
    frame_step = max(1, scene.frame_step)
    summary = {
        "vrm1_nonzero": 0,
        "vrm1_meshes": 0,
        "vrm0_nonzero": 0,
        "vrm0_meshes": 0,
    }

    for frame in range(frame_start, frame_end + 1, frame_step):
        scene.frame_set(frame)
        context.view_layer.update()
        depsgraph = context.evaluated_depsgraph_get()
        evaluated_armatures_by_name = _get_evaluated_armature_data_by_name(
            context, depsgraph
        )

        vrm1_nonzero, vrm1_meshes = _bake_vrm1_frame(
            context, evaluated_armatures_by_name, frame
        )
        vrm0_nonzero, vrm0_meshes = _bake_vrm0_frame(
            context, evaluated_armatures_by_name, frame
        )
        summary["vrm1_nonzero"] += vrm1_nonzero
        summary["vrm1_meshes"] += vrm1_meshes
        summary["vrm0_nonzero"] += vrm0_nonzero
        summary["vrm0_meshes"] += vrm0_meshes
    return summary


def _bake_vrm1_frame(
    context: Context,
    evaluated_armatures_by_name: dict[str, Armature],
    frame: int,
) -> tuple[int, int]:
    total_nonzero = 0
    total_meshes = 0
    for armature_data in context.blend_data.armatures:
        ext = get_armature_extension(armature_data)
        if not ext.is_vrm1():
            continue

        evaluated_armature_data = evaluated_armatures_by_name.get(armature_data.name)
        if not evaluated_armature_data:
            evaluated_armature_data = armature_data

        expressions = get_armature_vrm1_extension(armature_data).expressions
        evaluated_expressions = get_armature_vrm1_extension(
            evaluated_armature_data
        ).expressions

        name_to_expression = expressions.all_name_to_expression_dict()
        evaluated_name_to_expression = (
            evaluated_expressions.all_name_to_expression_dict()
        )

        nonzero_previews = 0
        for name, expression in name_to_expression.items():
            evaluated_expression = evaluated_name_to_expression.get(name, expression)
            value = float(evaluated_expression.preview)
            if value != 0.0:
                nonzero_previews += 1
            expression["preview"] = value
            _insert_keyframe(
                state.armature_temp_action.get(armature_data.as_pointer()),
                expression.path_from_id("preview"),
                0,
                frame,
                value,
            )

        values_by_mesh = Vrm1ExpressionPropertyGroup.collect_shapekey_values(
            context, expressions, evaluated_expressions
        )
        total_nonzero += nonzero_previews
        total_meshes += len(values_by_mesh)
        if logger.isEnabledFor(10):  # DEBUG
            logger.debug(
                "Bake VRM1 frame=%s armature=%s preview_nonzero=%s meshes=%s",
                frame,
                armature_data.name,
                nonzero_previews,
                len(values_by_mesh),
            )
        _apply_shapekey_values_and_keyframe(context, values_by_mesh, frame)
    return total_nonzero, total_meshes


def _bake_vrm0_frame(
    context: Context,
    evaluated_armatures_by_name: dict[str, Armature],
    frame: int,
) -> tuple[int, int]:
    total_nonzero = 0
    total_meshes = 0
    for armature_data in context.blend_data.armatures:
        ext = get_armature_extension(armature_data)
        if not ext.is_vrm0():
            continue

        evaluated_armature_data = evaluated_armatures_by_name.get(armature_data.name)
        if not evaluated_armature_data:
            evaluated_armature_data = armature_data

        blend_shape_groups = get_armature_vrm0_extension(
            armature_data
        ).blend_shape_master.blend_shape_groups
        evaluated_blend_shape_groups = get_armature_vrm0_extension(
            evaluated_armature_data
        ).blend_shape_master.blend_shape_groups

        nonzero_previews = 0
        for index, blend_shape_group in enumerate(blend_shape_groups):
            if index >= len(evaluated_blend_shape_groups):
                evaluated_blend_shape_group = blend_shape_group
            else:
                evaluated_blend_shape_group = evaluated_blend_shape_groups[index]

            preview_value = float(evaluated_blend_shape_group.preview)
            if preview_value != 0.0:
                nonzero_previews += 1
            blend_shape_group["preview"] = preview_value
            _insert_keyframe(
                state.armature_temp_action.get(armature_data.as_pointer()),
                blend_shape_group.path_from_id("preview"),
                0,
                frame,
                preview_value,
            )

        values_by_mesh = Vrm0BlendShapeGroupPropertyGroup.collect_shapekey_values(
            context, blend_shape_groups, evaluated_blend_shape_groups
        )
        total_nonzero += nonzero_previews
        total_meshes += len(values_by_mesh)
        if logger.isEnabledFor(10):  # DEBUG
            logger.debug(
                "Bake VRM0 frame=%s armature=%s preview_nonzero=%s meshes=%s",
                frame,
                armature_data.name,
                nonzero_previews,
                len(values_by_mesh),
            )
        _apply_shapekey_values_and_keyframe(context, values_by_mesh, frame)
    return total_nonzero, total_meshes


def _apply_shapekey_values_and_keyframe(
    context: Context,
    values_by_mesh: dict[str, dict[str, float]],
    frame: int,
) -> None:
    for mesh_data_name, key_block_name_to_value in values_by_mesh.items():
        mesh_data = context.blend_data.meshes.get(mesh_data_name)
        if not mesh_data:
            continue
        shape_keys = mesh_data.shape_keys
        if not shape_keys:
            continue
        key_blocks = shape_keys.key_blocks
        if not key_blocks:
            continue

        for key_block_name, value in key_block_name_to_value.items():
            key_block = key_blocks.get(key_block_name)
            if not key_block:
                continue
            key_block.value = value
            _insert_keyframe(
                state.shapekey_temp_action.get(shape_keys.as_pointer()),
                key_block.path_from_id("value"),
                0,
                frame,
                value,
            )


def _get_evaluated_armature_data_by_name(
    context: Context, depsgraph: bpy.types.Depsgraph
) -> dict[str, Armature]:
    evaluated_armatures_by_name: dict[str, Armature] = {}
    for obj in context.view_layer.objects:
        if obj.type != "ARMATURE":
            continue
        evaluated_obj = obj.evaluated_get(depsgraph)
        evaluated_data = evaluated_obj.data
        if isinstance(evaluated_data, Armature):
            evaluated_armatures_by_name[obj.data.name] = evaluated_data
    return evaluated_armatures_by_name


def _activate_baked_actions(context: Context) -> None:
    for armature_data in context.blend_data.armatures:
        action = state.armature_temp_action.get(armature_data.as_pointer())
        if not action:
            continue
        animation_data = armature_data.animation_data
        if not animation_data:
            animation_data = armature_data.animation_data_create()
        animation_data.action = action

    for mesh in context.blend_data.meshes:
        shape_keys = mesh.shape_keys
        if not shape_keys:
            continue
        action = state.shapekey_temp_action.get(shape_keys.as_pointer())
        if not action:
            continue
        animation_data = shape_keys.animation_data
        if not animation_data:
            animation_data = shape_keys.animation_data_create()
        animation_data.action = action


def _insert_keyframe(
    action: Action | None,
    data_path: str,
    index: int,
    frame: int,
    value: float,
) -> None:
    if not action:
        return
    fcurve = action.fcurves.find(data_path, index=index)
    if fcurve is None:
        fcurve = action.fcurves.new(data_path=data_path, index=index)
    keyframe = fcurve.keyframe_points.insert(frame, value, options={"FAST"})
    keyframe.interpolation = "LINEAR"
