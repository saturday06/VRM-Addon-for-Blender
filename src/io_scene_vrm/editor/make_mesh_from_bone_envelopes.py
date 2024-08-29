from collections.abc import Set as AbstractSet
from math import ceil
from typing import TYPE_CHECKING

import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty
from bpy.types import (
    Armature,
    Context,
    Material,
    Mesh,
    Operator,
    ShaderNode,
    ShaderNodeGroup,
    ShaderNodeOutputMaterial,
)
from mathutils import Vector

from ..common.shader import shader_node_group_import


class ICYP_OT_make_mesh_from_bone_envelopes(Operator):
    bl_idname = "icyp.make_mesh_from_envelopes"
    bl_label = "(WIP)basic mesh for vrm"
    bl_description = "Create mesh along with a simple setup for VRM export"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, _context: Context) -> bool:
        return True

    def execute(self, context: Context) -> set[str]:
        self.build_mesh(context)
        return {"FINISHED"}

    resolution: IntProperty(default=5, min=2)  # type: ignore[valid-type]
    max_distance_between_mataballs: FloatProperty(  # type: ignore[valid-type]
        default=0.1, min=0.001
    )
    use_selected_bones: BoolProperty(  # type: ignore[valid-type]
        default=False
    )
    may_vrm_humanoid: BoolProperty(default=True)  # type: ignore[valid-type]
    with_auto_weight: BoolProperty(default=False)  # type: ignore[valid-type]
    not_to_mesh: BoolProperty(default=True)  # type: ignore[valid-type]

    @staticmethod
    def find_material_output_node(material: Material) -> ShaderNode:
        if not material.node_tree:
            message = "No node tree"
            raise ValueError(message)
        for node in material.node_tree.nodes:
            if node.bl_idname == "ShaderNodeOutputMaterial" and isinstance(
                node, ShaderNodeOutputMaterial
            ):
                return node
        message = f'No "ShaderNodeOutputMaterial" node in {material}'
        raise ValueError(message)

    @staticmethod
    def material_init(mat: Material) -> None:
        mat.use_nodes = True
        if not mat.node_tree:
            return
        for node in mat.node_tree.nodes:
            if node.bl_idname != "ShaderNodeOutputMaterial":
                mat.node_tree.nodes.remove(node)

    @staticmethod
    def node_group_create(
        context: Context, material: Material, shader_node_group_name: str
    ) -> ShaderNodeGroup:
        if not material.node_tree:
            message = "No node tree"
            raise ValueError(message)
        node_group = material.node_tree.nodes.new("ShaderNodeGroup")
        if not isinstance(node_group, ShaderNodeGroup):
            message = f"{type(node_group)} is not a ShaderNodeGroup"
            raise TypeError(message)
        node_group.node_tree = context.blend_data.node_groups[shader_node_group_name]
        return node_group

    def build_mesh(self, context: Context) -> None:
        armature = context.active_object
        if not armature or armature.type != "ARMATURE":
            return
        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        bpy.ops.object.mode_set(mode="OBJECT")
        mball = context.blend_data.metaballs.new(f"{armature.name}_mball")
        mball.threshold = 0.001
        is_vrm_humanoid = False
        for bone in armature_data.bones:
            if self.use_selected_bones and bone.select is False:
                continue
            if "title" in armature and self.may_vrm_humanoid:  # = is VRM humanoid
                is_vrm_humanoid = True
                if bone.name in [
                    armature_data.get(s) for s in ("leftEye", "rightEye", "hips")
                ]:
                    continue
                if bone.name == "root":
                    continue
            hpos = bone.head_local
            hrad = bone.head_radius
            tpos = bone.tail_local
            trad = bone.tail_radius
            if is_vrm_humanoid and armature_data.get("head") == bone.name:
                elem = mball.elements.new()
                elem.co = (Vector(hpos) + Vector(tpos)) / 2
                elem.radius = Vector(Vector(tpos) - Vector(hpos)).length / 2
                continue
            if (
                Vector(Vector(tpos) - Vector(hpos)).length / self.resolution
                > self.max_distance_between_mataballs
            ):
                self.resolution = ceil(
                    Vector(Vector(tpos) - Vector(hpos)).length
                    / self.max_distance_between_mataballs
                )
                self.resolution = max(2, self.resolution)
            for i in range(self.resolution):
                loc = hpos + ((tpos - hpos) / (self.resolution - 1)) * i
                rad = hrad + ((trad - hrad) / (self.resolution - 1)) * i
                elem = mball.elements.new()
                elem.co = loc
                elem.radius = rad
            mball.resolution = min(hrad, trad, mball.resolution)
        mobj = context.blend_data.objects.new(f"{armature.name}_mesh", mball)
        mobj.location = armature.location
        mobj.rotation_quaternion = armature.rotation_quaternion
        mobj.scale = armature.scale
        bpy.ops.object.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")
        context.scene.collection.objects.link(mobj)
        context.view_layer.objects.active = mobj

        if self.not_to_mesh:
            return

        mobj.select_set(True)
        bpy.ops.object.convert(target="MESH")

        context.blend_data.metaballs.remove(mball)

        obj = context.view_layer.objects.active
        context.view_layer.objects.active = armature
        obj.select_set(True)
        if self.with_auto_weight:
            bpy.ops.object.parent_set(type="ARMATURE_AUTO")
            obj.select_set(True)
            context.view_layer.objects.active = obj
            bpy.ops.object.vertex_group_limit_total(limit=4)
        armature.select_set(False)

        context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.quads_convert_to_tris(quad_method="BEAUTY", ngon_method="BEAUTY")
        bpy.ops.uv.smart_project()

        shader_node_group_name = "MToon_unversioned"
        shader_node_group_import(context, shader_node_group_name)
        b_mat = context.blend_data.materials.new(f"{armature.name}_mesh_mat")
        self.material_init(b_mat)
        sg = self.node_group_create(context, b_mat, shader_node_group_name)
        if b_mat.node_tree:
            b_mat.node_tree.links.new(
                self.find_material_output_node(b_mat).inputs["Surface"],
                sg.outputs["Emission"],
            )
        if not isinstance(obj.data, Mesh):
            message = f"{type(obj.data)} is not a Mesh"
            raise TypeError(message)
        obj.data.materials.append(b_mat)

        bpy.ops.object.mode_set(mode="OBJECT")
        armature.select_set(True)

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        resolution: int  # type: ignore[no-redef]
        max_distance_between_mataballs: float  # type: ignore[no-redef]
        use_selected_bones: bool  # type: ignore[no-redef]
        may_vrm_humanoid: bool  # type: ignore[no-redef]
        with_auto_weight: bool  # type: ignore[no-redef]
        not_to_mesh: bool  # type: ignore[no-redef]
