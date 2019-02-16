import bpy
from mathutils import Matrix
from math import radians,sqrt
import json
class ICYP_OT_MAKE_ARAMATURE(bpy.types.Operator):
	bl_idname = "icyp.make_basic_armature"
	bl_label = "(WIP)basic armature"
	bl_description = "make armature and simple setup for VRM export"
	bl_options = {'REGISTER', 'UNDO'}
	
	#身長 at meter
	tall: bpy.props.FloatProperty(default=1.70, min=0.3, step=0.001)
	#頭身
	head_ratio: bpy.props.FloatProperty(default=8.0, min=4, step=0.05)
	#足-胴比率：０：子供、１：大人　に近くなる(低等身で有効)
	aging_ratio: bpy.props.FloatProperty(default=0.5, min=0, max=1, step=0.1)
	#目の奥み
	eye_depth: bpy.props.FloatProperty(default=-0.03, min=-0.1, max=0, step=0.005)
	#肩幅
	shoulder_in_width: bpy.props.FloatProperty(default=0.2125, min=0.01, step=0.005)
	shoulder_width: bpy.props.FloatProperty(default=0.08, min=0.01, step=0.005)
	#腕長さ率
	arm_length_ratio : bpy.props.FloatProperty(default=1, min=0.5, step=0.01)
	#手
	hand_size :bpy.props.FloatProperty(default=0.18, min=0.01, step=0.005)
	finger_1_2_ratio :bpy.props.FloatProperty(default=0.75, min=0.5,max=1, step=0.005)
	finger_2_3_ratio :bpy.props.FloatProperty(default=0.75, min=0.5,max=1, step=0.005)
	#足
	leg_length_ratio : bpy.props.FloatProperty(default=0.5, min=0.3, max=0.6,step=0.01)
	leg_width: bpy.props.FloatProperty(default=0.1, min=0.01, step=0.005)
	leg_size: bpy.props.FloatProperty(default=0.26, min=0.05, step=0.005)
	
	def execute(self, context):
		armature,compare_dict = self.make_armature(context)
		self.setup_as_vrm(armature,compare_dict)
		return {"FINISHED"}

	def make_armature(self, context):
		bpy.ops.object.add(type='ARMATURE', enter_editmode=True, location=(0,0,0))
		armature = context.object
		armature.name = "skelton"
		armature.show_in_front = True
		
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
			left_bone = bone_add(base_name + "_L", right_head_pos, right_tail_pos, parent_bones[0])
			right_bone = bone_add(base_name + "_R",
									[pos*axis for pos, axis in zip(right_head_pos, (-1, 1, 1))],
									[pos*axis for pos, axis in zip(right_tail_pos, (-1, 1, 1))],
									parent_bones[1]
								)
			return left_bone,right_bone
		def x_add(posA, add_x):
			pos = [pA + _add for pA, _add in zip(posA, [add_x, 0, 0])]
			return pos
		def y_add(posA, add_y):
			pos = [pA + _add for pA, _add in zip(posA, [0, add_y, 0])]
			return pos
		def z_add(posA, add_z):
			pos = [pA+_add for pA,_add in zip(posA,[0,0,add_z])]
			return pos

		root = bone_add("root", (0, 0, 0), (0, 0,0.3))
		head_size = self.tall / self.head_ratio
		#down side (前は8頭身の時の股上/股下の股下側割合、後ろは4頭身のときの〃を年齢具合で線形補完)(股上高めにすると破綻する)
		eight_upside_ratio, four_upside_ratio = 1-self.leg_length_ratio, (2.5/4)*(1-self.aging_ratio)+(1-self.leg_length_ratio)*self.aging_ratio
		hip_up_down_ratio = eight_upside_ratio * (1 - (8 - self.head_ratio) / 4) + four_upside_ratio * (8 - self.head_ratio) / 4
		#チェスト下とチェスト～首の割合
		upper_chest_neck_ratio = (1-(8-self.head_ratio)/4)*(1/3) + ((8-self.head_ratio)/4)*0.1

		#体幹 
		neck_len = (1-upper_chest_neck_ratio)*(self.tall*(1-hip_up_down_ratio)/2)/3
		upper_chest_len =  (self.tall*hip_up_down_ratio - head_size - neck_len)/3
		chest_len = upper_chest_len
		spine_len = chest_len
		
		Hips = bone_add("Hips", (0,0, self.tall*(1-hip_up_down_ratio) ), (0,0.1,self.tall*(1-hip_up_down_ratio)),root)
		Spine = bone_add("Spine",Hips.head,z_add(Hips.head,spine_len),Hips)
		Chest = bone_add("Chest", Spine.tail, z_add(Spine.tail,chest_len), Spine)
		upperChest = bone_add("upperChest", Chest.tail, z_add(Chest.tail,upper_chest_len), Chest)
		Neck = bone_add("Neck", upperChest.tail, z_add(upperChest.tail,neck_len), upperChest)
		Head = bone_add("Head", (0,0, self.tall-head_size), (0,0, self.tall), Neck)

		#目
		eye_depth = self.eye_depth
		eyes = x_mirror_bones_add("eye", (head_size / 5, 0, 		Head.head[2] + head_size / 2),
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

		arm_lengh = head_size * (1*(1-(self.head_ratio-6)/2)+1.5*((self.head_ratio-6)/2)) * self.arm_length_ratio
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

		def fingers(finger_name,proximal_pos,finger_len_sum):

			finger_normalize = 1/(self.finger_1_2_ratio*self.finger_2_3_ratio+self.finger_1_2_ratio+1)
			proximal_finger_len = finger_len_sum*finger_normalize
			intermediate_finger_len = finger_len_sum*finger_normalize*self.finger_1_2_ratio
			distal_finger_len = finger_len_sum*finger_normalize*self.finger_1_2_ratio*self.finger_2_3_ratio
			proximal_bones = x_mirror_bones_add(f"{finger_name}_proximal",proximal_pos,x_add(proximal_pos,proximal_finger_len),hands)
			intermediate_bones = x_mirror_bones_add(f"{finger_name}_intermidiate",proximal_bones[0].tail,x_add(proximal_bones[0].tail,intermediate_finger_len),proximal_bones)
			distal_bones = x_mirror_bones_add(f"{finger_name}_distal",intermediate_bones[0].tail,x_add(intermediate_bones[0].tail,distal_finger_len),intermediate_bones)
			return proximal_bones,intermediate_bones,distal_bones

		finger_y_offset = -hand_size/10
		thumbs = fingers(
			"finger_thumbs",
			y_add(hands[0].head,finger_y_offset - hand_size/5),
			hand_size/2
		)

		mats = [thumbs[0][i].matrix.translation for i in [0,1]]
		mats = [Matrix.Translation(mat) for mat in mats]
		for j in range(3):
			for n,angle in enumerate([-45,45]):
				thumbs[j][n].transform( mats[n].inverted() )
				thumbs[j][n].transform( Matrix.Rotation(radians(angle),4,"Z") )
				thumbs[j][n].transform( mats[n] )

		index_fingers = fingers(
			"finger_index",
			y_add(hands[0].tail,-hand_size/5 +finger_y_offset),
			(hand_size/2)-(1/2.3125)*(hand_size/2)/3
		)
		middle_fingers = fingers(
			"finger_middle",
			y_add(hands[0].tail,finger_y_offset),
			hand_size/2
		)
		ring_fingers = fingers(
			"finger_ring",
			y_add(hands[0].tail,hand_size/5 +finger_y_offset),
			(hand_size/2)-(1/2.3125)*(hand_size/2)/3
		)
		little_fingers = fingers(
			"finger_little",
			y_add(hands[0].tail,2*hand_size/5 +finger_y_offset),
			((hand_size/2)-(1/2.3125)*(hand_size/2)/3) * ((1/2.3125)+(1/2.3125)*0.75)
		)

		#'s is left,right tupple
		body_dict = {
			"hips":Hips.name,
			"spine":Spine.name,
			"chest":Chest.name,
			"upperChest":upperChest.name,
			"neck":Neck.name,
			"head":Head.name
		}
		left_right_body_dict = {
			f"{left_right}{bone_name}":bones[lr].name
			for bone_name,bones in {
				"Eye":eyes,
				"UpperLeg":upside_legs,
				"LowerLeg":lower_legs,
				"Foot":Foots,
				"Toes":Toes,
				"Shoulder":shoulders,
				"UpperArm":arms,
				"LowerArm":forearms,
				"Hand":hands
			}.items()
			for lr,left_right in enumerate(["left","right"])
		}

		#VRM finger like name key
		fingers_dict={
			f"{left_right}{finger_name}{position}":finger[i][lr].name
			for finger_name,finger in zip(["Thumb","Index","Middle","Ring","Little"],[thumbs,index_fingers,middle_fingers,ring_fingers,little_fingers])
			for i,position in enumerate(["Proximal","Intermediate","Distal"])
			for lr,left_right in enumerate(["left","right"])
		}

		#VRM bone name : blender bone name
		bone_name_all_dict = {}
		bone_name_all_dict.update(body_dict)
		bone_name_all_dict.update(left_right_body_dict)
		bone_name_all_dict.update(fingers_dict)

		context.scene.update()
		bpy.ops.object.mode_set(mode='OBJECT')
		return armature,bone_name_all_dict

	def setup_as_vrm(self,armature,compaire_dict):
		for vrm_bone_name,blender_bone_name in compaire_dict.items():
			armature.data.bones[blender_bone_name]["humanBone"] = vrm_bone_name

		def write_textblock_and_assgin_to_armature(block_name,value):
			text_block = bpy.data.texts.new(name=f"{armature.name}_{block_name}.json")
			text_block.write(json.dumps(value,indent = 4))
			armature[f"{block_name}"] = text_block.name
		write_textblock_and_assgin_to_armature("humanoid_params",{})
		write_textblock_and_assgin_to_armature("firstPerson_params",{})
		write_textblock_and_assgin_to_armature("blendshape_group",[])
		write_textblock_and_assgin_to_armature("spring_bone",[])

		return 