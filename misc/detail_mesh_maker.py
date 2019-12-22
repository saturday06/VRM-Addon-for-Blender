import bpy
import bmesh
from  mathutils import Matrix,Vector
from math import sin,cos,radians,degrees,atan2
class ICYP_OT_DETAIL_MESH_MAKER(bpy.types.Operator):
	bl_idname = "icyp.make_mesh_detail"
	bl_label = "(Don't work currently)detail mesh"
	l_description = "Create mesh awith a simple setup for VRM export"
	bl_options = {'REGISTER', 'UNDO'}

	
	#init before execute 
	def invoke(self, context, event):
		self.base_armature_name = [o for o in bpy.context.selected_objects if o.type=="ARMATURE"][0].name
		self.face_mesh_name = [o for o in bpy.context.selected_objects if o.type=="MESH"][0].name
		face_mesh = bpy.data.objects[self.face_mesh_name]
		face_mesh.display_type = "WIRE"
		mesh_origin_centor_bounds = face_mesh.bound_box
		rfd = face_mesh.bound_box[4]
		lfd = face_mesh.bound_box[0]
		rfu = face_mesh.bound_box[5]
		rbd = face_mesh.bound_box[7]
		self.neck_depth_offset = rfu[2]
		self.head_tall_size = rfu[2] - rfd[2]
		self.head_width_size = rfd[0] - lfd[0]
		self.head_depth_size = rfd[1] - rbd[1]
		return self.execute(context)

	def execute(self, context):
		self.base_armature = bpy.data.objects[self.base_armature_name]
		self.face_mesh = bpy.data.objects[self.face_mesh_name]
		head_bone = self.get_humanoid_bone("head")
		head_matrix = head_bone.matrix_local
		#ボーンマトリックスからY軸移動を打ち消して、あらためて欲しい高さ（上底が身長の高さ）にする変換(matrixはYupだけど、bone座標系はZup)
		head_matrix = head_matrix @ Matrix([[1,0,0,0],[0,1,0,-head_bone.head_local[2]],[0,0,1,0],[0,0,0,1]]) \
									@ Matrix.Translation(Vector([self.head_tall_size/16,self.neck_depth_offset - self.head_tall_size,0]))
		
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
		obj.scale[2] = -1
		bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
		obj.select_set(False)
		bpy.context.view_layer.objects.active = self.face_mesh
		return {"FINISHED"}

	def get_humanoid_bone(self,bone):
		return self.base_armature.data.bones[self.base_armature.data[bone]]


	eye_width_ratio: bpy.props.FloatProperty(default=2, min=0.5, max = 4,name = "Eye width ratio")
	nose_height : bpy.props.FloatProperty(default=0.015, min=0.01, max = 0.1,step=0.001,name = "nose height")
	eye_depth :bpy.props.FloatProperty(default=0.01, min=0.01, max = 0.1,name = "Eye depth")
	mouth_width_ratio:bpy.props.FloatProperty(default = 1, min = 0.3,max = 1,name = "Mouth width")

	def make_face(self,context,mesh):
		def add_point(point):
			return bm.verts.new(point)
		def make_circle(center,radius,axis,divide,angle=360,x_ratio = 1,y_ratio=1):
			if axis == "X":
				axis_n = (0,1)
			elif axis == "Y":
				axis_n = (1,2)
			else:
				axis_n = (2,0)
			if divide < 3:
				print("wrong divide set")
				divide = 3
			if angle == 0:
				print("wrong angle set")
				angle =180
			verts = []
			for i in range(divide):
				pi2 = 3.14*2*radians(angle)/radians(360)
				vert = add_point(center)
				xy = (sin(pi2*i/divide)*y_ratio,cos(pi2*i/divide)*x_ratio)
				for n,j in zip(axis_n,xy):
					vert.co[n] = vert.co[n]+j*radius
				verts.append(vert)
			
			bm.faces.new(verts)
			return
		def width_add(point,add_loc):
			return [p+a for p,a in zip(point,[0,0,add_loc])]
		def up_add(point,add_loc):
			return [p+a for p,a in zip(point,[0,add_loc,0])]
		def depth_add(point,add_loc):
			return [p+a for p,a in zip(point,[add_loc,0,0])]
        # X depth Y up Z width
		bm = bmesh.new()

		bm.verts.new([0,0,0])
		bm.verts.new([0,0,self.head_width_size/2])
		head_top_point_vert = add_point([0,self.head_tall_size,0])
		add_point([-self.head_depth_size/2,0,0])

		neck_point_vert = add_point([-self.head_tall_size/16,self.neck_tail_y,0])
		eye_point = Vector([-self.eye_depth-self.head_depth_size/2,self.head_tall_size/2,self.head_width_size/5])
		eye_width = eye_point[2]*self.eye_width_ratio*0.25
		eye_iris_size = eye_point[2] * self.eye_width_ratio*0.25/2
		make_circle(eye_point,eye_iris_size,"Y",12,360,1,1)
		eye_height = eye_iris_size*0.9
		eye_axis =radians(-15)
		eye_quad_lu_point 	= eye_point + Matrix.Rotation(eye_axis,4,"Y") @ Vector([0,eye_height,-eye_iris_size])
		eye_quad_ld_point 	= eye_point + Matrix.Rotation(eye_axis,4,"Y") @ Vector([0,-eye_height,-eye_iris_size])
		eye_quad_rd_point	= eye_point + Matrix.Rotation(eye_axis,4,"Y") @ Vector([0,-eye_height,eye_iris_size])
		eye_quad_ru_point	= eye_point + Matrix.Rotation(eye_axis,4,"Y") @ Vector([0,eye_height,eye_iris_size])
		eye_innner_point 	= eye_point + Matrix.Rotation(eye_axis,4,"Y") @ Vector([0,-eye_height, - eye_width])
		eye_outer_point 	= eye_point + Matrix.Rotation(eye_axis,4,"Y") @ Vector([0,eye_height, eye_width])

		eye_quad_lu_vert =	add_point(eye_quad_lu_point)
		eye_quad_ld_vert =	add_point(eye_quad_ld_point)
		eye_quad_rd_vert =	add_point(eye_quad_rd_point)
		eye_quad_ru_vert = 	add_point(eye_quad_ru_point)
		eye_innner_vert = add_point(eye_innner_point)
		eye_outer_vert = add_point(eye_outer_point)
		
		bm.edges.new(	[eye_innner_vert,eye_quad_lu_vert])
		bm.edges.new(	[eye_quad_lu_vert,eye_quad_ru_vert])
		bm.edges.new(	[eye_quad_ru_vert,eye_outer_vert])
		bm.edges.new(	[eye_outer_vert,eye_quad_rd_vert])
		bm.edges.new(	[eye_quad_rd_vert,eye_quad_ld_vert])
		bm.edges.new(	[eye_quad_ld_vert,eye_innner_vert])


		
		eye_brow_point = [-self.head_depth_size/2 ,self.head_tall_size*5/8,0]
		eye_brow_innner_point = width_add(eye_brow_point,eye_point[2] - eye_width*1.1)
		eye_brow_outer_point = width_add(eye_brow_point,eye_point[2] + eye_width*1.1)
		eye_brow_innner_vert = add_point(eye_brow_innner_point)
		eye_brow_outer_vert = add_point(eye_brow_outer_point)
		bm.edges.new([eye_brow_innner_vert,eye_brow_outer_vert])

		nose_start_vert = add_point([-self.eye_depth/2-self.head_depth_size/2,eye_point[1],0])
		nose_end_point = [self.nose_height-self.head_depth_size/2,self.head_tall_size/3,0]
		nose_end_vert = add_point(nose_end_point)
		nose_end_side_vert = add_point(depth_add( \
										width_add(
											nose_end_point,\
											eye_innner_point[2]),\
									 	-self.nose_height))
		nose_end_under_vert = add_point(depth_add(nose_end_point,-self.nose_height))
		bm.faces.new([nose_start_vert,nose_end_vert,nose_end_side_vert])
		bm.faces.new([nose_end_under_vert,nose_end_vert,nose_end_side_vert])

		forehead_vert = add_point(eye_brow_point)
		bm.edges.new([forehead_vert,nose_start_vert])

		otogai_point = [-self.head_depth_size/2,0,0]
		otogai_vert = add_point(otogai_point)
		ear_hole_point = [0,eye_point[1],self.head_width_size/2]
		ear_hole_vert = add_point(ear_hole_point)


		mouth_point = Vector([-self.head_depth_size/2+self.nose_height*2/3,self.head_tall_size*2/9,0])
		
		mouth_rotate_radian = atan2(self.nose_height,nose_end_point[1])
		rotated_height_up = Vector((Matrix.Rotation(-mouth_rotate_radian,4,"Z") @ Vector([self.mouth_width_ratio*-0.01,self.mouth_width_ratio*0.01,0])))
		rotated_height_down = Vector((Matrix.Rotation(-mouth_rotate_radian,4,"Z") @ Vector([self.mouth_width_ratio*0.01,self.mouth_width_ratio*0.01*1.3,0])))
		rotated_height_mid_up = Vector((Matrix.Rotation(-mouth_rotate_radian,4,"Z") @ Vector([0,self.mouth_width_ratio*0.005,0])))
		rotated_height_mid_down = Vector((Matrix.Rotation(-mouth_rotate_radian,4,"Z") @ Vector([0,self.mouth_width_ratio*0.005*1.3,0])))
		
		mouth_point_up_vert = add_point(mouth_point + rotated_height_up )
		mouth_point_mid_up_vert = add_point(mouth_point + rotated_height_mid_up )
		mouth_point_mid_down_vert = add_point(mouth_point - rotated_height_mid_down)
		mouth_point_down_vert = add_point(mouth_point - rotated_height_down)
		mouth_outer_point_vert = add_point(depth_add(width_add(mouth_point,self.mouth_width_ratio*self.head_width_size/5),(eye_point[0]-mouth_point[0])*self.mouth_width_ratio))
		mouth_center_vert = add_point(depth_add(mouth_point,rotated_height_up[0]/2))
		bm.faces.new([mouth_point_up_vert,mouth_point_mid_up_vert,mouth_outer_point_vert])
		bm.faces.new([mouth_point_mid_up_vert,mouth_center_vert,mouth_outer_point_vert])
		bm.faces.new([mouth_center_vert,mouth_point_mid_down_vert,mouth_outer_point_vert])
		bm.faces.new([mouth_point_mid_down_vert,mouth_point_down_vert,mouth_outer_point_vert])

		jaw_point = [0,mouth_point[1],self.head_width_size*3/8]
		jaw_vert = add_point(jaw_point)

		bm.edges.new([otogai_vert,jaw_vert])
		bm.edges.new([jaw_vert,ear_hole_vert])

		max_width_point = [0,eye_brow_point[1],self.head_width_size/2]
		max_width_vert = add_point(max_width_point)
		bm.edges.new([ear_hole_vert,max_width_vert])
		make_circle([0,max_width_point[1],0],max_width_point[2],"Y",12,90,1,(self.head_tall_size-max_width_point[1])/max_width_point[2])
		bm.to_mesh(mesh)
		bm.free()
		return 