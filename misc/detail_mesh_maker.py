import bpy
import bmesh
from  mathutils import Matrix,Vector
class ICYP_OT_DETAIL_MESH_MAKER(bpy.types.Operator):
	bl_idname = "icyp.make_mesh_detail"
	bl_label = "(Don't work currently)detail mesh"
	l_description = "Create mesh awith a simple setup for VRM export"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		self.base_armature = [o for o in bpy.context.selected_objects if o.type=="ARMATURE"][0]
		self.face_mesh =  [o for o in bpy.context.selected_objects if o.type=="MESH"][0]
		self.face_mesh.display_type = "WIRE"
		self.mesh_origin_centor_bounds = self.face_mesh.bound_box
		rfd = self.face_mesh.bound_box[4]
		lfd = self.face_mesh.bound_box[0]
		rfu = self.face_mesh.bound_box[5]
		rbd = self.face_mesh.bound_box[7]
		self.head_tall_size = rfu[2] - rfd[2]
		self.head_width_size = rfd[0] - lfd[0]
		self.head_depth_size = rfd[1] - rbd[1]
		

		head_bone = self.get_humanoid_bone("head")
		head_matrix = head_bone.matrix_local
		#ボーンマトリックスからY軸移動を打ち消して、あらためて欲しい高さ（上底が身長の高さ）にする変換(matrixはYupだけど、bone座標系はZup)
		head_matrix = head_matrix @ Matrix([[1,0,0,0],[0,1,0,-head_bone.head_local[2]],[0,0,1,0],[0,0,0,1]]) \
									@ Matrix.Translation(Vector([self.head_tall_size/16,rfu[2] - self.head_tall_size,0]))
		
		self.neck_tail_y = self.head_tall_size - (head_bone.tail_local[2] - head_bone.head_local[2])

		self.mesh = bpy.data.meshes.new("template_face")
		self.make_face(context,self.mesh)
		obj = bpy.data.objects.new("template_face", self.mesh)
		scene = bpy.context.scene
		scene.collection.objects.link(obj)
		bpy.context.view_layer.objects.active = obj
		obj.matrix_local = head_matrix
		bpy.ops.object.modifier_add(type='MIRROR')
		bpy.ops.object.mode_set(mode='OBJECT')
		bpy.ops.object.select_all(action="DESELECT")
		obj.select_set(True)
		bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

		return {"FINISHED"}

	def get_humanoid_bone(self,bone):
		return self.base_armature.data.bones[self.base_armature.data[bone]]


	def make_face(self,context,mesh):
        # X depth Y up -Z width
		bm = bmesh.new()
		vert = []
		bm.verts.new([0,0,0])
		bm.verts.new([0,0,-self.head_width_size/2])
		bm.verts.new([0,self.head_tall_size,0])
		bm.verts.new([-self.head_depth_size/2,0,0])
		neck_point = bm.verts.new([-self.head_tall_size/16,self.neck_tail_y,0])


		bm.to_mesh(mesh)
		bm.free()
		return 