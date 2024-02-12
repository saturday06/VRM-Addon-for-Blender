import secrets
import string
from abc import ABC, abstractmethod
from typing import Optional, Union

import bpy
from bpy.types import Armature, Context, NodesModifier, Object
from mathutils import Matrix, Quaternion

from ..common import shader
from ..common.deep import Json, make_json
from ..editor.vrm0.property_group import Vrm0HumanoidPropertyGroup
from ..editor.vrm1.property_group import Vrm1HumanoidPropertyGroup
from ..external import io_scene_gltf2_support


class AbstractBaseVrmExporter(ABC):
    def __init__(
        self,
        context: Context,
    ) -> None:
        self.context = context
        self.saved_current_pose_matrix_basis_dict: dict[str, Matrix] = {}
        self.saved_current_pose_matrix_dict: dict[str, Matrix] = {}
        self.saved_pose_position: Optional[str] = None
        self.saved_vrm1_look_at_preview: bool = False
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
        armature: Object,
        armature_data: Armature,
        humanoid: Union[Vrm0HumanoidPropertyGroup, Vrm1HumanoidPropertyGroup],
    ) -> None:
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
            return

        if pose == Vrm1HumanoidPropertyGroup.POSE_ITEM_VALUE_REST_POSITION_POSE or (
            pose == Vrm1HumanoidPropertyGroup.POSE_ITEM_VALUE_CUSTOM_POSE
            and not (action and action.name in bpy.data.actions)
        ):
            self.saved_pose_position = armature_data.pose_position
            armature_data.pose_position = "REST"
            return

        if self.context.view_layer.objects.active is not None:
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        self.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode="POSE")

        self.saved_pose_position = armature_data.pose_position
        if armature_data.pose_position != "POSE":
            armature_data.pose_position = "POSE"

        bpy.context.view_layer.update()
        self.saved_current_pose_matrix_basis_dict = {
            bone.name: bone.matrix_basis.copy() for bone in armature.pose.bones
        }
        self.saved_current_pose_matrix_dict = {
            bone.name: bone.matrix.copy() for bone in armature.pose.bones
        }

        ext = armature_data.vrm_addon_extension
        self.saved_vrm1_look_at_preview = ext.vrm1.look_at.enable_preview
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

        if action and action.name in bpy.data.actions:
            pose_marker_frame = 0
            if pose_marker_name:
                for search_pose_marker in action.pose_markers.values():
                    if search_pose_marker.name == pose_marker_name:
                        pose_marker_frame = search_pose_marker.frame
                        break
            armature.pose.apply_pose_from_action(
                action, evaluation_time=pose_marker_frame
            )

        bpy.context.view_layer.update()

    def restore_pose(self, armature: Object, armature_data: Armature) -> None:
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
            armature_data.pose_position = self.saved_pose_position
        bpy.ops.object.mode_set(mode="OBJECT")

        ext = armature_data.vrm_addon_extension
        if (
            ext.is_vrm1()
            and ext.vrm1.look_at.enable_preview != self.saved_vrm1_look_at_preview
        ):
            ext.vrm1.look_at.enable_preview = self.saved_vrm1_look_at_preview

    def clear_blend_shape_proxy_previews(self, armature_data: Armature) -> list[float]:
        ext = armature_data.vrm_addon_extension
        saved_previews = []
        for blend_shape_group in ext.vrm0.blend_shape_master.blend_shape_groups:
            saved_previews.append(blend_shape_group.preview)
            blend_shape_group.preview = 0
        return saved_previews

    def restore_blend_shape_proxy_previews(
        self, armature_data: Armature, previews: list[float]
    ) -> None:
        ext = armature_data.vrm_addon_extension
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
                if not isinstance(modifier, NodesModifier):
                    continue
                node_group = modifier.node_group
                if (
                    not node_group
                    or node_group.name != shader.OUTLINE_GEOMETRY_GROUP_NAME
                ):
                    continue
                modifier.show_viewport = False
                object_name_to_modifier_names.append((obj.name, modifier.name))
        return object_name_to_modifier_names

    @staticmethod
    def restore_mtoon1_outline_geometry_nodes(
        object_name_to_modifier_names: list[tuple[str, str]],
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
