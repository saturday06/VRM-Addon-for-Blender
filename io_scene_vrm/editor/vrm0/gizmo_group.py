# https://gist.github.com/FujiSunflower/09fdabc7ca991f8292657abc4ef001b0

import bpy
from bpy.types import GizmoGroup

class Vrm0FirstPersonGizmoGroup(GizmoGroup):
    bl_idname = "VRM_GGT_vrm0_first_person"
    bl_label = "First Person Gizmo"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT'}

    @classmethod
    def poll(cls, context):
        if context.active_object.data is None:
            return False
        return hasattr(context.active_object.data, "vrm_addon_extension")

    def setup(self, context):
        armature = context.active_object.data
        ext = armature.vrm_addon_extension
        first_person_props = ext.vrm0.first_person
        first_person_bone = armature.bones[first_person_props.first_person_bone.value]
        first_person_bone_offset = first_person_props.first_person_bone_offset
        gz = self.gizmos.new("GIZMO_GT_move_3d")
        gz.target_set_prop("offset", first_person_props, "first_person_bone_offset")
        gz.matrix_basis = first_person_bone.matrix_local
        gz.draw_style = 'CROSS_2D'
        gz.draw_options = {'ALIGN_VIEW'}
        gz.color = 1.0, 0.5, 0.0
        gz.alpha = 0.5
        gz.color_highlight = 1.0, 0.5, 1.0
        gz.alpha_highlight = 0.5
        gz.scale_basis = 0.25
        self.first_person_gizmo = gz

    def refresh(self, context):
        armature = context.active_object.data
        ext = armature.vrm_addon_extension
        gz = self.first_person_gizmo
        first_person_props = ext.vrm0.first_person
        first_person_bone = armature.bones[first_person_props.first_person_bone.value]
        gz.matrix_basis = first_person_bone.matrix_local
