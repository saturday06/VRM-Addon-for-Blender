import secrets
import string
from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Optional, Union

import bpy
from bpy.types import Armature, Context, NodesModifier, Object
from mathutils import Quaternion

from ..common import shader
from ..common.deep import Json, make_json
from ..common.workspace import save_workspace
from ..editor.vrm0.property_group import Vrm0HumanoidPropertyGroup
from ..editor.vrm1.property_group import Vrm1HumanoidPropertyGroup
from ..external import io_scene_gltf2_support


class AbstractBaseVrmExporter(ABC):
    def __init__(
        self,
        context: Context,
    ) -> None:
        self.context = context
        self.export_id = "BlenderVrmAddonExport" + (
            "".join(secrets.choice(string.digits) for _ in range(10))
        )
        self.gltf2_addon_export_settings = (
            io_scene_gltf2_support.create_export_settings()
        )

    @abstractmethod
    def export_vrm(self) -> Optional[bytes]:
        pass

    @contextmanager
    def setup_pose(
        self,
        armature: Object,
        armature_data: Armature,
        humanoid: Union[Vrm0HumanoidPropertyGroup, Vrm1HumanoidPropertyGroup],
    ) -> Iterator[None]:
        pose = humanoid.pose
        action = humanoid.pose_library
        pose_marker_name = humanoid.pose_marker_name

        if pose != Vrm1HumanoidPropertyGroup.POSE_ITEM_VALUE_CUSTOM_POSE:
            action = None
            pose_marker_name = ""

        if (
            pose == Vrm1HumanoidPropertyGroup.POSE_ITEM_VALUE_CURRENT_POSE
            and armature_data.pose_position == "REST"
        ):
            yield
            return

        if pose == Vrm1HumanoidPropertyGroup.POSE_ITEM_VALUE_REST_POSITION_POSE or (
            pose == Vrm1HumanoidPropertyGroup.POSE_ITEM_VALUE_CUSTOM_POSE
            and not (action and action.name in self.context.blend_data.actions)
        ):
            saved_pose_position = armature_data.pose_position
            armature_data.pose_position = "REST"
            try:
                yield
            finally:
                armature_data.pose_position = saved_pose_position
            return

        with save_workspace(self.context, armature):
            bpy.ops.object.select_all(action="DESELECT")
            bpy.ops.object.mode_set(mode="POSE")

            saved_pose_position = armature_data.pose_position
            if armature_data.pose_position != "POSE":
                armature_data.pose_position = "POSE"

            self.context.view_layer.update()
            saved_current_pose_matrix_basis_dict = {
                bone.name: bone.matrix_basis.copy() for bone in armature.pose.bones
            }
            saved_current_pose_matrix_dict = {
                bone.name: bone.matrix.copy() for bone in armature.pose.bones
            }

            ext = armature_data.vrm_addon_extension
            saved_vrm1_look_at_preview = ext.vrm1.look_at.enable_preview
            if ext.is_vrm1() and ext.vrm1.look_at.enable_preview:
                # TODO: エクスポート時にここに到達する場合は事前に警告をすると親切
                ext.vrm1.look_at.enable_preview = False
                if ext.vrm1.look_at.type == ext.vrm1.look_at.TYPE_VALUE_BONE:
                    human_bones = ext.vrm1.humanoid.human_bones

                    left_eye_bone_name = human_bones.left_eye.node.bone_name
                    left_eye_bone = armature.pose.bones.get(left_eye_bone_name)
                    if left_eye_bone:
                        if left_eye_bone.rotation_mode != "QUATERNION":
                            left_eye_bone.rotation_mode = "QUATERNION"
                        left_eye_bone.rotation_quaternion = Quaternion()

                    right_eye_bone_name = human_bones.right_eye.node.bone_name
                    right_eye_bone = armature.pose.bones.get(right_eye_bone_name)
                    if right_eye_bone:
                        if right_eye_bone.rotation_mode != "QUATERNION":
                            right_eye_bone.rotation_mode = "QUATERNION"
                        right_eye_bone.rotation_quaternion = Quaternion()

            if action and action.name in self.context.blend_data.actions:
                pose_marker_frame = 0
                if pose_marker_name:
                    for search_pose_marker in action.pose_markers.values():
                        if search_pose_marker.name == pose_marker_name:
                            pose_marker_frame = search_pose_marker.frame
                            break
                armature.pose.apply_pose_from_action(
                    action, evaluation_time=pose_marker_frame
                )

        self.context.view_layer.update()

        try:
            yield
        finally:
            with save_workspace(self.context, armature):
                bpy.ops.object.select_all(action="DESELECT")
                bpy.ops.object.mode_set(mode="POSE")

                bones = [bone for bone in armature.pose.bones if not bone.parent]
                while bones:
                    bone = bones.pop()
                    matrix_basis = saved_current_pose_matrix_basis_dict.get(bone.name)
                    if matrix_basis is not None:
                        bone.matrix_basis = matrix_basis
                    bones.extend(bone.children)
                self.context.view_layer.update()

                bones = [bone for bone in armature.pose.bones if not bone.parent]
                while bones:
                    bone = bones.pop()
                    matrix = saved_current_pose_matrix_dict.get(bone.name)
                    if matrix is not None:
                        bone.matrix = matrix
                    bones.extend(bone.children)
                self.context.view_layer.update()

                armature_data.pose_position = saved_pose_position
                bpy.ops.object.mode_set(mode="OBJECT")

                ext = armature_data.vrm_addon_extension
                if (
                    ext.is_vrm1()
                    and ext.vrm1.look_at.enable_preview != saved_vrm1_look_at_preview
                ):
                    ext.vrm1.look_at.enable_preview = saved_vrm1_look_at_preview

    @contextmanager
    def clear_blend_shape_proxy_previews(
        self, armature_data: Armature
    ) -> Iterator[None]:
        ext = armature_data.vrm_addon_extension

        saved_vrm0_previews: list[float] = []
        for blend_shape_group in ext.vrm0.blend_shape_master.blend_shape_groups:
            saved_vrm0_previews.append(blend_shape_group.preview)
            blend_shape_group.preview = 0

        saved_vrm1_previews: dict[str, float] = {}
        for (
            name,
            expression,
        ) in ext.vrm1.expressions.all_name_to_expression_dict().items():
            saved_vrm1_previews[name] = expression.preview
            expression.preview = 0

        try:
            yield
        finally:
            for blend_shape_group, blend_shape_preview in zip(
                ext.vrm0.blend_shape_master.blend_shape_groups, saved_vrm0_previews
            ):
                blend_shape_group.preview = blend_shape_preview

            for (
                name,
                expression,
            ) in ext.vrm1.expressions.all_name_to_expression_dict().items():
                expression_preview = saved_vrm1_previews.get(name)
                if expression_preview is not None:
                    expression.preview = expression_preview

    @staticmethod
    def enter_hide_mtoon1_outline_geometry_nodes(
        context: Context,
    ) -> dict[str, list[tuple[str, bool, bool]]]:
        object_name_to_modifiers: dict[str, list[tuple[str, bool, bool]]] = {}
        for obj in context.blend_data.objects:
            for modifier in obj.modifiers:
                if not modifier.show_viewport:
                    continue
                if modifier.type != "NODES":
                    continue
                if not isinstance(modifier, NodesModifier):
                    continue
                node_group = modifier.node_group
                if (
                    not node_group
                    or node_group.name != shader.OUTLINE_GEOMETRY_GROUP_NAME
                ):
                    continue
                modifiers = object_name_to_modifiers.get(obj.name)
                if modifiers is None:
                    modifiers = []
                    object_name_to_modifiers[obj.name] = modifiers
                modifiers = object_name_to_modifiers[obj.name]
                modifiers.append(
                    (
                        modifier.name,
                        modifier.show_render,
                        modifier.show_viewport,
                    )
                )
                if modifier.show_render:
                    modifier.show_render = False
                if modifier.show_viewport:
                    modifier.show_viewport = False
        return object_name_to_modifiers

    @staticmethod
    def exit_hide_mtoon1_outline_geometry_nodes(
        context: Context,
        object_name_to_modifiers: dict[str, list[tuple[str, bool, bool]]],
    ) -> None:
        for object_name, modifiers in object_name_to_modifiers.items():
            for modifier_name, render, viewport in modifiers:
                obj = context.blend_data.objects.get(object_name)
                if not obj:
                    continue
                modifier = obj.modifiers.get(modifier_name)
                if (
                    not modifier
                    or modifier.type != "NODES"
                    or not isinstance(modifier, NodesModifier)
                ):
                    continue
                node_group = modifier.node_group
                if (
                    not node_group
                    or node_group.name != shader.OUTLINE_GEOMETRY_GROUP_NAME
                ):
                    continue
                if modifier.show_render != render:
                    modifier.show_render = render
                if modifier.show_viewport != viewport:
                    modifier.show_viewport = viewport

    @staticmethod
    @contextmanager
    def hide_mtoon1_outline_geometry_nodes(context: Context) -> Iterator[None]:
        object_name_to_modifier_names = (
            AbstractBaseVrmExporter.enter_hide_mtoon1_outline_geometry_nodes(context)
        )
        try:
            yield
        finally:
            AbstractBaseVrmExporter.exit_hide_mtoon1_outline_geometry_nodes(
                context, object_name_to_modifier_names
            )


def assign_dict(
    target: dict[str, Json],
    key: str,
    value: Union[Json, tuple[float, float, float], tuple[float, float, float, float]],
    default_value: Json = None,
) -> bool:
    if value is None or value == default_value:
        return False
    target[key] = make_json(value)
    return True
