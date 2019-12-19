import bpy
import bmesh

class ICYP_OT_DETAIL_MESH_MAKER(bpy.types.Operator):
    bl_idname = "icyp.make_mesh_detail"
    bl_label = "(Don't work currently)detail mesh"
    l_description = "Create mesh awith a simple setup for VRM export"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        self.base_armature = [o for o in bpy.context.selected_objects if o.type=="ARMATURE"][0]
        self.face_mesh =  [o for o in bpy.context.selected_objects if o.type=="MESH"][0]
        self.mesh_origin_centor_bounds = self.mesh_face_mesh.bound_box
        rfd = self.mesh_face_mesh.bound_box[4]
        lfd = self.mesh_face_mesh.bound_box[0]
        rfu = self.mesh_face_mesh.bound_box[5]
        rbd = self.mesh_face_mesh.bound_box[7]
        self.head_tall_size = rfu[2] - rfd[2]
        self.head_width_size = rfd[0] - lfd[0]
        self.head_depth_size = rfd[1] - rbd[1]
        self.mesh = bpy.data.meshes.new("template_face")
        self.make_face(context,mesh)
        obj = bpy.data.objects.new("template_face", mesh)
        scene = bpy.context.scene
        scene.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        obj.matrix_local = self.face_mesh.matrix_local
        bpy.ops.object.modifier_add(type='MIRROR')


        return {"FINISHED"}


    def make_face(self,context,mesh):
        bm = bmesh.new()
        bm.to_mesh(mesh)
        bm.free()
        return 