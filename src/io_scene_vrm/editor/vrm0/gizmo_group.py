# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Set as AbstractSet

from bpy.types import Armature, Context, GizmoGroup

from ..extension import get_armature_extension


# https://gist.github.com/FujiSunflower/09fdabc7ca991f8292657abc4ef001b0
class Vrm0FirstPersonBoneOffsetGizmoGroup(GizmoGroup):
    bl_idname = "VRM_GGT_vrm0_first_person_bone_offset"
    bl_label = "First Person Bone Offset Gizmo"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_options: AbstractSet[str] = {"3D", "PERSISTENT"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        active_object = context.active_object
        if not active_object:
            return False
        return active_object.type == "ARMATURE"

    def setup(self, context: Context) -> None:
        active_object = context.active_object
        if not active_object:
            return
        armature_data = active_object.data
        if not isinstance(armature_data, Armature):
            return
        ext = get_armature_extension(armature_data)
        first_person = ext.vrm0.first_person
        first_person_bone = armature_data.bones[
            first_person.first_person_bone.bone_name
        ]
        gizmo = self.gizmos.new("GIZMO_GT_move_3d")
        gizmo.target_set_prop("offset", first_person, "first_person_bone_offset")
        gizmo.matrix_basis = first_person_bone.matrix_local
        gizmo.draw_style = "CROSS_2D"
        gizmo.draw_options = {"ALIGN_VIEW"}
        gizmo.color = 1.0, 0.5, 0.0
        gizmo.alpha = 0.5
        gizmo.color_highlight = 1.0, 0.5, 1.0
        gizmo.alpha_highlight = 0.5
        gizmo.scale_basis = 0.25

        self.first_person_gizmo = gizmo

    def refresh(self, context: Context) -> None:
        active_object = context.active_object
        if not active_object:
            return
        armature_data = active_object.data
        if not isinstance(armature_data, Armature):
            return
        ext = get_armature_extension(armature_data)
        gizmo = self.first_person_gizmo
        first_person = ext.vrm0.first_person
        first_person_bone = armature_data.bones[
            first_person.first_person_bone.bone_name
        ]
        gizmo.matrix_basis = first_person_bone.matrix_local
