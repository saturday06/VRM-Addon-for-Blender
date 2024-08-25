from collections.abc import Set as AbstractSet

from bpy.types import Context, Operator


class ICYP_OT_draw_model(Operator):
    bl_idname = "vrm.model_draw"
    bl_label = "Preview MToon 0.0"
    bl_description = "Draw selected with MToon of GLSL"
    bl_options: AbstractSet[str] = {"REGISTER"}

    def execute(self, _context: Context) -> set[str]:
        return {"CANCELLED"}


class ICYP_OT_remove_draw_model(Operator):
    bl_idname = "vrm.model_draw_remove"
    bl_label = "Remove MToon preview"
    bl_description = "remove draw function"
    bl_options: AbstractSet[str] = {"REGISTER"}

    def execute(self, _context: Context) -> set[str]:
        return {"CANCELLED"}
