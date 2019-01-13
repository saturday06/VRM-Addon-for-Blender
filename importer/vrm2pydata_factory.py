"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

from .. import V_Types as VRM_Types

def bone(node)->VRM_Types.Node:
    v_node = VRM_Types.Node()
    if "name" in node:
        v_node.name = node["name"]
    else:
        v_node.name = "tmp"
    v_node.position = node["translation"]
    v_node.rotation = node["rotation"]
    v_node.scale = node["scale"]
    if "children" in node:
        if type(node["children"]) is int:
            v_node.children = [node["children"]]
        else:
            v_node.children = node["children"]
    else:
        v_node.children = None
    if "mesh" in node:
        v_node.mesh_id = node["mesh"]
    if "skin" in node:
        v_node.skin_id = node["skin"]
    return v_node



def material(mat,ext_mat,textures)->VRM_Types.Material:

    if "VRM_USE_GLTFSHADER" in ext_mat["shader"]:  #standard, or VRM unsuported shader(no saved)
        v_mat = VRM_Types.Material_GLTF()
        v_mat.name = mat["name"]
        v_mat.shader_name = "gltf"
        if "pbrMetallicRoughness" in mat:
            pbrmat = mat["pbrMetallicRoughness"]
            if "baseColorTexture" in pbrmat:
                texture_index = pbrmat["baseColorTexture"]["index"]
                v_mat.color_texture_index = textures[texture_index]["source"]
                v_mat.color_texcoord_index= pbrmat["baseColorTexture"]["texCoord"]
            if "baseColorFactor" in pbrmat:
                v_mat.base_color = pbrmat["baseColorFactor"]
            if "metallicFactor" in pbrmat:
                v_mat.metallicFactor = pbrmat["metallicFactor"]
            if "roughnessFactor" in pbrmat:
                v_mat.roughnessFactor = pbrmat["roughnessFactor"]
            if "metallicRoughnessTexture" in pbrmat:
                v_mat.metallicRoughnessTexture_index = pbrmat["metallicRoughnessTexture"]
                v_mat.metallicRoughnessTexture_texcoord = pbrmat["baseColorTexture"]["texCoord"]

        if "normalTexture" in mat:
            v_mat.normal_texture_index = mat["normalTexture"]["index"]
            v_mat.normal_texture_texcoord_index = mat["normalTexture"]["texCoord"]
        if "emissiveTexture" in mat:
            v_mat.emissive_texture_index = mat["emissiveTexture"]["index"]
            v_mat.emissive_texture_texcoord_index = mat["emissiveTexture"]["texCoord"]
        if "occlusionTexture" in mat:
            v_mat.occlusion_texture_index = mat["occlusionTexture"]["index"]
            v_mat.occlusion_texture_texcood_index = mat["occlusionTexture"]["texCoord"]
        if "emissiveFactor" in mat:
            v_mat.emissive_color = mat["emissiveFactor"]

        if "doubleSided" in mat:
            v_mat.doubleSided = mat["doubleSided"]
        if "alphaMode" in mat:
            if mat["alphaMode"] == "MASK":
                v_mat.alpha_mode = "MASK"
            if mat["alphaMode"] == "BLEND":
                v_mat.alpha_mode = "Z_TRANSPARENCY"
            if mat["alphaMode"] == "OPAQUE":
                v_mat.alpha_mode = "OPAQUE"
        if "extensions" in mat:
            if "KHR_materials_unlit" in mat["extensions"]:
                v_mat.shadeless = True

    else:#"MToon or Transparent_Zwrite"
        if ext_mat["shader"] == "VRM/MToon":
            v_mat = VRM_Types.Material_MToon()
            v_mat.name = ext_mat["name"]
            v_mat.shader_name = ext_mat["shader"]
            #region check unknown props exist
            subset = {
                "float": ext_mat["floatProperties"].keys() - v_mat.float_props_dic.keys() ,
                "vector": ext_mat["vectorProperties"].keys() - v_mat.vector_props_dic.keys(),
                "texture": ext_mat["textureProperties"].keys() - v_mat.texture_index_dic.keys(),
                "keyword": ext_mat["keywordMap"].keys() - v_mat.keyword_dic.keys()
            }
            for k, _subset in subset.items():       
                if _subset:
                    print("unknown {} propaties {} in {}".format(k, _subset, ext_mat["name"]))
            #endregion check unknown props exit

            v_mat.float_props_dic.update(ext_mat["floatProperties"])
            v_mat.vector_props_dic.update(ext_mat["vectorProperties"])
            v_mat.texture_index_dic.update(ext_mat["textureProperties"])
            v_mat.keyword_dic.update(ext_mat["keywordMap"])
            v_mat.tag_dic.update(ext_mat["tagMap"])

        if ext_mat["shader"] == "VRM/UnlitTransparentZWrite":
            v_mat = VRM_Types.Material_Transparent_Z_write()
            v_mat.shader_name = ext_mat["shader"]
            v_mat.float_prop_dic.update(ext_mat["floatProperties"])
            v_mat.vector_props_dic.update(ext_mat["vectorProperties"])
            v_mat.texture_index_dic.update(ext_mat["textureProperties"])

    return v_mat




