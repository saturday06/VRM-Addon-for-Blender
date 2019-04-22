"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""
import bpy,blf
import bmesh
from .. import V_Types as VRM_types
from ..V_Types import nested_json_value_getter as json_get
import re
from math import sqrt, pow
from mathutils import Vector
from collections import deque
class Bones_rename(bpy.types.Operator):
    bl_idname = "vrm.bones_rename"
    bl_label = "Rename Vroid_bones"
    bl_description = "Rename Vroid_bones as Blender type"
    bl_options = {'REGISTER', 'UNDO'}
    
    
    def execute(self, context):
        for x in bpy.context.active_object.data.bones:
            for RL in ["L","R"]:
                ma = re.match("(.*)_"+RL+"_(.*)",x.name)
                if ma:
                    tmp = ""
                    for y in ma.groups():
                        tmp += y + "_"
                    tmp += RL
                    x.name = tmp
        return {"FINISHED"}


import json
from collections import OrderedDict
import os

class Vroid2VRC_ripsync_from_json_recipe(bpy.types.Operator):
    bl_idname = "vrm.ripsync_vrm"
    bl_label = "Make ripsync4VRC"
    bl_description = "Make ripsync from Vroid to VRC by json"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        recipe_uri =os.path.join(os.path.dirname(__file__) ,"Vroid2vrc_ripsync_recipe.json")
        recipe = None
        with open(recipe_uri,"rt") as raw_recipe:
            recipe = json.loads(raw_recipe.read(),object_pairs_hook=OrderedDict)
        for shapekey_name,based_values in recipe["shapekeys"].items():
            for k in bpy.context.active_object.data.shape_keys.key_blocks:
                k.value = 0.0
            for based_shapekey_name,based_val in based_values.items():
                #if M_F00_000+_00
                if not based_shapekey_name in bpy.context.active_object.data.shape_keys.key_blocks:
                    based_shapekey_name = based_shapekey_name.replace("M_F00_000","M_F00_000_00")#Vroid064から命名が変わった
                bpy.context.active_object.data.shape_keys.key_blocks[based_shapekey_name].value = based_val
            bpy.ops.object.shape_key_add(from_mix = True)
            bpy.context.active_object.data.shape_keys.key_blocks[-1].name = shapekey_name
        for k in bpy.context.active_object.data.shape_keys.key_blocks:
                k.value = 0.0
        return {"FINISHED"}


class VRM_VALIDATOR(bpy.types.Operator):
    bl_idname = "vrm.model_validate"
    bl_label = "Validate VRM model"
    bl_description = "NO Quad_Poly & N_GON, NO unSkined Mesh etc..."
    bl_options = {'REGISTER', 'UNDO'}

    messages_set= []
    def execute(self,context):
        messages = VRM_VALIDATOR.messages_set = set()
        print("validation start")
        armature_count = 0
        armature = None
        node_name_set = set()
        #region selected object seeking
        for obj in bpy.context.selected_objects:
            if obj.name in node_name_set:
                messages.add("Nodes(mesh,bones) require unique names for VRM export. {} is duplicated.".format(obj.name))
            node_name_set.add(obj.name)
            if obj.type != "EMPTY" and (obj.parent is not None and obj.parent.type != "ARMATURE" and obj.type == "MESH"):
                if obj.location != Vector([0.0,0.0,0.0]):#mesh and armature origin is on [0,0,0]
                    messages.add("There are not an object on the origin {}".format(obj.name))
            if obj.type == "ARMATURE":
                armature = obj
                armature_count += 1
                if armature_count >= 2:#only one armature
                    messages.add("Only one armature is required for VRM export. Multiple armatures found.")
                already_root_bone_exist = False
                for bone in obj.data.bones:
                    if bone.name in node_name_set:#nodes name is unique
                        messages.add("Nodes(mesh,bones) require unique names for VRM export. {} is duplicated.".format(bone.name))
                    node_name_set.add(bone.name)
                    if bone.parent == None: #root bone is only 1
                        if already_root_bone_exist:
                            messages.add("There is only one root bone {},{} is root bone now".format(bone.name,already_root_bone_exist))
                        already_root_bone_exist = bone.name
                #TODO: T_POSE,
                require_human_bone_dic = {bone_tag : None for bone_tag in [
                "hips","leftUpperLeg","rightUpperLeg","leftLowerLeg","rightLowerLeg","leftFoot","rightFoot",
                "spine","chest","neck","head","leftUpperArm","rightUpperArm",
                "leftLowerArm","rightLowerArm","leftHand","rightHand"
                ]}
                for bone in armature.data.bones:
                    if "humanBone" in bone.keys():
                        if bone["humanBone"] in require_human_bone_dic.keys():
                            if require_human_bone_dic[bone["humanBone"]]:
                                messages.add("humanBone is duplicated with {},{}".format(bone.name,require_human_bone_dic[bone["humanBone"]].name))
                            else:
                                require_human_bone_dic[bone["humanBone"]] = bone
                for k,v in require_human_bone_dic.items():
                    if v is None:
                        messages.add("humanBone: {} is not defined.".format(k))
                defined_human_bone = ["jaw","leftShoulder","rightShoulder",
                "leftEye","rightEye","upperChest","leftToes","rightToes",
                "leftThumbProximal","leftThumbIntermediate","leftThumbDistal","leftIndexProximal",
                "leftIndexIntermediate","leftIndexDistal","leftMiddleProximal","leftMiddleIntermediate",
                "leftMiddleDistal","leftRingProximal","leftRingIntermediate","leftRingDistal",
                "leftLittleProximal","leftLittleIntermediate","leftLittleDistal",
                "rightThumbProximal","rightThumbIntermediate","rightThumbDistal",
                "rightIndexProximal","rightIndexIntermediate","rightIndexDistal",
                "rightMiddleProximal","rightMiddleIntermediate","rightMiddleDistal",
                "rightRingProximal","rightRingIntermediate","rightRingDistal",
                "rightLittleProximal","rightLittleIntermediate","rightLittleDistal"
                ]

            if obj.type == "MESH":
                if len(obj.data.materials) == 0:
                    messages.add(f"There is no material assigned to mesh {obj.name}")
                for poly in obj.data.polygons:
                    if poly.loop_total > 3:#polygons need all triangle
                        messages.add(f"There are not Triangle faces in {obj.name}")
                        break
                
                #TODO modifier applyed, vertex weight Bone exist, vertex weight numbers.
        #endregion selected object seeking
        if armature_count == 0:
            messages.add("NO ARMATURE!")
            
        used_image = []
        used_material_set = set()
        for mesh in [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]:
            for mat in mesh.data.materials:
                used_material_set.add(mat)
            for v in mesh.data.vertices:
                if len(v.groups) == 0:
                    messages.add(f"vertex id {v.index} is no weight in {mesh.name}")
                elif len(v.groups) >= 5:
                    messages.add(f"vertex id {v.index} has too many(over 4) weight in {mesh.name}")
        for mat in used_material_set:
            for node in mat.node_tree.nodes:
                if node.type =="OUTPUT_MATERIAL" \
                and (
                    node.inputs['Surface'].links[0].from_node.type != "GROUP" \
                    or node.inputs["Surface"].links[0].from_node.node_tree.get("SHADER") is None 
                ):
                     messages.add(f"{mat.name} doesn't connect VRM SHADER node group to Material output node in material node tree. Please use them and connect properly.")

        shader_nodes_and_material = [(node.inputs["Surface"].links[0].from_node,mat) for mat in used_material_set \
                                        for node in mat.node_tree.nodes \
                                        if node.type =="OUTPUT_MATERIAL" \
                                            and node.inputs['Surface'].links[0].from_node.type == "GROUP" \
                                            and node.inputs["Surface"].links[0].from_node.node_tree.get("SHADER") is not None
                                        ]

        for node,material in shader_nodes_and_material:
            def input_check(expect_node_type,shader_val):
                if node.inputs[shader_val].links:
                    n = node.inputs[shader_val].links[0].from_node
                    if n.type != expect_node_type:
                        messages.add(f"need {expect_node_type} input in {shader_val} of {material.name}")
                    else:
                        if expect_node_type == "TEX_IMAGE":
                            used_image.append(n.image)
            #MToon
            if node.node_tree["SHADER"] == "MToon_unversioned":
                for shader_val in VRM_types.Material_MToon.texture_kind_exchange_dic.values():
                    if shader_val is None:
                        continue
                    else:
                        if shader_val == "ReceiveShadow_Texture":
                            continue
                        input_check("TEX_IMAGE",shader_val)
                for shader_val in [*list(VRM_types.Material_MToon.float_props_exchange_dic.values()),"ReceiveShadow_Texture_alpha"]:
                    if shader_val is None:
                        continue
                    else:
                        input_check("VALUE", shader_val)
                for k in ["_Color", "_ShadeColor", "_EmissionColor", "_OutlineColor"]:
                    input_check("RGB", VRM_types.Material_MToon.vector_props_exchange_dic[k])
            #GLTF    
            elif node.node_tree["SHADER"] == "GLTF":
                texture_input_name_list = [
					"color_texture",
					"normal",
					"emissive_texture",
					"occlusion_texture"
				]
                val_input_name_list = [
                    "metallic",
                    "roughness",
                    "unlit"
                ]
                rgba_input_name_list = [
                    "base_Color",
                    "emissive_color"
                ]
                for k in texture_input_name_list:
                    input_check("TEX_IMAGE",k)
                for k in val_input_name_list:
                    input_check("VALUE",k)
                for k in rgba_input_name_list:
                    input_check("RGB", k)
            #Transparent_Zwrite
            elif node.node_tree["SHADER"] == "TRANSPARENT_ZWRITE":
                input_check("TEX_IMAGE","Main_Texture")
            else:
                pass #?
		#thumbnail
        try:
            if armature is not None:
                if armature.get("texture") != None:
                    thumbnail_image = bpy.data.images.get(armature["texture"])
                    if thumbnail_image:
                        used_image.append(thumbnail_image)
                    else:
                        messages.add(f"thumbnail_image is missing. Please load {armature['texture']}")
        except:
            messages.add(f"thumbnail_image is missing. Please load {armature['texture']}")
            pass
            
        for img in used_image:
            if img.is_dirty or img.filepath =="":
                messages.add(f"{img.name} is not saved. Please save.")
            if img.file_format.lower() not in ["png","jpeg"]:
                messages.add("glTF only supports PNG and JPEG textures")

        
        
        if armature is not None:
            #region vrm metas check 
            required_vrm_metas = { #care about order 0 : that must be SAFE SELECTION (for auto set custom propaties )
                "allowedUserName":["OnlyAuthor","ExplicitlyLicensedPerson","Everyone"],
                "violentUssageName":["Disallow","Allow"],
                "sexualUssageName":["Disallow","Allow"],
                "commercialUssageName":["Disallow","Allow"],
                "licenseName":["Redistribution_Prohibited","CC0","CC_BY","CC_BY_NC","CC_BY_SA","CC_BY_NC_SA","CC_BY_ND","CC_BY_NC_ND","Other"],
            }
            for k,v in required_vrm_metas.items():
                if armature.get(k) is None:
                    armature[k] = v[0]
                    messages.add(f"{k} is not defined in armature as custom propaty. It set as {v}. Please check it.")
                if armature.get(k) not in v :
                    messages.add(f"{k} value must be in {v}. Value is {armature.get(k)}")
            vrm_metas = [
                "version",#model version (not VRMspec etc)
                "author",
                "contactInformation",
                "reference",
                "title",
                "otherPermissionUrl",
                "otherLicenseUrl"
            ]
            for k in vrm_metas:
                if armature.get(k) is None:
                    armature[k] = "undefined"
                    messages.add(f"{k} is not defined in armature as custom propaty. It set as \"undefined\". Please check it.")

            #region textblock_validate

            def text_block_name_to_json(textblock_name):
                if textblock_name not in armature:
                    return None
                try:
                    json_as_dict = json.loads("".join([line.body for line in bpy.data.texts[armature[textblock_name]].lines]),object_pairs_hook=OrderedDict)
                except json.JSONDecodeError as e:
                    messages.add(f"Cannot load textblock of {textblock_name} as Json at line {e.pos.lineno}. please check json grammar.")
                    json_as_dict = None
                return json_as_dict
            def text_block_write(block_name,data_dict):
                textblock = bpy.data.texts.new(name = f"{block_name}_.json")
                textblock.write(json.dumps(data_dict,indent = 4))
                return textblock

            mesh_obj_names = [obj.name for obj in bpy.context.selected_objects if obj.type == "MESH"]
            #region humanoid_parameter
            humanoid_param_name = "humanoid_params"
            humanoid_param = text_block_name_to_json(humanoid_param_name)
            if humanoid_param is None:
                armature[humanoid_param_name] = text_block_write(
                    humanoid_param_name,
                    {"armStretch": 0.05,
                    "legStretch": 0.05,
                    "upperArmTwist": 0.5,
                    "lowerArmTwist": 0.5,
                    "upperLegTwist": 0.5,
                    "lowerLegTwist": 0.5,
                    "feetSpacing": 0,
                    "hasTranslationDoF": False
                    })
            #endregion humanoid_parameter
            #region first_person
            firstPerson_params_name = "firstPerson_params"
            firstperson_params = text_block_name_to_json(firstPerson_params_name)
            fp_bone = json_get(firstperson_params,["firstPersonBone"],-1)
            if fp_bone != -1:
                if not firstperson_params["firstPersonBone"] in armature.data.bones:
                    messages.add(f"firstPersonBone :{firstperson_params['firstPersonBone']} is not found."+\
                                 f"Please fix in textblock : {firstPerson_params_name} ")
            if "meshAnnotations" in firstperson_params.keys():
                if type(firstperson_params["meshAnnotations"]) is not list:
                    messages.add(f"meshAnnotations in textblock:{firstPerson_params_name} must be list.")
                else:
                    for meshAnotation in firstperson_params["meshAnnotations"]:
                        if not meshAnotation["mesh"] in mesh_obj_names:
                            messages.add(f"mesh :{meshAnotation['mesh']} is not found."+\
                                        f"Please fix setting in textblock : {firstPerson_params_name} ")
            if "lookAtTypeName" in firstperson_params:
                if not firstperson_params["lookAtTypeName"] in ["Bone","BlendShape"]:
                    messages.add(f"lookAtTypeName is \"Bone\" or \"BlendShape\". Current :{firstperson_params['lookAtTypeName']}."+\
                                 f"Please fix setting in textblock : {firstPerson_params_name} ")
            #endregion first_person

            #TODO ABOVE IS DONE

            #region blendshape_master
            blendshape_group_name = "blendshape_group"
            blendShapeGroups_list = text_block_name_to_json(blendshape_group_name)
            #meshをidから名前に
            #weightを0-100から0-1に
            #shape_indexを名前に
            #materialValuesはそのままで行けるハズ・・・
            ex={\
            "name": "A",
            "presetName": "a",
            "binds": [
                {"mesh": "Face.baked",
                 "index": "Face.M_F00_000_00_Fcl_MTH_A",
                 "weight": 1.0}
            ],
            "materialValues": []
            }
            for bsg in blendShapeGroups_list:
                for bind_dic in bsg["binds"]:
                    if not bind_dic["mesh"] in mesh_obj_names:
                        messages.add(f"mesh :{bind_dic['mesh']} is not found."+\
                                    f"Please fix setting in textblock : {blendshape_group_name} ")          
                    else:
                        if bpy.data.objects[bind_dic["mesh"]].data.shape_keys is None:
                            messages.add(f"mesh :{bind_dic['mesh']} doesn't have shapekey. but blendshape Group need it."+\
                                         f"Please fix setting in textblock :{blendshape_group_name}")
                        else:
                            if not bind_dic["index"] in bpy.data.objects[bind_dic["mesh"]].data.shape_keys.key_blocks:
                                messages.add(f"mesh :{bind_dic['mesh']} doesn't have shapekey :{bind_dic['index']}. but blendshape Group need it."+\
                                            f"Please fix setting in textblock :{blendshape_group_name}")
                            if bind_dic["weight"] > 1 or bind_dic["weight"] < 0:
                                messages.add(f"mesh :{bind_dic['mesh']}:shapekey:{bind_dic['index']}:value needs between 0 and 1."+\
                                            f"Please fix setting in textblock :{blendshape_group_name}")                            
            
            #endregion blendshape_master

            #region springbone
            spring_bonegroup_list = text_block_name_to_json("spring_bone") 
            #node_idを管理するのは面倒なので、名前に置き換える
            #collider_groupも同じく
            bone_names_list = [bone.name for bone in armature.data.bones]
            for bone_group in spring_bonegroup_list:
                for bone_name in bone_group["bones"]:
                    if not bone_name in bone_names_list :
                        messages.add(f"Bone name : {bone_name} is not found in spring_bone setting.")
                for bone_name in bone_group["colliderGroups"]:
                    if not bone_name in bone_names_list:
                        messages.add(f"Bone name : {bone_name} is not found in spring_bone setting.")
            
            
        #endregion vrm metas check

        for mes in messages:
            print(mes)
        print("validation finished")
        
        if len(messages) > 0 :
            VRM_VALIDATOR.draw_func_add()
            raise Exception
        else:
            messages.add("not found expected error for export")
            VRM_VALIDATOR.draw_func_add()           
        return {"FINISHED"}

    #region 3Dview drawer
    draw_func = None
    counter = 0
    @staticmethod
    def draw_func_add():
        if VRM_VALIDATOR.draw_func is not None:
            VRM_VALIDATOR.draw_func_remove()
        VRM_VALIDATOR.draw_func = bpy.types.SpaceView3D.draw_handler_add(
            VRM_VALIDATOR.texts_draw,
            (), 'WINDOW', 'POST_PIXEL')
        VRM_VALIDATOR.counter = 300

    @staticmethod
    def draw_func_remove():
        if VRM_VALIDATOR.draw_func is not None:
            bpy.types.SpaceView3D.draw_handler_remove(
                VRM_VALIDATOR.draw_func, 'WINDOW')
            VRM_VALIDATOR.draw_func = None
    
    @staticmethod
    def texts_draw():
        text_size = 20
        dpi = 72
        blf.size(0, text_size, dpi)
        for i,text in enumerate(list(VRM_VALIDATOR.messages_set)):
            blf.position(0, text_size, text_size*(i+1)+100, 0)
            blf.draw(0, text)
        blf.position(0,text_size,text_size*(2+len(VRM_VALIDATOR.messages_set))+100,0)
        blf.draw(0, "message delete count down...:{}".format(VRM_VALIDATOR.counter))
        VRM_VALIDATOR.counter -= 1
        if VRM_VALIDATOR.counter <= 0:
            VRM_VALIDATOR.draw_func_remove()
    #endregion 3Dview drawer