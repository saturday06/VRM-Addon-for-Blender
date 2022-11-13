import secrets
import string
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, Union

import bpy

from ..common.char import INTERNAL_NAME_PREFIX
from ..common.deep import Json, make_json


class AbstractBaseVrmExporter(ABC):
    def __init__(
        self,
        context: bpy.types.Context,
    ) -> None:
        self.context = context
        self.original_pose_library: Optional[bpy.types.Action] = None
        self.saved_current_pose_library: Optional[bpy.types.Action] = None
        self.saved_pose_position: Optional[str] = None
        self.export_id = "BlenderVrmAddonExport" + (
            "".join(secrets.choice(string.digits) for _ in range(10))
        )

    @abstractmethod
    def export_vrm(self) -> Optional[bytes]:
        pass

    def setup_pose(
        self,
        armature: bpy.types.Object,
        user_pose_library: Optional[bpy.types.Action],
        user_pose_marker_name: str,
    ) -> None:
        if self.context.view_layer.objects.active is not None:
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        self.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode="POSE")

        self.saved_pose_position = armature.data.pose_position

        pose_library: Optional[bpy.types.Action] = None
        pose_index: Optional[int] = None
        if (
            user_pose_library
            and user_pose_library.name in bpy.data.actions
            and user_pose_marker_name
        ):
            pose_library = user_pose_library
            if pose_library:
                for search_pose_index, search_pose_marker in enumerate(
                    pose_library.pose_markers.values()
                ):
                    if search_pose_marker.name == user_pose_marker_name:
                        pose_index = search_pose_index
                        armature.data.pose_position = "POSE"
                        break

        self.original_pose_library = armature.pose_library
        self.saved_current_pose_library = bpy.data.actions.new(
            INTERNAL_NAME_PREFIX + self.export_id + "SavedCurrentPoseLibrary"
        )

        armature.pose_library = self.saved_current_pose_library
        bpy.ops.poselib.pose_add(
            name=INTERNAL_NAME_PREFIX + self.export_id + "SavedCurrentPose"
        )

        if pose_library and pose_index is not None:
            armature.pose_library = pose_library
            bpy.ops.poselib.apply_pose(pose_index=pose_index)

    def restore_pose(self, armature: bpy.types.Object) -> None:
        if self.context.view_layer.objects.active is not None:
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        self.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode="POSE")

        if self.saved_current_pose_library:
            armature.pose_library = self.saved_current_pose_library
            bpy.ops.poselib.apply_pose(pose_index=0)
            bpy.ops.poselib.unlink()

        armature.pose_library = self.original_pose_library

        if (
            self.saved_current_pose_library
            and not self.saved_current_pose_library.users
        ):
            bpy.data.actions.remove(self.saved_current_pose_library)

        if self.saved_pose_position:
            armature.data.pose_position = self.saved_pose_position

        bpy.ops.object.mode_set(mode="OBJECT")


def assign_dict(
    target: Dict[str, Json],
    key: str,
    value: Union[Json, Tuple[float, float, float], Tuple[float, float, float, float]],
    default_value: Json = None,
) -> bool:
    if value is None or value == default_value:
        return False
    target[key] = make_json(value)
    return True
