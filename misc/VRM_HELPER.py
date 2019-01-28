"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""
import bpy
import bmesh
import re
from math import sqrt, pow
from mathutils import Vector
from collections import deque
class Bones_rename(bpy.types.Operator):
    bl_idname = "vrm.bones_rename"
    bl_label = "convert Vroid_bones"
    bl_description = "convert Vroid_bones as blender type"
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
    bl_label = "make ripsync4VRC"
    bl_description = "make ripsync from Vroid to VRC by json"
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
                bpy.context.active_object.data.shape_keys.key_blocks[based_shapekey_name].value = based_val
            bpy.ops.object.shape_key_add(from_mix = True)
            bpy.context.active_object.data.shape_keys.key_blocks[-1].name = shapekey_name
        for k in bpy.context.active_object.data.shape_keys.key_blocks:
                k.value = 0.0
        return {"FINISHED"}


class VRM_VALIDATOR(bpy.types.Operator):
    bl_idname = "vrm.model_validate"
    bl_label = "check as VRM model"
    bl_description = "NO Quad_Poly & N_GON, NO unSkind Mesh etc..."
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self,context):
        print("validation start")
        armature_count = 0
        armature = None
        node_name_set = set()
        for obj in bpy.context.selected_objects:
            if obj.name in node_name_set:
                print("VRM exporter need Nodes(mesh,bones) name is unique. {} is doubled.".format(obj.name))
            node_name_set.add(obj.name)
            if obj.type != "EMPTY" and (obj.parent is not None and obj.parent.type != "ARMATURE" and obj.type == "MESH"):
                if obj.location != Vector([0.0,0.0,0.0]):#mesh and armature origin is on [0,0,0]
                    print("There are not on origine location object {}".format(obj.name))
            if obj.type == "ARMATURE":
                armature = obj
                armature_count += 1
                if armature_count > 2:#only one armature
                    print("VRM exporter needs only one armature not some armatures")
                already_root_bone_exist = False
                for bone in obj.data.bones:
                    if bone.name in node_name_set:#nodes name is unique
                        print("VRM exporter need Nodes(mesh,bones) name is unique. {} is doubled".format(bone.name))
                    node_name_set.add(bone.name)
                    if bone.parent == None: #root bone is only 1
                        if already_root_bone_exist:
                            print("root bone is only one {},{} are root bone now".format(bone.name,already_root_bone_exist))
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
                                print("humanBone is doubled with {},{}".format(bone.name,require_human_bone_dic[bone["humanBone"]].name))
                            else:
                                require_human_bone_dic[bone["humanBone"]] = bone
                for k,v in require_human_bone_dic.items():
                    if v is None:
                        print("humanBone: {} is not defined.".format(k))
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
                    print("There is no material in mesh {}".format(obj.name))
                for poly in obj.data.polygons:
                    if poly.loop_total > 3:#polygons need all triangle
                        print("There are not Triangle faces in {}".format(obj.name))
                #TODO modifier applyed, vertex weight Bone exist, vertex weight numbers.
        used_image = []
        used_material_set = set()
        for mesh in [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]:
            for mat in mesh.data.materials:
                used_material_set.add(mat)
        for mat in used_material_set:
            if mat.texture_slots is not None:
	            used_image += [tex_slot.texture.image for tex_slot in mat.texture_slots if tex_slot is not None]
		#thumbnail
        try:
            used_image.append(bpy.data.images[armature["texture"]])
        except:
            pass
        for img in used_image:
            if img.is_dirty or img.filepath =="":
                print("{} is not saved, please save.".format(img.name))
            if image.file_format.lower() not in ["png","jpeg"]:
                print("GLTF texture format is PNG AND JPEG only")


        #TODO textblock_validate
        print("validation finished")
        return {"FINISHED"}