import bpy,bmesh

class ICYP_MESH_Maker():
	def __init__(self,args):
		mesh = bpy.data.meshes.new("template_humanoid")
		self.make_humanoid(mesh,args)
		obj = bpy.data.objects.new("a", mesh)
		scene = bpy.context.scene
		scene.collection.objects.link(obj)
		bpy.context.view_layer.objects.active = obj
		bpy.ops.object.modifier_add(type='MIRROR')
		return


	def make_humanoid(self, mesh, args):
		self.bm = bmesh.new()
		#region body
		#make head
		head_size = args.tall / args.head_ratio
		self.make_half_cube([head_size,head_size,head_size],[0,0,args.tall - head_size])
		#make neck
		neck_bone = args.armature_obj.data.bones[args.armature_obj.data["neck"]]
		self.make_half_cube([head_size / 2, head_size / 2, neck_bone.length], neck_bone.head_local)
		#TODO under neck

		#endregion body

		#region arm
		#TODO
		#endregion arm

		#region leg
		#TODO
		#endregion leg
		
		self.bm.to_mesh(mesh)
		self.bm.free()
		return

	def make_cube(self, xyz, translation=None):
		points = self.cubic_points(xyz, translation)
		verts = []
		for p in points:
			verts.append(self.bm.verts.new(p))
		for poly in self.cube_loop:
			self.bm.faces.new([verts[i] for i in poly])

	def make_half_cube(self, xyz,translation=None):
		points = self.half_cubic_points(xyz,translation)
		verts = []
		for p in points:
			verts.append(self.bm.verts.new(p))
		for poly in self.cube_loop_half:
			self.bm.faces.new([verts[i] for i in poly])
	
	def cubic_points(self, xyz, translation=None):
		if translation is None:
			translation = [0,0,0]
		x = xyz[0]
		y = xyz[1]
		z = xyz[2]
		tx = translation[0]
		ty = translation[1]
		tz = translation[2]
		return (
			(-x/2+tx,-y/2+ty,0+tz),
			(-x/2+tx,y/2+ty,0+tz),
			(x/2+tx,y/2+ty,0+tz),
			(x/2+tx,-y/2+ty,0+tz),

			(-x/2+tx,-y/2+ty,z+tz),
			(-x/2+tx,y/2+ty,z+tz),
			(x/2+tx,y/2+ty,z+tz),
			(x/2+tx,-y/2+ty,z+tz),
		)

	cube_loop = [
		[0,1,2,3],
		[7,6,5,4],
		[4,5,1,0],
		[5,6,2,1],
		[6,7,3,2],
		[7,4,0,3]
	]

	def half_cubic_points(self, xyz, translation=None):
		if translation is None:
			translation = [0,0,0]
		x = xyz[0]
		y = xyz[1]
		z = xyz[2]
		tx = translation[0]
		ty = translation[1]
		tz = translation[2]
		return (
			(0,-y/2+ty,0+tz),
			(0,y/2+ty,0+tz),
			(x/2+tx,y/2+ty,0+tz),
			(x/2+tx,-y/2+ty,0+tz),

			(0,-y/2+ty,z+tz),
			(0,y/2+ty,z+tz),
			(x/2+tx,y/2+ty,z+tz),
			(x/2+tx,-y/2+ty,z+tz),
		)

	cube_loop_half = [
		[0,1,2,3],
		[7,6,5,4],
		[5,6,2,1],
		[6,7,3,2],
		[7,4,0,3]
	]
