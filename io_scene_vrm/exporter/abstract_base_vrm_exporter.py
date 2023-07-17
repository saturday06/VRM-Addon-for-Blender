import secrets
import string
from abc import ABC, abstractmethod
from typing import Optional, Union

import bpy
from mathutils import Matrix

from ..common import shader
from ..common.deep import Json, make_json
from ..external import io_scene_gltf2_support


class AbstractBaseVrmExporter(ABC):
    def __init__(
        self,
        context: bpy.types.Context,
    ) -> None:
        self.context = context
        self.saved_current_pose_matrix_basis_dict: dict[str, Matrix] = {}
        self.saved_current_pose_matrix_dict: dict[str, Matrix] = {}
        self.saved_pose_position: Optional[str] = None
        self.export_id = "BlenderVrmAddonExport" + (
            "".join(secrets.choice(string.digits) for _ in range(10))
        )
        self.gltf2_addon_export_settings = (
            io_scene_gltf2_support.create_export_settings()
        )

    @abstractmethod
    def export_vrm(self) -> Optional[bytes]:
        pass

    def setup_pose(
        self,
        armature: bpy.types.Object,
        action: Optional[bpy.types.Action],
        pose_marker_name: str,
    ) -> None:
        if not action or action.name not in bpy.data.actions:
            return

        if self.context.view_layer.objects.active is not None:
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        self.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode="POSE")

        self.saved_pose_position = armature.data.pose_position
        armature.data.pose_position = "POSE"

        pose_marker_frame = 0
        if pose_marker_name:
            for search_pose_marker in action.pose_markers.values():
                if search_pose_marker.name == pose_marker_name:
                    pose_marker_frame = search_pose_marker.frame
                    break

        bpy.context.view_layer.update()
        self.saved_current_pose_matrix_basis_dict = {
            bone.name: bone.matrix_basis.copy() for bone in armature.pose.bones
        }
        self.saved_current_pose_matrix_dict = {
            bone.name: bone.matrix.copy() for bone in armature.pose.bones
        }

        armature.pose.apply_pose_from_action(action, evaluation_time=pose_marker_frame)
        bpy.context.view_layer.update()

    def restore_pose(self, armature: bpy.types.Object) -> None:
        if self.context.view_layer.objects.active is not None:
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        self.context.view_layer.objects.active = armature
        bpy.context.view_layer.update()
        bpy.ops.object.mode_set(mode="POSE")

        bones = [bone for bone in armature.pose.bones if not bone.parent]
        while bones:
            bone = bones.pop()
            matrix_basis = self.saved_current_pose_matrix_basis_dict.get(bone.name)
            if matrix_basis is not None:
                bone.matrix_basis = matrix_basis
            bones.extend(bone.children)
        bpy.context.view_layer.update()

        bones = [bone for bone in armature.pose.bones if not bone.parent]
        while bones:
            bone = bones.pop()
            matrix = self.saved_current_pose_matrix_dict.get(bone.name)
            if matrix is not None:
                bone.matrix = matrix
            bones.extend(bone.children)
        bpy.context.view_layer.update()

        if self.saved_pose_position:
            armature.data.pose_position = self.saved_pose_position
        bpy.ops.object.mode_set(mode="OBJECT")

    def clear_blend_shape_proxy_previews(
        self, armature: bpy.types.Object
    ) -> list[float]:
        ext = armature.data.vrm_addon_extension
        saved_previews = []
        for blend_shape_group in ext.vrm0.blend_shape_master.blend_shape_groups:
            saved_previews.append(blend_shape_group.preview)
            blend_shape_group.preview = 0
        return saved_previews

    def restore_blend_shape_proxy_previews(
        self, armature: bpy.types.Object, previews: list[float]
    ) -> None:
        ext = armature.data.vrm_addon_extension
        for blend_shape_group, blend_shape_preview in zip(
            ext.vrm0.blend_shape_master.blend_shape_groups, previews
        ):
            blend_shape_group.preview = blend_shape_preview

    @staticmethod
    def hide_mtoon1_outline_geometry_nodes() -> list[tuple[str, str]]:
        object_name_to_modifier_names = []
        for obj in bpy.data.objects:
            for modifier in obj.modifiers:
                if not modifier.show_viewport:
                    continue
                if modifier.type != "NODES":
                    continue
                if modifier.node_group.name != shader.OUTLINE_GEOMETRY_GROUP_NAME:
                    continue
                modifier.show_viewport = False
                object_name_to_modifier_names.append((obj.name, modifier.name))
        return object_name_to_modifier_names

    @staticmethod
    def restore_mtoon1_outline_geometry_nodes(
        object_name_to_modifier_names: list[tuple[str, str]]
    ) -> None:
        for object_name, modifier_name in object_name_to_modifier_names:
            obj = bpy.data.objects.get(object_name)
            if not obj:
                continue
            modifier = obj.modifiers.get(modifier_name)
            if not modifier:
                continue
            modifier.show_viewport = True


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
