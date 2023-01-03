from math import ceil
from typing import Set

import bpy
from mathutils import Vector

from ..common.shader import shader_node_group_import


class ICYP_OT_make_mesh_from_bone_envelopes(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "icyp.make_mesh_from_envelopes"
    bl_label = "(WIP)basic mesh for vrm"
    bl_description = "Create mesh along with a simple setup for VRM export"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, _context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> Set[str]:
        self.build_mesh(context)
        return {"FINISHED"}

    resolution: bpy.props.IntProperty(default=5, min=2)  # type: ignore[valid-type]
    max_distance_between_mataballs: bpy.props.FloatProperty(  # type: ignore[valid-type]
        default=0.1, min=0.001
    )
    use_selected_bones: bpy.props.BoolProperty(  # type: ignore[valid-type]
        default=False
    )
    may_vrm_humanoid: bpy.props.BoolProperty(default=True)  # type: ignore[valid-type]
    with_auto_weight: bpy.props.BoolProperty(default=False)  # type: ignore[valid-type]
    not_to_mesh: bpy.props.BoolProperty(default=True)  # type: ignore[valid-type]

    @staticmethod
    def find_material_output_node(material: bpy.types.Material) -> bpy.types.ShaderNode:
        for node in material.node_tree.nodes:
            if node.bl_idname == "ShaderNodeOutputMaterial":
                return node
        raise ValueError(f'No "ShaderNodeOutputMaterial" node in {material}')

    def build_mesh(self, context: bpy.types.Context) -> None:
        if context.active_object.type != "ARMATURE":
            return
        bpy.ops.object.mode_set(mode="OBJECT")
        armature = context.active_object
        mball = bpy.data.metaballs.new(f"{armature.name}_mball")
        mball.threshold = 0.001
        is_vrm_humanoid = False
        for bone in armature.data.bones:
            if self.use_selected_bones and bone.select is False:
                continue
            if "title" in armature and self.may_vrm_humanoid:  # = is VRM humanoid
                is_vrm_humanoid = True
                if bone.name in [
                    armature.data.get(s) for s in ("leftEye", "rightEye", "hips")
                ]:
                    continue
                if bone.name == "root":
                    continue
            hpos = bone.head_local
            hrad = bone.head_radius
            tpos = bone.tail_local
            trad = bone.tail_radius
            if is_vrm_humanoid and armature.data.get("head") == bone.name:
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
            if min([hrad, trad]) < mball.resolution:
                mball.resolution = min([hrad, trad])
        mobj = bpy.data.objects.new(f"{armature.name}_mesh", mball)
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

        bpy.data.metaballs.remove(mball)

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

        def material_init(mat: bpy.types.Material) -> None:
            mat.use_nodes = True
            if not self.material.node_tree:
                return
            for node in mat.node_tree.nodes:
                if node.bl_idname != "ShaderNodeOutputMaterial":
                    mat.node_tree.nodes.remove(node)

        def node_group_create(
            material: bpy.types.Material, shader_node_group_name: str
        ) -> bpy.types.ShaderNodeGroup:
            node_group = material.node_tree.nodes.new("ShaderNodeGroup")
            node_group.node_tree = bpy.data.node_groups[shader_node_group_name]
            return node_group

        shader_node_group_name = "MToon_unversioned"
        shader_node_group_import(shader_node_group_name)
        b_mat = bpy.data.materials.new(f"{armature.name}_mesh_mat")
        material_init(b_mat)
        sg = node_group_create(b_mat, shader_node_group_name)
        if self.material.node_tree:
            b_mat.node_tree.links.new(
                self.find_material_output_node(b_mat).inputs["Surface"],
                sg.outputs["Emission"],
            )
        obj.data.materials.append(b_mat)

        bpy.ops.object.mode_set(mode="OBJECT")
        armature.select_set(True)
