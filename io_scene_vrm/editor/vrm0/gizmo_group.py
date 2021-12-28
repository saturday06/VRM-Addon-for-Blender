import bpy
from bpy.types import GizmoGroup


# https://gist.github.com/FujiSunflower/09fdabc7ca991f8292657abc4ef001b0
class Vrm0FirstPersonBoneOffsetGizmoGroup(GizmoGroup):  # type: ignore[misc]
    bl_idname = "VRM_GGT_vrm0_first_person_bone_offset"
    bl_label = "First Person Bone Offset Gizmo"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_options = {"3D", "PERSISTENT"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if context.active_object.data is None:
            return False
        return hasattr(context.active_object.data, "vrm_addon_extension")

    def setup(self, context: bpy.types.Context) -> None:
        armature = context.active_object.data
        ext = armature.vrm_addon_extension
        first_person_props = ext.vrm0.first_person
        first_person_bone = armature.bones[first_person_props.first_person_bone.value]
        gizmo = self.gizmos.new("GIZMO_GT_move_3d")
        gizmo.target_set_prop("offset", first_person_props, "first_person_bone_offset")
        gizmo.matrix_basis = first_person_bone.matrix_local
        gizmo.draw_style = "CROSS_2D"
        gizmo.draw_options = {"ALIGN_VIEW"}
        gizmo.color = 1.0, 0.5, 0.0
        gizmo.alpha = 0.5
        gizmo.color_highlight = 1.0, 0.5, 1.0
        gizmo.alpha_highlight = 0.5
        gizmo.scale_basis = 0.25

        # pylint: disable=attribute-defined-outside-init;
        self.first_person_gizmo = gizmo
        # pylint: enable=attribute-defined-outside-init;

    def refresh(self, context: bpy.types.Context) -> None:
        armature = context.active_object.data
        ext = armature.vrm_addon_extension
        gizmo = self.first_person_gizmo
        first_person_props = ext.vrm0.first_person
        first_person_bone = armature.bones[first_person_props.first_person_bone.value]
        gizmo.matrix_basis = first_person_bone.matrix_local
