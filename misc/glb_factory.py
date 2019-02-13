"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""
from .glb_bin_collector import Glb_bin_collection, Image_bin, Glb_bin
from ..gl_const import GL_CONSTANS
from .. import V_Types as VRM_types
from collections import OrderedDict
from math import pow
import json
import struct
from sys import float_info
import bpy,bmesh
class Glb_obj():
	def __init__(self):
		bpy.ops.vrm.model_validate()
		
		self.json_dic = OrderedDict()
		self.bin = b""
		self.glb_bin_collector = Glb_bin_collection()
		self.armature = [obj for obj in bpy.context.selected_objects if obj.type == "ARMATURE"][0]
		self.result = None

	def convert_bpy2glb(self):
		self.image_to_bin()
		self.armature_to_node_and_scenes_dic() #親のないboneは1つだけ as root_bone
		self.texture_to_dic() 
		self.material_to_dic()
		self.mesh_to_bin_and_dic() 
		self.json_dic["scene"] = 0
		self.glTF_meta_to_dic()
		self.vrm_meta_to_dic() #colliderとかmetaとか....
		self.finalize()
		return self.result
	@staticmethod
	def axis_blender_to_glb(vec3):
		return [vec3[i]*t for i,t in zip([0,2,1],[-1,1,1])]

	@staticmethod
	def textblock2str(textblock):
		return "".join([line.body for line in textblock.lines])

	def image_to_bin(self):
		#collect used image
		used_image = set()
		used_material_set = set()
		for mesh in [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]:
			for mat in mesh.data.materials:
				used_material_set.add(mat)

		shader_nodes = [(node.inputs["Surface"].links[0].from_node,mat) for mat in used_material_set \
                        for node in mat.node_tree.nodes \
                        if node.type =="OUTPUT_MATERIAL" \
                            and node.inputs['Surface'].links[0].from_node.type == "GROUP" \
                            and node.inputs["Surface"].links[0].from_node.node_tree.get("SHADER") is not None
                        ]
		#image fetching
		for node,mat in shader_nodes:
			if node.node_tree["SHADER"] == "MToon_unversioned":
				mat["vrm_shader"] = "MToon_unversioned"
				for shader_vals in VRM_types.Material_MToon.texture_kind_exchange_dic.values():
					if shader_vals is None:
						continue
					else:
						if shader_vals == "ReceiveShadow_Texture":
							if node.inputs[shader_vals+"_alpha"].links:
								n = node.inputs[shader_vals+"_alpha"].links[0].from_node
								used_image.add(n.image)	                           
						elif node.inputs[shader_vals].links:
							n = node.inputs[shader_vals].links[0].from_node
							used_image.add(n.image)
			elif node.node_tree["SHADER"] == "GLTF":
				texture_input_name_list = [
					"color_texture",
					"normal",
					"emissive_texture",
					"occlusion_texture"
				]
				for k in texture_input_name_list:
					if node.inputs[k].links:
						n = node.inputs[k].links[0].from_node
						used_image.add(n.image)
				mat["vrm_shader"] = "GLTF"
			elif node.node_tree["SHADER"] == "TRANSPARENT_ZWRITE":
				if node.inputs["Main_Texture"].links:
					n = node.inputs["Main_Texture"].links[0].from_node
					used_image.add(n.image)
				mat["vrm_shader"] = "TRANSPARENT_ZWRITE"
			else:
				#?
				pass
		#thumbnail
		used_image.add(bpy.data.images[self.armature["texture"]])

		for image in used_image:
			with open(image.filepath_from_user(),"rb") as f:
				image_bin = f.read()
			name = image.name
			filetype = "image/"+image.file_format.lower()
			Image_bin(image_bin,name,filetype,self.glb_bin_collector)
		return

	def armature_to_node_and_scenes_dic(self):
		nodes = []
		scene = []
		skins = []

		bone_id_dic = {b.name : bone_id for bone_id,b in enumerate(self.armature.data.bones)}
		def bone_to_node(b_bone):
			parent_head_local = b_bone.parent.head_local if b_bone.parent is not None else [0,0,0]
			node = OrderedDict({
				"name":b_bone.name,
				"translation":self.axis_blender_to_glb([b_bone.head_local[i] - parent_head_local[i] for i in range(3)]),
				#"rotation":[0,0,0,1],
				#"scale":[1,1,1],
				"children":[bone_id_dic[ch.name] for ch in b_bone.children]
			})
			if len(node["children"]) == 0:
				del node["children"]
			return node
		skin = {"joints":[]}
		for bone in self.armature.data.bones:
			if bone.parent is None: #root bone
				root_bone_id = bone_id_dic[bone.name]
				skin["joints"].append(root_bone_id)
				skin["skeleton"] = root_bone_id
				scene.append(root_bone_id)
				nodes.append(bone_to_node(bone))
				bone_children = [b for b in bone.children]
				while bone_children :
					child = bone_children.pop()
					nodes.append(bone_to_node(child))
					skin["joints"].append(bone_id_dic[child.name])
					bone_children += [ch for ch in child.children]
				nodes = sorted(nodes,key=lambda node: bone_id_dic[node["name"]])
		skins.append(skin)
					

		skin_invert_matrix_bin = b""
		f_4x4_packer = struct.Struct("<16f").pack
		for node_id in skins[0]["joints"]:
			bone_name = nodes[node_id]["name"]
			bone_glb_world_pos = self.axis_blender_to_glb(self.armature.data.bones[bone_name].head_local)
			inv_matrix = [
				1,0,0,0,
				0,1,0,0,
				0,0,1,0,
				-bone_glb_world_pos[0],-bone_glb_world_pos[1],-bone_glb_world_pos[2],1
			]
			skin_invert_matrix_bin += f_4x4_packer(*inv_matrix)

		IM_bin = Glb_bin(skin_invert_matrix_bin,"MAT4",GL_CONSTANS.FLOAT,len(skins[0]["joints"]),None,self.glb_bin_collector)
		skins[0]["inverseBindMatrices"] = IM_bin.accessor_id

		self.json_dic.update({"scenes":[{"nodes":scene}]})
		self.json_dic.update({"nodes":nodes})
		self.json_dic.update({"skins":skins})
		return 

	def texture_to_dic(self):
		self.json_dic["samplers"] = [{
            "magFilter": GL_CONSTANS.LINEAR,	#決め打ちなの？->gltf互換だとこれしかないからいいや
            "minFilter": GL_CONSTANS.LINEAR,	#決め打ちなの？->gltf互換だとこれしかないからいいや
            "wrapS": GL_CONSTANS.REPEAT ,		#TODO 決め打ちなの？ 10497 REPEAT と
            "wrapT": GL_CONSTANS.REPEAT 		#TODO 決め打ちなの？ 33071 CLAMP_TO_EDGE　があるから　そのうち・・・
        }]
		textures = []
		for id in range(len(self.glb_bin_collector.image_bins)):
			texture = {
				"sampler":0,
				"source": id
			}
			textures.append(texture)
		self.json_dic.update({"textures":textures})
		return

	def material_to_dic(self):
		glb_material_list = []
		VRM_material_props_list = []

		image_id_dic = {image.name:image.image_id for image in self.glb_bin_collector.image_bins}
		used_material_set = set()
		for mesh in [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]:
			for mat in mesh.data.materials:
				used_material_set.add(mat)

		#region function separate by shader
		def pbr_fallback(baseColor=(1,1,1,1),metallness=0,roughness=0.9,
				baseColor_texture_name=None,
				transparent_method="OPAQUE", transparency_cutoff=0.5,
				unlit = True):
			"""transparent_method = {"OPAQUE","MASK","BLEND"}"""
			fallback_dic = {"name":b_mat.name}
			fallback_dic["pbrMetallicRoughness"] = {
                "baseColorFactor":baseColor,
                "metallicFactor": metallness,
                "roughnessFactor": roughness
			}
			for k, v in fallback_dic["pbrMetallicRoughness"].items():
				if v is None:
					del fallback_dic["pbrMetallicRoughness"][k]

			if baseColor_texture_name:
				fallback_dic["pbrMetallicRoughness"].update({"baseColorTexture": {
						"index": image_id_dic[baseColor_texture_name],
						"texCoord": 0 #TODO:
						}})
			fallback_dic["alphaMode"] = transparent_method
			if transparent_method == "MASK":
				fallback_dic["alphaCutoff"] = transparency_cutoff
			if unlit:
				fallback_dic["extensions"] = {"KHR_materials_unlit":{}}
			return fallback_dic

		#region util func
		def get_texture_name(shader_node,input_socket_name):
			tex_name = None
			if shader_node.inputs.get(input_socket_name):
				if shader_node.inputs.get(input_socket_name).links:
					tex_name = shader_node.inputs.get(input_socket_name).links[0].from_node.image.name
			return tex_name
		def get_float_value(shader_node,input_socket_name):
			float_val = None
			if shader_node.inputs.get(input_socket_name):
				if shader_node.inputs.get(input_socket_name).links:
					float_val = shader_node.inputs.get(input_socket_name).links[0].from_node.outputs[0].default_value
				else:
					float_val = shader_node.inputs.get(input_socket_name).default_value
			return float_val
		def get_rgba_val(shader_node,input_socket_name):
			rgba_val = None
			if shader_node.inputs.get(input_socket_name):
				if shader_node.inputs.get(input_socket_name).links:
					rgba_val = [shader_node.inputs.get(input_socket_name).links[0].from_node.outputs[0].default_value[i] for i in range(4)]
				else:
					rgba_val = [shader_node.inputs.get(input_socket_name).default_value[i] for i in range(4)]		
			return rgba_val
		#endregion util func

		def make_MToon_unversioned_extension_dic(b_mat,MToon_Shader_Node):
			MToon_dic = OrderedDict()
			MToon_dic["name"] = b_mat.name
			MToon_dic["shader"] = "VRM/MToon"
			MToon_dic["keywordMap"] = keyword_map = {}
			MToon_dic["tagMap"] = tag_map = {}
			MToon_float_dic = MToon_dic["floatProperties"] = OrderedDict()
			MToon_vector_dic = MToon_dic["vectorProperties"] = OrderedDict()
			MToon_texture_dic = MToon_dic["textureProperties"] = OrderedDict()
			for float_key,float_prop in [(k,val) for k,val in VRM_types.Material_MToon.float_props_exchange_dic.items() if val ]:
				float_val = get_float_value(MToon_Shader_Node,float_prop)
				if float_val :
					MToon_float_dic[float_key] = float_val

			vec_prop_set = set(VRM_types.Material_MToon.vector_props_exchange_dic.values()) \
							 - set(VRM_types.Material_MToon.texture_kind_exchange_dic.values())
			for vector_key,vector_props in [(k,v) for k,v in VRM_types.Material_MToon.vector_props_exchange_dic.items() if v in vec_prop_set ]:
				vector_val = get_rgba_val(MToon_Shader_Node,vector_props)
				if vector_val:
					MToon_vector_dic[vector_key] = vector_val

			use_nomalmap = False
			maintex_name= None		
			for texture_key, texture_prop in VRM_types.Material_MToon.texture_kind_exchange_dic.items():
				tex_name = get_texture_name(MToon_Shader_Node,texture_prop)
				if tex_name:
					MToon_texture_dic[texture_key] = image_id_dic[tex_name]
					MToon_vector_dic[texture_key] = [0,0,1,1]
					if texture_prop == "MainTexture":
						maintex_name = tex_name
					elif texture_prop == "NomalmapTexture":
						use_nomalmap = True

			def material_prop_setter(blend_mode, \
									 src_blend, dst_blend, \
									 z_write, alphatest, \
									 render_queue, render_type):
				MToon_float_dic["_BlendMode"] = blend_mode
				MToon_float_dic["_SrcBlend"] = src_blend
				MToon_float_dic["_DstBlend"] = dst_blend
				MToon_float_dic["_ZWrite"] = z_write
				keyword_map.update({"_ALPHATEST_ON": alphatest})
				MToon_dic["renderQueue"] = render_queue
				tag_map["RenderType"] = render_type

			if b_mat.blend_method== "OPAQUE":
				material_prop_setter(0,1,0,1,False,-1,"Opaque")
			elif b_mat.blend_method == "CLIP":
				material_prop_setter(1,1,0,1,True,2450,"TransparentCutout")
				MToon_float_dic["_Cutoff"] = b_mat.alpha_threshold
			else:  #transparent and Z_TRANPARENCY or Raytrace
				material_prop_setter(3,5,10,1,True,3000,"Transparent")
			keyword_map.update({"_ALPHABLEND_ON": b_mat.blend_method not in ("OPAQUE","CLIP")})
			keyword_map.update({"_ALPHAPREMULTIPLY_ON":False})

			MToon_float_dic["_CullMode"] = 0 #no cull
			MToon_float_dic["_OutlineCullMode"] = 1 #front face cull (for invert normal outline)
			MToon_float_dic["_DebugMode"] = 0
			keyword_map.update({"MTOON_DEBUG_NORMAL":False})
			keyword_map.update({"MTOON_DEBUG_LITSHADERATE":False})
			keyword_map.update({"_NORMALMAP": use_nomalmap})

			#for pbr_fallback
			if b_mat.blend_method == "OPAQUE":
				transparent_method = "OPAQUE"
				transparency_cutoff = None
			elif b_mat.blend_method =="CLIP":
				transparent_method = "MASK"
				transparency_cutoff = b_mat.alpha_threshold
			else:
				transparent_method ="BLEND"
				transparency_cutoff = None
			pbr_dic = pbr_fallback(baseColor = MToon_vector_dic["_Color"],
									baseColor_texture_name = maintex_name,
									transparent_method = transparent_method,
									transparency_cutoff = transparency_cutoff)
			return MToon_dic,pbr_dic
		
		def make_GLTF_mat_dic(b_mat, GLTF_Shader_Node):		
			GLTF_dic = OrderedDict()
			GLTF_dic["name"] = b_mat.name
			GLTF_dic["shader"] = "VRM_USE_GLTFSHADER"
			GLTF_dic["keywordMap"] =  {}
			GLTF_dic["tagMap"] = {}
			GLTF_dic["floatProperties"] = {}
			GLTF_dic["vectorProperties"] = {}
			GLTF_dic["textureProperties"] = {}

			if b_mat.blend_method == "OPAQUE":
				transparent_method = "OPAQUE"
				transparency_cutoff = None
			elif b_mat.blend_method =="CLIP":
				transparent_method = "MASK"
				transparency_cutoff = b_mat.alpha_threshold
			else:
				transparent_method ="BLEND"
				transparency_cutoff = None
		
			pbr_dic = pbr_fallback(
				baseColor=get_rgba_val(GLTF_Shader_Node, "base_Color"),
				metallness=get_float_value(GLTF_Shader_Node, "metallic"),
				roughness=get_float_value(GLTF_Shader_Node, "roughness"),
				baseColor_texture_name=get_texture_name(GLTF_Shader_Node,"color_texture"),
				transparent_method=transparent_method,
				transparency_cutoff=transparency_cutoff,
				unlit=True if get_float_value(GLTF_Shader_Node,"unlit") >=0.5 else False
			)
			def pbr_tex_add(texture_type, socket_name):
				image_name = get_texture_name(GLTF_Shader_Node,socket_name)
				if image_name is not None:
					image_id = image_id_dic.get(image_name)
					if image_id is not None:
						pbr_dic[texture_type] = {
							"index":image_id,
							"texCoord":0
						}
			pbr_tex_add("normalTexture", "normal")
			pbr_tex_add("emissiveTexture","emissive_texture")
			pbr_tex_add("occlusionTexture", "occlusion_texture")
			pbr_dic["emissiveFactor"] = get_rgba_val(GLTF_Shader_Node,"emissive_color")[0:3]
					
			return GLTF_dic, pbr_dic
		
		def make_TRNSZW_mat_dic(b_mat, TRANSZW_Shader_Node):
			ZW_dic = OrderedDict()
			ZW_dic["name"] = b_mat.name
			ZW_dic["shader"] = "VRM/UnlitTransparentZWrite"
			ZW_dic["renderQueue"] = 2600
			ZW_dic["keywordMap"] =  {}
			ZW_dic["tagMap"] = {"RenderType": "Transparent"}
			ZW_dic["floatProperties"] = {}
			ZW_dic["vectorProperties"] = {}
			ZW_dic["textureProperties"] = {}			
			color_tex = get_texture_name(TRANSZW_Shader_Node, "Main_Texture")
			if color_tex is not None:
				ZW_dic["textureProperties"] = {"_MainTex": image_id_dic[color_tex]}
				ZW_dic["vectorProperties"] = {"_MainTex":[0,0,1,1]}
			pbr_dic = pbr_fallback(baseColor_texture_name=color_tex,transparent_method="BLEND")

			return ZW_dic,pbr_dic
		#endregion function separate by shader


		for b_mat in used_material_set:
			
			if b_mat["vrm_shader"] == "MToon_unversioned":
				for node in b_mat.node_tree.nodes:
					if node.type == "OUTPUT_MATERIAL":
						MToon_shader_node = node.inputs["Surface"].links[0].from_node
						break
				materialPropaties_dic,pbr_dic = make_MToon_unversioned_extension_dic(b_mat,MToon_shader_node)
			elif b_mat["vrm_shader"] == "GLTF":
				for node in b_mat.node_tree.nodes:
					if node.type == "OUTPUT_MATERIAL":
						GLTF_shader_node = node.inputs["Surface"].links[0].from_node
						break
				materialPropaties_dic,pbr_dic = make_GLTF_mat_dic(b_mat,GLTF_shader_node)				 
			elif b_mat["vrm_shader"] == "TRANSPARENT_ZWRITE":
				for node in b_mat.node_tree.nodes:
					if node.type == "OUTPUT_MATERIAL":
						ZW_shader_node = node.inputs["Surface"].links[0].from_node
						break
				materialPropaties_dic,pbr_dic = make_TRNSZW_mat_dic(b_mat,ZW_shader_node)	 
			else:
				print("please use vrm_shader")
				raise Exception  #?
			
			glb_material_list.append(pbr_dic)
			VRM_material_props_list.append(materialPropaties_dic)
			
		self.json_dic.update({"materials" : glb_material_list})
		self.json_dic.update({"extensions":{"VRM":{"materialProperties":VRM_material_props_list}}})
		return

	def mesh_to_bin_and_dic(self):
		self.json_dic["meshes"] = []
		for id,mesh in enumerate([obj for obj in bpy.context.selected_objects if obj.type == "MESH"]):
			is_skin_mesh = True
			if len([m for m in mesh.modifiers if m.type == "ARMATURE"]) == 0:
				if mesh.parent is not None:
					if mesh.parent.type == "ARMATURE":
						if mesh.parent_bone != None:
							is_skin_mesh = False
			node_dic = OrderedDict({
					"name":mesh.name,
					"translation":self.axis_blender_to_glb(mesh.location), #原点にいてほしいけどね, vectorのままだとjsonに出来ないからこうする
					"rotation":[0,0,0,1],	#このへんは規約なので
					"scale":[1,1,1],		#このへんは規約なので
					"mesh":id,
				})
			if is_skin_mesh:
				node_dic["skin"] = 0 #TODO:　決め打ちってどうよ：一体のモデルなのだから２つもあっては困る(から決め打ち(やめろ(やだ))
			self.json_dic["nodes"].append(node_dic)
			
			mesh_node_id = len(self.json_dic["nodes"])-1

			if is_skin_mesh:
				self.json_dic["scenes"][0]["nodes"].append(mesh_node_id)
			else:
				parent_node = [node for node in self.json_dic["nodes"] if node["name"] == mesh.parent_bone ][0]
				if "children" in parent_node.keys():
					parent_node["children"].append(mesh_node_id)
				else:
					parent_node["children"] = [mesh_node_id]
				relate_pos = [mesh.location[i] - self.armature.data.bones[mesh.parent_bone].head_local[i] for i in range(3)]
				self.json_dic["nodes"][mesh_node_id]["translation"] = self.axis_blender_to_glb(relate_pos)

			#region hell
			bpy.ops.object.mode_set(mode='OBJECT')
			mesh.hide_viewport = False
			mesh.hide_select = False
			bpy.context.view_layer.objects.active = mesh
			bpy.ops.object.mode_set(mode='EDIT')
			bm = bmesh.from_edit_mesh(mesh.data)

			#region tempolary_used
			mat_id_dic = {mat["name"]:i for i,mat in enumerate(self.json_dic["materials"])} 
			material_slot_dic = {i:mat.name for i,mat in enumerate(mesh.material_slots)} 
			node_id_dic = {node["name"]:i for i,node in enumerate(self.json_dic["nodes"])} 
			def joint_id_from_node_name_solver(node_name):
				try:
					node_id = node_id_dic[node_name]
					joint_id = self.json_dic["skins"][0]["joints"].index(node_id)
				except ValueError:
					joint_id = -1 #存在しないボーンを指してる場合は-1を返す
					print("{} bone may be not exist".format(node_name))
				return joint_id
			v_group_name_dic = {i:vg.name for i,vg in enumerate(mesh.vertex_groups)}
			fmin,fmax = float_info.min,float_info.max
			unique_vertex_id = 0
			unique_vertex_id_dic = {} #loop verts id : base vertex id (uv違いを同じ頂点番号で管理されているので)
			unique_vertex_dic = {} # {(uv...,vertex_index):unique_vertex_id} (uvと頂点番号が同じ頂点は同じものとして省くようにする)
			uvlayers_dic = {i:uvlayer.name for i,uvlayer in enumerate(mesh.data.uv_layers)}
			def fetch_morph_vertex_normal_difference(): #TODO 実装
				morph_normal_diff_dic = {}
				vert_base_normal_dic = OrderedDict()
				for kb in mesh.data.shape_keys.key_blocks:
					vert_base_normal_dic.update( {kb.name:kb.normals_vertex_get()})
				for k,v in vert_base_normal_dic.items():
					if k == "Basis":
						continue
					values = []
					for vert_morph_normal,vert_base_normal in zip(zip(*[iter(v)]*3),zip(*[iter(vert_base_normal_dic["Basis"])]*3)):
						values.append([vert_morph_normal[i]- vert_base_normal[i] for i in range(3)])
					morph_normal_diff_dic.update({k:values})
				return morph_normal_diff_dic
			#endregion  tempolary_used
			primitive_index_bin_dic = OrderedDict({mat_id_dic[mat.name]:b"" for mat in mesh.material_slots})
			primitive_index_vertex_count = OrderedDict({mat_id_dic[mat.name]:0 for mat in mesh.material_slots})
			if mesh.data.shape_keys is None : 
				shape_pos_bin_dic = {}
				shape_normal_bin_dic = {}
				shape_min_max_dic = {}
				morph_normal_diff_dic = {}
			else:
				shape_pos_bin_dic = OrderedDict({shape.name:b"" for shape in mesh.data.shape_keys.key_blocks[1:]})#0番目Basisは省く
				shape_normal_bin_dic = OrderedDict({shape.name:b"" for shape in mesh.data.shape_keys.key_blocks[1:]})
				shape_min_max_dic = OrderedDict({shape.name:[[fmax,fmax,fmax],[fmin,fmin,fmin]] for shape in mesh.data.shape_keys.key_blocks[1:]})
				morph_normal_diff_dic = fetch_morph_vertex_normal_difference() #{morphname:{vertexid:[diff_X,diff_y,diff_z]}}
			position_bin =b""
			position_min_max = [[fmax,fmax,fmax],[fmin,fmin,fmin]]
			normal_bin = b""
			joints_bin = b""
			weights_bin = b""
			texcord_bins = {id:b"" for id in uvlayers_dic.keys()}
			f_vec4_packer = struct.Struct("<ffff").pack
			f_vec3_packer = struct.Struct("<fff").pack
			f_pair_packer = struct.Struct("<ff").pack
			I_scalar_packer = struct.Struct("<I").pack
			H_vec4_packer = struct.Struct("<HHHH").pack

			def min_max(minmax,position):
				for i in range(3):
					minmax[0][i] = position[i] if position[i] < minmax[0][i] else minmax[0][i]
					minmax[1][i] = position[i] if position[i] > minmax[1][i] else minmax[1][i]
				return
			for face in bm.faces:
				#このへん絶対超遅い
				for loop in face.loops:
					uv_list = []
					for uvlayer_name in uvlayers_dic.values():
						uv_layer = bm.loops.layers.uv[uvlayer_name]
						uv_list += [loop[uv_layer].uv[0],loop[uv_layer].uv[1]]
					cached_vert_id = unique_vertex_dic.get((*uv_list,loop.vert.index)) #keyがなければNoneを返す
					if cached_vert_id is not None:
						primitive_index_bin_dic[mat_id_dic[material_slot_dic[face.material_index]]] += I_scalar_packer(cached_vert_id)
						primitive_index_vertex_count[mat_id_dic[material_slot_dic[face.material_index]]] += 1
						continue
					else: 
						unique_vertex_dic[(*uv_list,loop.vert.index)] = unique_vertex_id
					for id,uvlayer_name in uvlayers_dic.items():
						uv_layer = bm.loops.layers.uv[uvlayer_name]
						uv = loop[uv_layer].uv
						texcord_bins[id] += f_pair_packer(uv[0],-uv[1]) #blenderとglbのuvは上下逆
					for shape_name in shape_pos_bin_dic.keys(): 
						shape_layer = bm.verts.layers.shape[shape_name]
						morph_pos = self.axis_blender_to_glb( [loop.vert[shape_layer][i] - loop.vert.co[i] for i in range(3)])
						shape_pos_bin_dic[shape_name] += f_vec3_packer(*morph_pos)
						shape_normal_bin_dic[shape_name] +=f_vec3_packer(*self.axis_blender_to_glb(morph_normal_diff_dic[shape_name][loop.vert.index]))
						min_max(shape_min_max_dic[shape_name],morph_pos)
					if is_skin_mesh:			
						magic = 0
						joints = [magic,magic,magic,magic]
						weights = [0.0, 0.0, 0.0, 0.0]
						if len(mesh.data.vertices[loop.vert.index].groups) >= 5:
							print("vertex weights are less than 4 in {}".format(mesh.name))
							raise Exception
						for v_group in mesh.data.vertices[loop.vert.index].groups:
							joint_id = joint_id_from_node_name_solver(v_group_name_dic[v_group.group])
							if joint_id == -1:#存在しないボーンを指してる場合は-1を返されてるので、その場合は飛ばす
								continue			
							weights.pop(3)
							weights.insert(0,v_group.weight)
							joints.pop(3)
							joints.insert(0,joint_id)
						nomalize_fact = sum(weights)
						try:
							weights = [weights[i]/nomalize_fact for i in range(4)]
						except ZeroDivisionError :
							print("vertex has no weight in {}".format(mesh.name)) 
							raise ZeroDivisionError
						if sum(weights) < 1:
							weights[0] += 1 - sum(weights)
						joints_bin += H_vec4_packer(*joints)
						weights_bin += f_vec4_packer(*weights) 

					vert_location = self.axis_blender_to_glb(loop.vert.co)
					position_bin += f_vec3_packer(*vert_location)
					min_max(position_min_max,vert_location)
					normal_bin += f_vec3_packer(*self.axis_blender_to_glb(loop.vert.normal))
					unique_vertex_id_dic[unique_vertex_id]=loop.vert.index
					primitive_index_bin_dic[mat_id_dic[material_slot_dic[face.material_index]]] += I_scalar_packer(unique_vertex_id)
					primitive_index_vertex_count[mat_id_dic[material_slot_dic[face.material_index]]] += 1
					unique_vertex_id += 1
				
			#DONE :index position, uv, normal, position morph,JOINT WEIGHT  
			#TODO: morph_normal, v_color...?
			primitive_glbs_dic = OrderedDict({
				mat_id:Glb_bin(index_bin,"SCALAR",GL_CONSTANS.UNSIGNED_INT,primitive_index_vertex_count[mat_id],None,self.glb_bin_collector)
				for mat_id,index_bin in primitive_index_bin_dic.items() if index_bin !=b""
			})
			pos_glb = Glb_bin(position_bin,"VEC3",GL_CONSTANS.FLOAT,unique_vertex_id,position_min_max,self.glb_bin_collector)
			nor_glb = Glb_bin(normal_bin,"VEC3",GL_CONSTANS.FLOAT,unique_vertex_id,None,self.glb_bin_collector)
			uv_glbs = [
				Glb_bin(texcood_bin,"VEC2",GL_CONSTANS.FLOAT,unique_vertex_id,None,self.glb_bin_collector)
					for texcood_bin in texcord_bins.values()]
			if is_skin_mesh:
				joints_glb = Glb_bin(joints_bin,"VEC4",GL_CONSTANS.UNSIGNED_SHORT,unique_vertex_id,None,self.glb_bin_collector)
				weights_glb = Glb_bin(weights_bin,"VEC4",GL_CONSTANS.FLOAT,unique_vertex_id,None,self.glb_bin_collector)
			if len(shape_pos_bin_dic.keys()) != 0:
				morph_pos_glbs = [Glb_bin(morph_pos_bin,"VEC3",GL_CONSTANS.FLOAT,unique_vertex_id,morph_minmax,self.glb_bin_collector) 
						for morph_pos_bin,morph_minmax in zip(shape_pos_bin_dic.values(),shape_min_max_dic.values())
						]
				morph_normal_glbs = [Glb_bin(morph_normal_bin,"VEC3",GL_CONSTANS.FLOAT,unique_vertex_id,None,self.glb_bin_collector) 
						for morph_normal_bin in shape_normal_bin_dic.values()
						] 
			primitive_list = []
			for primitive_id,index_glb in primitive_glbs_dic.items():
				primitive = OrderedDict({"mode":4})
				primitive["material"] = primitive_id
				primitive["indices"] = index_glb.accessor_id
				primitive["attributes"] = {
					"POSITION":pos_glb.accessor_id,
					"NORMAL":nor_glb.accessor_id,
				}
				if is_skin_mesh:
					primitive["attributes"].update({
						"JOINTS_0":joints_glb.accessor_id,
						"WEIGHTS_0":weights_glb.accessor_id
					})
				primitive["attributes"].update({"TEXCOORD_{}".format(i):uv_glb.accessor_id for i,uv_glb in enumerate(uv_glbs)})
				if len(shape_pos_bin_dic.keys()) != 0:
					primitive["targets"]=[{"POSITION":morph_pos_glb.accessor_id,"NORMAL":morph_normal_glb.accessor_id} for morph_pos_glb,morph_normal_glb in zip(morph_pos_glbs,morph_normal_glbs)]
					primitive["extras"] = {"targetNames":[shape_name for shape_name in shape_pos_bin_dic.keys()]} 
				primitive_list.append(primitive)
			self.json_dic["meshes"].append(OrderedDict({"name":mesh.name,"primitives":primitive_list}))
			#endregion hell
		bpy.ops.object.mode_set(mode='OBJECT')
			
		return

	exporter_name = "icyp_blender_vrm_exporter_experimental_0.0"
	def glTF_meta_to_dic(self):
		glTF_meta_dic = {
			"extensionsUsed":["VRM","KHR_materials_unlit"],
			"asset":{
				"generator":self.exporter_name,
				"version":"2.0" #GLTF version
				}
			}

		self.json_dic.update(glTF_meta_dic)
		return

	def vrm_meta_to_dic(self):
		#materialProperties　は　material_to_dic()で処理する
		#region vrm_extension
		vrm_extension_dic = OrderedDict()
		vrm_extension_dic["exporterVersion"] = self.exporter_name
		vrm_extension_dic["specVersion"] = "0.0"
		#region meta
		vrm_extension_dic["meta"] = vrm_meta_dic = {}
		#安全側に寄せておく
		required_vrm_metas = {
			"allowedUserName":"Disallow",
			"violentUssageName":"Disallow",
			"sexualUssageName":"Disallow",
			"commercialUssageName":"Disallow",
			"licenseName":"Redistribution_Prohibited",
		}
		vrm_metas = [
			"version",#model version (not VRMspec etc)
			"author",
			"contactInformation",
			"reference",
			"title",
			"otherPermissionUrl",
			"otherLicenseUrl"
		]
		for k, v in required_vrm_metas.items():
			vrm_meta_dic[k] = self.armature[k] if k in self.armature.keys() else v
		for key in vrm_metas:
			vrm_meta_dic[key] = self.armature[key] if key in self.armature.keys() else ""

		if "texture" in self.armature.keys():
			thumbnail_index_list =[i for i,img in enumerate(self.glb_bin_collector.image_bins) if img.name == self.armature["texture"]]
			if len(thumbnail_index_list) > 0 :
				vrm_meta_dic["texture"] = thumbnail_index_list[0]
		#endregion meta
		#region humanoid
		vrm_extension_dic["humanoid"] = vrm_humanoid_dic = {"humanBones":[]}
		node_name_id_dic = {node["name"]:i for i, node in enumerate(self.json_dic["nodes"])}
		for bone in self.armature.data.bones:
			if "humanBone" in bone.keys():
				vrm_humanoid_dic["humanBones"].append({ 
					"bone": bone["humanBone"],
					"node":node_name_id_dic[bone.name],
					"useDefaultValues": True
				})
		vrm_humanoid_dic.update(json.loads(self.textblock2str(bpy.data.texts[self.armature["humanoid_params"]])))
		#endregion humanoid
		#region firstPerson
		vrm_extension_dic["firstPerson"] = vrm_FP_dic = {}
		vrm_FP_dic.update(json.loads(self.textblock2str(bpy.data.texts[self.armature["firstPerson_params"]])))
		if vrm_FP_dic["firstPersonBone"] != -1:
			vrm_FP_dic["firstPersonBone"] = node_name_id_dic[vrm_FP_dic["firstPersonBone"]]
		if "meshAnnotations" in vrm_FP_dic.keys():
			for meshAnnotation in vrm_FP_dic["meshAnnotations"]:
				meshAnnotation["mesh"] = [i for i,mesh in enumerate(self.json_dic["meshes"]) if mesh["name"]==meshAnnotation["mesh"]][0]

		#endregion firstPerson
		#region blendShapeMaster
		vrm_extension_dic["blendShapeMaster"] = vrm_BSM_dic = {}
		BSM_list = json.loads(self.textblock2str(bpy.data.texts[self.armature["blendshape_group"]]))
		#meshを名前からid
        #weightを0-1から0-100に
        #shape_indexを名前からindexに
		def clamp(min,val,max):
			if max >= val:
				if val >= min:return val
				else:
					print("blendshapeGroup weight is between 0 - 1, value is {}".format(val))
					return min
			else:
				print("blendshapeGroup weight is between 0 - 1, value is {}".format(val))
				return max
		for bsm in BSM_list:
			for bind in bsm["binds"]:
				bind["mesh"] = [i for i,mesh in enumerate(self.json_dic["meshes"]) if mesh["name"]==bind["mesh"]][0]
				bind["index"] = self.json_dic["meshes"][bind["mesh"]]["primitives"][0]["extras"]["targetNames"].index(bind["index"])
				bind["weight"] = clamp(0, bind["weight"]*100, 100)
		vrm_BSM_dic["blendShapeGroups"] = BSM_list
		#endregion blendShapeMaster

		#region secondaryAnimation
		vrm_extension_dic["secondaryAnimation"] = {"boneGroups":[],"colliderGroups":[]}

		#region colliderGroups
		#armatureの子emptyを変換する
		collider_group_list = []
		empty_dic = {node_name_id_dic[ch.parent_bone]:[] for ch in self.armature.children if ch.type == "EMPTY"}
		for childEmpty in [ch for ch in self.armature.children if ch.type == "EMPTY"]:
			empty_dic[node_name_id_dic[childEmpty.parent_bone]].append(childEmpty)
		for node_id,empty_objs in empty_dic.items():
			collider_group = {"node":node_id,"colliders":[]}
			colliders = collider_group["colliders"]
			for empty in empty_objs:
				collider = {"radius":empty.empty_display_size}
				empty_offset_pos = [empty.matrix_world.to_translation()[i] \
									- self.armature.location[i] \
									- self.armature.data.bones[empty.parent_bone].head_local[i] \
									for i in range(3)]
				collider["offset"] = OrderedDict({axis: o_s for axis, o_s in zip(("x", "y", "z"), self.axis_blender_to_glb(empty_offset_pos))})
				collider["offset"]["z"] = collider["offset"]["z"]*-1 #TODO: たぶんuniVRMのシリアライズがｺﾗｲﾀﾞｰだけunity系になってる
				colliders.append(collider)
			collider_group_list.append(collider_group)

		vrm_extension_dic["secondaryAnimation"]["colliderGroups"] = collider_group_list
		#endrigon colliderGroups

		#region boneGroup
		#ﾎﾞｰﾝ名からnode_idに
        #collider_groupも名前からcolliderGroupのindexに直す
		collider_node_id_list = [c_g["node"] for c_g in collider_group_list]
		BG_list = json.loads(self.textblock2str(bpy.data.texts[self.armature["spring_bone"]]))
		for bone_group in BG_list:
			bone_group["bones"] = [node_name_id_dic[name] for name in bone_group["bones"] ]
			bone_group["colliderGroups"] = [collider_node_id_list.index(node_name_id_dic[name]) for name in bone_group["colliderGroups"] ]
		vrm_extension_dic["secondaryAnimation"]["boneGroups"]= BG_list
		#endregion boneGroup
		#endregion secondaryAnimation
		self.json_dic["extensions"]["VRM"].update(vrm_extension_dic)
		#endregion vrm_extension
		
		#region secondary 
		self.json_dic["nodes"].append({
			"name":"secondary",
			"translation":[0.0,0.0,0.0],
			"rotation":[0.0,0.0,0.0,1.0],
			"scale":[1.0,1.0,1.0]
		})
		self.json_dic["scenes"][0]["nodes"].append(len(self.json_dic["nodes"])-1)
		return


	def finalize(self):
		bin_json, self.bin = self.glb_bin_collector.pack_all()
		self.json_dic.update(bin_json)
		magic = b'glTF' + struct.pack('<I', 2)
		json_str = json.dumps(self.json_dic).encode("utf-8")
		if len(json_str)%4 !=0:
			for i in range(4 - len(json_str)%4):
				json_str += b"\x20"
		json_size = struct.pack("<I", len(json_str))
		if len(self.bin)%4 !=0:
			for i in range(4-len(self.bin)%4):
				self.bin += b"\x00"
		bin_size = struct.pack("<I",len(self.bin))
		total_size = struct.pack("<I",len(json_str) + len(self.bin)+28) #include header size
		self.result = magic + total_size + \
				json_size + b"JSON" + json_str + \
				bin_size + b'BIN\x00' + self.bin
		return

