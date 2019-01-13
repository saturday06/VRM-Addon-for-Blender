"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""


import bpy, bmesh
from mathutils import Vector,Matrix
from .. import V_Types as VRM_Types
from math import sqrt,pow,radians
import numpy
import os.path
import json,copy

class Blend_model():
    def __init__(self,context,vrm_pydata,is_put_spring_bone_info):
        self.context = context
        self.textures = None
        self.armature = None
        self.bones = None
        self.material_dict = None
        self.primitive_obj_dict = None
        self.mesh_joined_objects = None
        model_name = vrm_pydata.json["extensions"]["VRM"]["meta"]["title"]
        self.model_collection = bpy.data.collections.new(f"{model_name}_collection")
        self.context.scene.collection.children.link(self.model_collection)
        self.vrm_model_build(vrm_pydata,is_put_spring_bone_info)


    def vrm_model_build(self,vrm_pydata,is_put_spring_bone_info):

        affected_object = self.scene_init()
        self.texture_load(vrm_pydata)
        self.make_armature(vrm_pydata)
        self.make_material(vrm_pydata)
        self.make_primitive_mesh_objects(vrm_pydata)
        self.json_dump(vrm_pydata)
        self.attach_vrm_attributes(vrm_pydata)
        self.cleaning_data()
        self.axis_transform()
        if is_put_spring_bone_info:
            self.put_spring_bone_info(vrm_pydata)
        self.finishing(affected_object)
        return 0

    def scene_init(self):
        # active_objectがhideだとbpy.ops.object.mode_set.poll()に失敗してエラーが出るのでその回避と、それを元に戻す
        affected_object = None
        if self.context.active_object != None:
            if hasattr(self.context.active_object, "hide_viewport"):
                if self.context.active_object.hide_viewport:
                    self.context.active_object.hide_viewport = False
                    affected_object = self.context.active_object
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action="DESELECT")
        return affected_object

    def finishing(self,affected_object):
        #initで弄ったやつを戻す
        if affected_object is not None:
            affected_object.hide_viewport = True
        return

        #image_path_to Texture
    def texture_load(self, vrm_pydata):
        self.textures = []
        for image_props in vrm_pydata.image_propaties:
            img = bpy.data.images.load(image_props.filePath)
            tex = bpy.data.textures.new(name = image_props.name,type="IMAGE")
            tex.image = img
            self.textures.append(tex)
        return
            
    def make_armature(self, vrm_pydata):
        #build bones as armature
        bpy.ops.object.add(type='ARMATURE', enter_editmode=True, location=(0,0,0))
        self.armature = self.context.object
        self.model_collection.objects.link(self.armature)
        self.armature.name = "skelton"
        self.armature.show_in_front = True
        self.armature.data.display_type = "STICK"
        self.bones = dict()
        def bone_chain(self_and_parent_id_tuple):
            id = self_and_parent_id_tuple[0]
            parent_id = self_and_parent_id_tuple[1]

            if id == -1:#自身がrootのrootの時
                pass
            else:
                py_bone = vrm_pydata.nodes_dict[id]
                print("pybone name is "+py_bone.name+" .")
                if py_bone.blend_bone:#すでにインスタンス化済みのボーンが出てきたとき。
                    li = [py_bone.blend_bone]
                    while li:
                        bo = li.pop()
                        if parent_id != -1:
                            bo.translate(self.bones[parent_id].head)
                            bo.parent = self.bones[parent_id]
                        for ch in bo.children:
                            li.append(ch)
                    return
                if py_bone.mesh_id is not None and py_bone.children is None:
                    return  #子がなく、mesh属性を持つnodeはboneを生成しない
                b = self.armature.data.edit_bones.new(py_bone.name)
                py_bone.name = b.name
                py_bone.blend_bone = b
                if parent_id == -1:
                    parent_pos = [0,0,0]
                else:
                    parent_pos = self.bones[parent_id].head
                b.head = numpy.array(parent_pos)+numpy.array(py_bone.position)
                #region temprary tail pos(gltf doesn't have bone. there defines as joints )
                def vector_length(bone_vector):
                    return sqrt(pow(bone_vector[0],2)+pow(bone_vector[1],2)+pow(bone_vector[2],2))
                #gltfは関節で定義されていて骨の長さとか向きとかないからまあなんかそれっぽい方向にボーンを向けて伸ばしたり縮めたり
                if py_bone.children == None:
                    if parent_id == -1:#唯我独尊：上向けとけ
                        b.tail = [b.head[0],b.head[1]+0.05,b.head[2]]
                    else:#normalize length to 0.03　末代：親から距離をちょっととる感じ
                        lengh = vector_length(py_bone.position)
                        lengh *= 30
                        if lengh <= 0.01:#0除算除けと気分
                            lengh =0.01
                        posDiff = [py_bone.position[i]/lengh for i in range(3)]
                        if posDiff == [0.0,0.0,0.0]:
                            posDiff[1] += 0.01 #ボーンの長さが0だとOBJECT MODEに戻った時にボーンが消えるので上向けとく
                        b.tail = [b.head[i]+posDiff[i] for i in range(3)]
                else:#子供たちの方向の中間を見る
                    mean_relate_pos = numpy.array([0.0,0.0,0.0],dtype=numpy.float)
                    count=0
                    for childID in py_bone.children:
                        count +=1
                        mean_relate_pos += vrm_pydata.nodes_dict[childID].position
                    mean_relate_pos = mean_relate_pos / count
                    if vector_length(mean_relate_pos) == 0:#子の位置の平均が根本と同じなら上向けとく
                        mean_relate_pos[1] +=0.1
                    b.tail =[b.head[i] + mean_relate_pos[i] for i in range(3)]

                #endregion tail pos    
                self.bones[id] = b

                if parent_id != -1:
                    b.parent = self.bones[parent_id]
                if py_bone.children != None:
                        for x in py_bone.children:
                            bone_nodes.append((x,id))
            return 0
        root_node_set = list(set(vrm_pydata.skins_root_node_list))
        root_nodes =  root_node_set if root_node_set else [node for scene in vrm_pydata.json["scenes"] for node in scene["nodes"]] 
        bone_nodes = [(root_node,-1) for root_node in root_nodes]
        while len(bone_nodes):
            bone_chain(bone_nodes.pop())
        #call when bone built
        self.context.scene.update()
        bpy.ops.object.mode_set(mode='OBJECT')
        try:
            for coll in self.armature.users_collection:
                if coll.name != self.model_collection.name:
                    coll.objects.unlink(self.armature)
        except:
            print("Master collection doesn't have armature obj")
            pass
        return
    
    #region material
    def make_material(self, vrm_pydata):
        #Material_datas　適当なので要調整
        self.material_dict = dict()
        for index,mat in enumerate(vrm_pydata.materials):
            b_mat = bpy.data.materials.new(mat.name)
            
            b_mat["shader_name"] = mat.shader_name
            if type(mat) == VRM_Types.Material_GLTF:
                self.build_material_from_GLTF(b_mat, mat)
            if type(mat) == VRM_Types.Material_MToon:
                self.build_material_from_MToon(b_mat, mat)
            if type(mat) == VRM_Types.Material_Transparent_Z_write:
                self.build_material_from_Transparent_Z_write
            
            self.material_dict[index] = b_mat
        return
    #region material_util func
    def set_material_transparent(self,b_mat, transparent_mode):
        if transparent_mode == "OPAQUE":
            b_mat.use_transparency = False
        elif transparent_mode == "Z_TRANSPARENCY":
            b_mat.use_transparency = True
            b_mat.alpha = 1
            b_mat.transparency_method = "Z_TRANSPARENCY"
        elif transparent_mode == "MASK":
            b_mat.use_transparency = True
            b_mat.alpha = 1
            b_mat.transparency_method = "MASK"
        return

    def texture_add(self,b_mat,b_texture,texture_param_dict,slot_param_dict):
        ts = b_mat.texture_slots.add()
        ts.texture = b_texture
        for attr,param in texture_param_dict.items():
            setattr(ts.texture,attr,param)
        for attr,param in slot_param_dict.items():
            setattr(ts,attr,param)
        return ts

    def texture_add_helper(self, b_mat, texture_id, mapping, uv_layer_num=0,
                            texture_param_dict = None, slot_param_dict=None):
        if texture_id == None:
            return
        b_texture = self.textures[texture_id]
        texture_param_dict = {} if texture_param_dict == None else texture_param_dict
        slot_param_dict = {} if slot_param_dict == None else slot_param_dict
        slot_param_dict.update({"texture_coords": mapping})
        if mapping == "UV":
            slot_param_dict.update({"uv_layer": f"TEXCOORD_{uv_layer_num}"})
        tex_slot = self.texture_add(b_mat, b_texture, texture_param_dict, slot_param_dict)
        return tex_slot

    def color_texture_add(self, b_mat, texture_index, uv_layer_index):
        self.texture_add_helper(
            b_mat, texture_index,
            "UV", uv_layer_index, None,
            {"use_map_alpha": True, "blend_type": "MULTIPLY"}
            )
    def normal_texture_add(self, b_mat, texture_index, uv_layer_index):
        self.texture_add_helper(
            b_mat, texture_index,
            "UV", uv_layer_index,
            {"use_normal_map": True},
            {"blend_type": "MIX",
            "use_map_color_diffuse":False,
            "use_map_normal": True})

    def un_affect_texture_add(self, b_mat, texture_index, uv_layer_index, role):
        ts = self.texture_add_helper(
            b_mat,texture_index,
            "UV", uv_layer_index,
            None,
            {"use_map_color_diffuse": False})
        if ts is not None:
            if "role" in ts.texture:
                print(f"{ts.texture.name} texture's role :{role}: is over written")             
            ts.texture["role"] = role


    def connect_value_node(self,material, value ,socket_to_connect):
        value_node = material.node_tree.nodes.new("ShaderNodeValue")
        value_node.label = socket_to_connect.name
        value_node.outputs[0].default_value = value
        material.node_tree.links.new(socket_to_connect,value_node.outputs[0])
        return value_node

    def connect_rgb_node(self, material ,color, socket_to_connect):
        rgb_node = material.node_tree.nodes.new("ShaderNodeRGB")
        rgb_node.label = socket_to_connect.name
        rgb_node.outputs[0].default_value = color
        material.node_tree.links.new(socket_to_connect,rgb_node.outputs[0])
        return rgb_node

    def connect_texture_node(self,material,tex_index,color_socket_to_connect = None,alpha_socket_to_connect = None):
        image_node = material.node_tree.nodes.new("ShaderNodeTexImage")
        image_node.image = self.textures[tex_index].image
        image_node.label = color_socket_to_connect.name
        if color_socket_to_connect:
            material.node_tree.links.new(color_socket_to_connect,image_node.outputs["Color"])
        if alpha_socket_to_connect:
            material.node_tree.links.new(alpha_socket_to_connect,image_node.outputs["Alpha"])
        return image_node

    def node_group_import(self,shader_node_group_name):
        if shader_node_group_name not in bpy.data.node_groups:
            filedir = os.path.join(os.path.dirname(os.path.dirname(__file__)),"resources","material_node_groups.blend","NodeTree")
            filepath = os.path.join(filedir,shader_node_group_name)
            bpy.ops.wm.append(filepath=filepath,filename=shader_node_group_name,directory=filedir)

    def node_group_create(self,material,shader_node_group_name):
        node_group = material.node_tree.nodes.new("ShaderNodeGroup")
        node_group.node_tree = bpy.data.node_groups[shader_node_group_name]
        return node_group

    def node_placer(self,parent_node):
        bottom_pos = [parent_node.location[0]-200, parent_node.location[1]]
        for child_node in [link.from_node for socket in parent_node.inputs for link in socket.links]:
            if child_node.type != "GROUP":
                child_node.hide = True
            child_node.location = bottom_pos
            bottom_pos[1] -= 40
            for ch_node in [link.from_node for socket in child_node.inputs for link in socket.links]:
                self.node_placer(child_node)
        return
    #endregion material_util func

    def build_material_from_GLTF(self, b_mat, pymat):
        b_mat.use_shadeless = pymat.shadeless
        b_mat.diffuse_color = pymat.base_color[0:3]
        self.set_material_transparent(b_mat, pymat.alphaMode)

        self.color_texture_add(
            b_mat, pymat.color_texture_index,
            pymat.color_texcoord_index)
        
        self.texture_add_helper(
            b_mat, pymat.normal_texture_index,
            pymat.normal_texture_texcoord_index)
        return

    def build_material_from_MToon(self, b_mat, pymat):
        shader_node_group_name = "MToon_unversioned"
        sphire_add_vector_node_group_name = "matcap_vector"
        self.node_group_import(shader_node_group_name)
        self.node_group_import(sphire_add_vector_node_group_name)

        b_mat.use_nodes = True
        b_mat.node_tree.nodes.remove(b_mat.node_tree.nodes["Principled BSDF"])
        sg = self.node_group_create(b_mat,shader_node_group_name)
        b_mat.node_tree.links.new(b_mat.node_tree.nodes["Material Output"].inputs['Surface'], sg.outputs["Emission"])
        
        float_prop_exchange_dic = VRM_Types.Material_MToon.float_props_exchange_dic
        for k, v in pymat.float_props_dic.items():
            if k in [key for key,val in float_prop_exchange_dic.items() if val is not None]:
                self.connect_value_node(b_mat, v ,sg.inputs[float_prop_exchange_dic[k]])
            else:
                b_mat[k] = v

        for k, v in pymat.keyword_dic.items():
            b_mat[k] = v

        vector_props_dic = VRM_Types.Material_MToon.vector_props_exchange_dic
        for k, v in pymat.vector_props_dic.items():
            if k in ["_Color","_ShadeColor","_EmissionColor","_OutlineColor"]:
                self.connect_rgb_node(b_mat,v,sg.inputs[vector_props_dic[k]])
            else:
                b_mat[k] = v

        tex_dic = VRM_Types.Material_MToon.texture_kind_exchange_dic
        for tex_name, tex_index in pymat.texture_index_dic.items():
            if tex_index is None:
                continue
            if not tex_name in tex_dic.keys():
                if "unknown_texture" in b_mat:
                    b_mat["unknown_texture"] = {}
                b_mat["unknown_texture"].update({tex_name:self.textures[tex_index].name})
                print(f"unknown texture {tex_name}")
            elif tex_name == "_MainTex":
                self.connect_texture_node(b_mat,tex_index, sg.inputs[tex_dic[tex_name]], sg.inputs[tex_dic[tex_name]+"Alpha"])
            elif tex_name == "_ReceiveShadowTexture":
                self.connect_texture_node(b_mat,tex_index,alpha_socket_to_connect = sg.inputs[tex_dic[tex_name]+"_alpha"])
            elif tex_name == "_SphereAdd":
                tex_node = self.connect_texture_node(b_mat,tex_index,color_socket_to_connect= sg.inputs[tex_dic[tex_name]])
                b_mat.node_tree.links.new(tex_node.inputs["Vector"],self.node_group_create(b_mat,sphire_add_vector_node_group_name).outputs["Vector"])
            else:
                self.connect_texture_node(b_mat,tex_index,color_socket_to_connect = sg.inputs[tex_dic[tex_name]])

        self.node_placer(b_mat.node_tree.nodes["Material Output"])

        transparant_exchange_dic = {0:"OPAQUE",1:"MASK",2:"Z_TRANSPARENCY",3:"Z_TRANSPARENCY"}#Trans_Zwrite(3)も2扱いで。
        if transparant_exchange_dic[pymat.float_props_dic["_BlendMode"]] != "OPAQUE":
            b_mat.blend_method = "HASHED"
        return

    def build_material_from_Transparent_Z_write(self, b_mat, pymat):
        for k, v in pymat.float_props_dic.items():
            b_mat[k] = v
        for tex_name, tex_index in pymat.texture_index_dic.items():
            if tex_name == "_MainTex":
                self.color_texture_add(b_mat, tex_index, 0)
        for k, v in pymat.vector_props_dic.items():
            if k == "_Color":
                b_mat.diffuse_color = v[0:3]
            else:
                b_mat[k] = v
        self.set_material_transparent(b_mat,"Z_TRANSPARENCY")          
        return                

    #endregion material


    def make_primitive_mesh_objects(self, vrm_pydata):
        self.primitive_obj_dict = {pymesh.object_id:[] for pymesh in vrm_pydata.meshes}
        morph_cache_dict = {} #key:tuple(POSITION,targets.POSITION),value:points_data
        #mesh_obj_build
        for pymesh in vrm_pydata.meshes:
            b_mesh = bpy.data.meshes.new(pymesh.name)
            b_mesh.from_pydata(pymesh.POSITION, [], pymesh.face_indices.tolist())
            b_mesh.update()
            obj = bpy.data.objects.new(pymesh.name, b_mesh)
            self.primitive_obj_dict[pymesh.object_id].append(obj)
            #kuso of kuso kakugosiro
            #origin 0:Vtype_Node 1:mesh 2:skin
            origin = None
            for key_is_node_id,node in vrm_pydata.origine_nodes_dict.items():
                if node[1] == pymesh.object_id:
                    obj.location = node[0].position #origin boneの場所に移動
                    if len(node) == 3:
                        origin = node
                    else:  #len=2 ≒ skinがない場合
                        parent_id = None
                        for id, py_node in vrm_pydata.nodes_dict.items():
                            if py_node.children is None:
                                continue
                            if key_is_node_id in py_node.children:
                                parent_id = id
                        obj.parent = self.armature
                        obj.parent_type = "BONE"
                        obj.parent_bone = self.armature.data.bones[vrm_pydata.nodes_dict[parent_id].name].name
                        #boneのtail側にparentされるので、根元からmesh nodeのpositionに動かしなおす
                        #obj.location = node[0].position
                        obj.matrix_world =  Matrix.Translation([self.armature.matrix_world.to_translation()[i]  \
                                            + self.armature.data.bones[obj.parent_bone].matrix_local.to_translation()[i] \
                                            + node[0].position[i] for i in range(3)] )

                        #obj.rotation_euler[2] = numpy.deg2rad(90)
                        #bpy.ops.object.transform_apply(rotation=True)
                        

            
            # vertex groupの作成
            if origin != None:
                nodes_index_list = vrm_pydata.skins_joints_list[origin[2]]
                # VertexGroupに頂点属性から一個ずつｳｪｲﾄを入れる用の辞書作り
                if hasattr(pymesh,"JOINTS_0") and hasattr(pymesh,"WEIGHTS_0"):
                    vg_dict = { #使うkey(bone名)のvalueを空のリストで初期化（中身まで全部内包表記で？キモすぎるからしない。
                        vrm_pydata.nodes_dict[nodes_index_list[joint_id]].name : list() 
                            for joint_id in [joint_id for joint_ids in pymesh.JOINTS_0 for joint_id in joint_ids]
                    }
                    for v_index,(joint_ids,weights) in enumerate(zip(pymesh.JOINTS_0,pymesh.WEIGHTS_0)):
                        for joint_id,weight in zip(joint_ids,weights):
                            node_id = nodes_index_list[joint_id]
                            vg_dict[vrm_pydata.nodes_dict[node_id].name].append([v_index,weight])
                    vg_list = [] # VertexGroupのリスト
                    for vg_key in vg_dict.keys():
                        obj.vertex_groups.new(name=vg_key)
                        vg_list.append(obj.vertex_groups[-1])
                    #頂点ﾘｽﾄに辞書から書き込む
                    for vg in vg_list:
                        weights = vg_dict[vg.name]
                        for w in weights:
                            if w[1] != 0.0:
                                #頂点はまとめてﾘｽﾄで追加できるようにしかなってない
                                vg.add([w[0]], w[1], 'REPLACE')
                obj.modifiers.new("amt","ARMATURE").object = self.armature

            #end of kuso
            scene = self.context.scene
            scene.collection.objects.link(obj)
            
            # uv
            flatten_vrm_mesh_vert_index = pymesh.face_indices.flatten()
            texcoord_num = 0
            while True:
                channnel_name = "TEXCOORD_" + str(texcoord_num)
                if hasattr(pymesh,channnel_name):
                    b_mesh.uv_layers.new(name=channnel_name)
                    blen_uv_data = b_mesh.uv_layers[channnel_name].data
                    vrm_texcoord  = getattr(pymesh,channnel_name)
                    for id,v_index in enumerate(flatten_vrm_mesh_vert_index):
                        blen_uv_data[id].uv = vrm_texcoord[v_index]
                        #blender axisnaize(上下反転)
                        blen_uv_data[id].uv[1] = blen_uv_data[id].uv[1] * -1 + 1
                    texcoord_num += 1
                else:
                    break

            #material適用
            obj.data.materials.append(self.material_dict[pymesh.material_index])
            
            #vertex_color　なぜかこれだけ面基準で、loose verts and edgesに色は塗れない
            #また、2.79では頂点カラーにalpha（４要素目）がないから完全対応は無理だったが
            #2.80では4要素になった模様
            #TODO: テスト (懸案：cleaningで頂点結合でデータ物故割れる説)
            vcolor_count = 0
            while True:
                vc_color_name = f"COLOR_{vcolor_count}"
                if hasattr(pymesh,vc_color_name):
                    vc = b_mesh.vertex_colors.new(name = vc_color_name)
                    for v_index,col in enumerate(vc.data):
                        vc.data[v_index].color = getattr(pymesh,vc_color_name)[flatten_vrm_mesh_vert_index[v_index]]
                    vcolor_count += 1
                else:
                    break

            #shapekey_data_factory with cache
            def absolutaize_morph_Positions(basePoints,morphTargetpos_and_index):
                shape_key_Positions = []
                morphTargetpos = morphTargetpos_and_index[0]
                morphTargetindex = morphTargetpos_and_index[1]

                #すでに変換したことがあるならそれを使う
                if (pymesh.POSITION_accessor,morphTargetindex) in morph_cache_dict.keys():
                    return morph_cache_dict[(pymesh.POSITION_accessor,morphTargetindex)]

                for basePos,morphPos in zip(basePoints,morphTargetpos):
                    #numpy.array毎回作るのは見た目きれいだけど8倍くらい遅い
                    shape_key_Positions.append([
                        basePos[0] + morphPos[0],
                        basePos[1] + morphPos[1],
                        basePos[2] + morphPos[2]
                    ])
                morph_cache_dict[(pymesh.POSITION_accessor,morphTargetindex)] = shape_key_Positions
                return shape_key_Positions
                
            #shapeKeys
            if hasattr(pymesh,"morphTarget_point_list_and_accessor_index_dict"):
                obj.shape_key_add(name = "Basis")
                for morphName,morphPos_and_index in pymesh.morphTarget_point_list_and_accessor_index_dict.items():
                    obj.shape_key_add(name = morphName)
                    keyblock = b_mesh.shape_keys.key_blocks[morphName]
                    shape_data = absolutaize_morph_Positions(pymesh.POSITION,morphPos_and_index)
                    for i,co in enumerate(shape_data):
                        keyblock.data[i].co = co

    def attach_vrm_attributes(self,vrm_pydata):
        VRM_extensions = vrm_pydata.json["extensions"]["VRM"]
        try:
            humanbones_relations = VRM_extensions["humanoid"]["humanBones"]
            for humanbone in humanbones_relations:
                self.armature.data.bones[vrm_pydata.json["nodes"][humanbone["node"]]["name"]]["humanBone"] = humanbone["bone"]
        except Exception as e:
            print(e)
            pass
        try:   
            for metatag,metainfo in VRM_extensions["meta"].items():
                if metatag == "texture":
                    self.armature[metatag] = self.textures[metainfo].image.name
                else:
                    self.armature[metatag] = metainfo
        except Exception as e:
            print(e)
            pass
            
        return

    def json_dump(self, vrm_pydata):
        vrm_ext_dic = vrm_pydata.json["extensions"]["VRM"]
        model_name = vrm_ext_dic["meta"]["title"]
        textblock = bpy.data.texts.new(name = f"{model_name}_raw.json")
        textblock.write(json.dumps(vrm_pydata.json,indent = 4))


        def write_textblock_and_assgin_to_armature(block_name,value):
            text_block = bpy.data.texts.new(name=f"{model_name}_{block_name}.json")
            text_block.write(json.dumps(value,indent = 4))
            self.armature[f"{block_name}"] = text_block.name
        
        #region humanoid_parameter
        humanoid_params = copy.deepcopy(vrm_ext_dic["humanoid"])
        del humanoid_params["humanBones"]
        write_textblock_and_assgin_to_armature("humanoid_params",humanoid_params)
        #endregion humanoid_parameter
        #region first_person
        firstperson_params = copy.deepcopy(vrm_ext_dic["firstPerson"])
        if firstperson_params["firstPersonBone"] != -1:
            firstperson_params["firstPersonBone"] = vrm_pydata.json["nodes"][firstperson_params["firstPersonBone"]]["name"]
        if "meshAnnotations" in firstperson_params.keys():
            for meshAnotation in firstperson_params["meshAnnotations"]:
                meshAnotation["mesh"] = vrm_pydata.json["meshes"][meshAnotation["mesh"]]["name"]

        write_textblock_and_assgin_to_armature("firstPerson_params",firstperson_params)
        #endregion first_person

        #region blendshape_master
        blendShapeGroups_list = copy.deepcopy(vrm_ext_dic["blendShapeMaster"]["blendShapeGroups"])
        #meshをidから名前に
        #weightを0-100から0-1に
        #shape_indexを名前に
        #materialValuesはそのままで行けるハズ・・・
        for bsg in blendShapeGroups_list:
            for bind_dic in bsg["binds"]:
                bind_dic["index"] = vrm_pydata.json["meshes"][bind_dic["mesh"]]["primitives"][0]["extras"]["targetNames"][bind_dic["index"]]
                bind_dic["mesh"] = self.primitive_obj_dict[bind_dic["mesh"]][0].name
                bind_dic["weight"] = bind_dic["weight"] / 100
        write_textblock_and_assgin_to_armature("blendshape_group",blendShapeGroups_list)
        #endregion blendshape_master

        #region springbone
        spring_bonegroup_list =copy.deepcopy(vrm_ext_dic["secondaryAnimation"]["boneGroups"])
        colliderGroups_list = vrm_ext_dic["secondaryAnimation"]["colliderGroups"]
        #node_idを管理するのは面倒なので、名前に置き換える
        #collider_groupも同じく
        for bone_group in spring_bonegroup_list:
            bone_group["bones"] = [ vrm_pydata.json["nodes"][node_id]["name"] for node_id in bone_group["bones"]]
            bone_group["colliderGroups"] = [vrm_pydata.json["nodes"][colliderGroups_list[collider_gp_id]["node"]]["name"] for collider_gp_id in bone_group["colliderGroups"]]
        write_textblock_and_assgin_to_armature("spring_bone",spring_bonegroup_list)
        #endregion springbone

        return

    def cleaning_data(self):
        #cleaning
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action="DESELECT")
        for objs in self.primitive_obj_dict.values():
            for obj in objs:
                obj.select_set(True)
                bpy.ops.object.shade_smooth()
                self.context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.delete_loose()
                bpy.ops.mesh.select_all()
                bpy.ops.mesh.remove_doubles(use_unselected= True)
                bpy.ops.object.mode_set(mode='OBJECT')
                obj.select_set(False)

        #join primitives
        self.mesh_joined_objects = []
        bpy.ops.object.select_all(action="DESELECT")
        for objs in self.primitive_obj_dict.values():
            self.context.view_layer.objects.active = objs[0]
            trash_mesh_names = [obj.data.name for obj in objs[1:]]
            for obj in objs:
                obj.select_set(True)
            bpy.ops.object.join()
            for unused_mesh in [mesh for mesh in bpy.data.meshes if mesh.name in trash_mesh_names]:
                bpy.data.meshes.remove(unused_mesh)
            self.mesh_joined_objects.append(self.context.active_object)
            self.model_collection.objects.link(self.context.active_object)
            self.context.scene.collection.objects.unlink(self.context.active_object)
            bpy.ops.object.select_all(action="DESELECT")
        return

    def axis_transform(self):
        #axis armature->>objの順でやらないと不具合
        bpy.ops.object.select_all(action="DESELECT")
        self.context.view_layer.objects.active = self.armature
        self.armature.select_set(True)
        self.armature.rotation_mode = "XYZ"
        self.armature.rotation_euler[0] = numpy.deg2rad(90)
        self.armature.rotation_euler[2] = numpy.deg2rad(-180)
        self.armature.location = [self.armature.location[axis]*inv for axis,inv in zip([0,2,1],[-1,1,1])]
        bpy.ops.object.transform_apply(location = True,rotation=True)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action="DESELECT")
        for obj in self.mesh_joined_objects:
            self.context.view_layer.objects.active = obj
            obj.select_set(True)
            if obj.parent_type == 'BONE':#ボーンにくっ付いて動くのは無視:なんか吹っ飛ぶ髪の毛がいる?
                bpy.ops.object.transform_apply(rotation=True)
                print(f"bone parent object {obj.name}")
                obj.select_set(False)
                continue
            obj.rotation_mode = "XYZ"
            obj.rotation_euler[0] = numpy.deg2rad(90)
            obj.rotation_euler[2] = numpy.deg2rad(-180)
            obj.location = [obj.location[axis]*inv for axis,inv in zip([0,2,1],[-1,1,1])]
            bpy.ops.object.transform_apply(location= True,rotation=True)
            obj.select_set(False)
        return
    
    def put_spring_bone_info(self,vrm_pydata):

        if not "secondaryAnimation" in vrm_pydata.json["extensions"]["VRM"]:
            print("no secondary animation object")
            return 
        secondaryAnimation_json = vrm_pydata.json["extensions"]["VRM"]["secondaryAnimation"]
        spring_rootbone_groups_json = secondaryAnimation_json["boneGroups"]
        collider_groups_json = secondaryAnimation_json["colliderGroups"]
        nodes_json = vrm_pydata.json["nodes"]
        for bone_group in spring_rootbone_groups_json:
            for bone_id in bone_group["bones"]:
                bone = self.armature.data.bones[nodes_json[bone_id]["name"]]
                for key, val in bone_group.items():
                    if key == "bones":
                        continue
                    bone[key] = val

        model_name = vrm_pydata.json["extensions"]["VRM"]["meta"]["title"]
        coll = bpy.data.collections.new(f"{model_name}_colliders")
        self.model_collection.children.link(coll)
        for collider_group in collider_groups_json:
            collider_base_node = nodes_json[collider_group["node"]]
            node_name = collider_base_node["name"]
            for i, collider in enumerate(collider_group["colliders"]):
                collider_name = f"{node_name}_collider_{i}"
                obj = bpy.data.objects.new(name = collider_name,object_data = None)
                obj.parent = self.armature
                obj.parent_type = "BONE"
                obj.parent_bone = node_name
                offset = [collider["offset"]["x"],collider["offset"]["y"],collider["offset"]["z"]] #values直接はindexｱｸｾｽ出来ないのでしゃあなし
                offset = [offset[axis]*inv for axis,inv in zip([0,2,1],[-1,-1,1])] #TODO: Y軸反転はuniVRMのシリアライズに合わせてる
                
                obj.matrix_world = self.armature.matrix_world @ Matrix.Translation(offset) @ self.armature.data.bones[node_name].matrix_local
                obj.empty_display_size = collider["radius"]  
                obj.empty_display_type = "SPHERE"
                coll.objects.link(obj)
                
        return 