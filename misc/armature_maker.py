import bpy

class ICYP_OT_MAKE_ARAMATURE(bpy.types.Operator):
	bl_idname = "icyp.make_basic_armature"
	bl_label = "(WIP)basic aramature"
	bl_description = "make armature and simple setup for VRM export"
	bl_options = {'REGISTER', 'UNDO'}
	
	#身長 at meter
	tall: bpy.props.FloatProperty(default=1.70, min=0.3, step=0.001)
	#頭身
	head_ratio: bpy.props.FloatProperty(default=8.0, min=4, step=0.05)
	#足-胴比率：０：子供、１：大人　に近くなる
	age_ratio: bpy.props.FloatProperty(default=0.5, min=0, max=1, step=0.1)
	#目の奥み
	eye_depth: bpy.props.FloatProperty(default=-0.03, min=-0.1, max=0, step=0.005)
	#肩幅
	shoulder_in_width: bpy.props.FloatProperty(default=0.2125, min=0.01, step=0.005)
	shoulder_width: bpy.props.FloatProperty(default=0.08, min=0.01, step=0.005)
	#手（パー
	hand_size :bpy.props.FloatProperty(default=0.18, min=0.01, step=0.005)
	#足幅
	leg_width: bpy.props.FloatProperty(default=0.1, min=0.01, step=0.005)
	leg_size: bpy.props.FloatProperty(default=0.26, min=0.05, step=0.005)
	
	def execute(self, context):
		armature = self.make_armature(context)
		#self.setup_as_vrm(armature)
		return {"FINISHED"}

	def make_armature(self, context):
		bpy.ops.object.add(type='ARMATURE', enter_editmode=True, location=(0,0,0))
		armature = context.object
		armature.name = "skelton"
		armature.show_in_front = True
		armature.data.display_type = "STICK"
		armature.data.use_mirror_x = True
		bone_dic = {}
		def bone_add(name, head_pos, tail_pos, parent_bone=None):
			added_bone = armature.data.edit_bones.new(name)
			added_bone.head = head_pos
			added_bone.tail = tail_pos
			if parent_bone is not None:
				added_bone.parent = parent_bone
			bone_dic.update({name:added_bone})
			return added_bone
		def x_mirror_bones_add(base_name, right_head_pos, right_tail_pos, parent_bones):
			left_bone = bone_add(base_name + "_l", right_head_pos, right_tail_pos, parent_bones[0])
			right_bone = bone_add(base_name + "_r",
									[pos*axis for pos, axis in zip(right_head_pos, (-1, 1, 1))],
									[pos*axis for pos, axis in zip(right_tail_pos, (-1, 1, 1))],
									parent_bones[1]
								)
			return left_bone,right_bone
		def z_add(posA, add_z):
			pos = [pA+_add for pA,_add in zip(posA,[0,0,add_z])]
			return pos
		def x_add(posA, add_x):
			pos = [pA + _add for pA, _add in zip(posA, [add_x, 0, 0])]
			return pos
		root = bone_add("root", (0, 0, 0), (0, 0,0.3))
		head_size = self.tall / self.head_ratio
		#down side (前は8頭身の時の股上/股下の股下側割合、後ろは4頭身のときの〃を線形補完)
		eight_upside_ratio, four_upside_ratio = 0.5, (2.5/4)*(1-self.age_ratio)+(0.5)*self.age_ratio
		hip_up_down_ratio = eight_upside_ratio * (1 - (8 - self.head_ratio) / 4) + four_upside_ratio * (8 - self.head_ratio) / 4
		#チェスト下とチェスト～首の割合
		upper_chest_neck_ratio = (1-(8-self.head_ratio)/4)*(1/3) + ((8-self.head_ratio)/4)*0.1

		neck_len = (1-upper_chest_neck_ratio)*(self.tall*(1-hip_up_down_ratio)/2)/3
		upper_chest_len = neck_len*2
		chest_len = (self.tall*hip_up_down_ratio - head_size - neck_len - upper_chest_len)/2
		spine_len = chest_len
		#体幹
		Hips = bone_add("Hips", (0,0, self.tall*(1-hip_up_down_ratio) ), (0,0.1,self.tall*(1-hip_up_down_ratio)),root)
		Spine = bone_add("Spine",Hips.head,z_add(Hips.head,spine_len),Hips)
		Chest = bone_add("Chest", Spine.tail, z_add(Spine.tail,chest_len), Spine)
		upperChest = bone_add("upperChest", Chest.tail, z_add(Chest.tail,upper_chest_len), Chest)
		Neck = bone_add("Neck", upperChest.tail, z_add(upperChest.tail,neck_len), upperChest)
		Head = bone_add("Head", (0,0, self.tall-head_size), (0,0, self.tall), Neck)
		#目
		eye_depth = self.eye_depth
		x_mirror_bones_add("eye", (head_size / 5, 0, Head.head[2] + head_size / 2),
									(head_size / 5, eye_depth, Head.head[2] + head_size / 2),
									(Head, Head))
		#足
		leg_width = self.leg_width
		leg_size = self.leg_size
		leg_bone_lengh =( self.tall*(1-hip_up_down_ratio) - self.tall*0.05 )/2
		upside_legs = x_mirror_bones_add("Upper_Leg",
				x_add(Hips.head, leg_width),
				z_add(x_add(Hips.head, leg_width), -leg_bone_lengh),
				 (Hips, Hips)
				)
		lower_legs = x_mirror_bones_add("Lower_Leg",
				upside_legs[0].tail,
				(leg_width,0,self.tall*0.05),
				upside_legs
				)
		Foots = x_mirror_bones_add("Foot",
				lower_legs[0].tail,
				(leg_width,-leg_size*(2/3),0),
				lower_legs
				)
		Toes = x_mirror_bones_add("Toes",
				Foots[0].tail,
				(leg_width,-leg_size,0),
				Foots
				)						
		
		#肩～指
		shoulder_in_pos = self.shoulder_in_width / 2
		
		shoulders = x_mirror_bones_add("shoulder",
			x_add(upperChest.tail, shoulder_in_pos),
			x_add(upperChest.tail, shoulder_in_pos + self.shoulder_width),
			(upperChest,upperChest))

		arm_lengh = head_size * (1.5*(1-(self.head_ratio-6)/2)+1*((self.head_ratio-6)/2))
		arms = x_mirror_bones_add("Arm",
			shoulders[0].tail,
			x_add(shoulders[0].tail,arm_lengh),
			shoulders)
		hand_size = self.hand_size
		forearms = x_mirror_bones_add("forearm",
			arms[0].tail,
			#グーにするとパーの半分くらいになる、グーのとき手を含む下腕の長さと上腕の長さが概ね一緒
			x_add(arms[0].tail,arm_lengh - hand_size/2),
			arms)
		hands = x_mirror_bones_add("hand",
			forearms[0].tail,
			x_add(forearms[0].tail,hand_size/2),
			forearms
		)

		def fingers(proximal_bones):
			#intermediate_bones
			#distal_bones
			pass


		bpy.ops.object.mode_set(mode='OBJECT')
		return armature