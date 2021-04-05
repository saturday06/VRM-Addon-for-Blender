"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

from typing import Any, Dict, Optional

from .. import vrm_types


def bone(node: Dict[str, Any]) -> vrm_types.Node:
    v_node = vrm_types.Node(
        name=node.get("name", "tmp"),
        position=node.get("translation", [0, 0, 0]),
        rotation=node.get("rotation", (0, 0, 0, 1)),
        scale=node.get("scale", (1, 1, 1)),
    )
    if "children" in node:
        children = node["children"]
        if isinstance(children, int):
            v_node.children = [children]
        else:
            v_node.children = children
    else:
        v_node.children = None
    if "mesh" in node:
        v_node.mesh_id = node["mesh"]
    if "skin" in node:
        v_node.skin_id = node["skin"]
    return v_node


def material(
    mat: Dict[str, Any], ext_mat: Dict[str, Any]
) -> Optional[vrm_types.Material]:
    shader = ext_mat.get("shader")

    # standard, or VRM unsupported shader(no saved)
    if shader not in ["VRM/MToon", "VRM/UnlitTransparentZWrite"]:
        gltf = vrm_types.MaterialGltf()
        gltf.name = mat.get("name", "")
        gltf.shader_name = "gltf"
        if "pbrMetallicRoughness" in mat:
            pbrmat = mat["pbrMetallicRoughness"]
            if "baseColorTexture" in pbrmat and isinstance(
                pbrmat["baseColorTexture"], dict
            ):
                texture_index = pbrmat["baseColorTexture"].get("index")
                gltf.color_texture_index = texture_index
                gltf.color_texcoord_index = pbrmat["baseColorTexture"].get("texCoord")
            if "baseColorFactor" in pbrmat:
                gltf.base_color = pbrmat["baseColorFactor"]
            if "metallicFactor" in pbrmat:
                gltf.metallic_factor = pbrmat["metallicFactor"]
            if "roughnessFactor" in pbrmat:
                gltf.roughness_factor = pbrmat["roughnessFactor"]
            if "metallicRoughnessTexture" in pbrmat and isinstance(
                pbrmat["metallicRoughnessTexture"], dict
            ):
                texture_index = pbrmat["metallicRoughnessTexture"].get("index")
                gltf.metallic_roughness_texture_index = texture_index
                gltf.metallic_roughness_texture_texcoord = pbrmat[
                    "metallicRoughnessTexture"
                ].get("texCoord")

        if "normalTexture" in mat and isinstance(mat["normalTexture"], dict):
            gltf.normal_texture_index = mat["normalTexture"].get("index")
            gltf.normal_texture_texcoord_index = mat["normalTexture"].get("texCoord")
        if "emissiveTexture" in mat and isinstance(mat["emissiveTexture"], dict):
            gltf.emissive_texture_index = mat["emissiveTexture"].get("index")
            gltf.emissive_texture_texcoord_index = mat["emissiveTexture"].get(
                "texCoord"
            )
        if "occlusionTexture" in mat and isinstance(mat["occlusionTexture"], dict):
            gltf.occlusion_texture_index = mat["occlusionTexture"].get("index")
            gltf.occlusion_texture_texcoord_index = mat["occlusionTexture"].get(
                "texCoord"
            )
        if "emissiveFactor" in mat:
            gltf.emissive_factor = mat["emissiveFactor"]

        if "doubleSided" in mat:
            gltf.double_sided = mat["doubleSided"]
        if "alphaMode" in mat:
            if mat["alphaMode"] == "MASK":
                gltf.alpha_mode = "MASK"
                if mat.get("alphaCutoff"):
                    gltf.alphaCutoff = mat.get("alphaCutoff")
                else:
                    gltf.alphaCutoff = 0.5
            elif mat["alphaMode"] == "BLEND":
                gltf.alpha_mode = "Z_TRANSPARENCY"
            elif mat["alphaMode"] == "OPAQUE":
                gltf.alpha_mode = "OPAQUE"
        if "extensions" in mat and "KHR_materials_unlit" in mat["extensions"]:
            gltf.shadeless = 1  # 0 is shade ,1 is shadeless

        if isinstance(ext_mat.get("extras"), dict) and isinstance(
            ext_mat["extras"].get("VRM_Addon_for_Blender_legacy_gltf_material"), dict
        ):
            gltf.vrm_addon_for_blender_legacy_gltf_material = True
        return gltf

    # "MToon or Transparent_Zwrite"
    if shader == "VRM/MToon":
        mtoon = vrm_types.MaterialMtoon()
        mtoon.name = ext_mat.get("name", "")
        mtoon.shader_name = ext_mat.get("shader", "")
        # region check unknown props exist
        subset = {
            "float": ext_mat.get("floatProperties", {}).keys()
            - mtoon.float_props_dic.keys(),
            "vector": ext_mat.get("vectorProperties", {}).keys()
            - mtoon.vector_props_dic.keys(),
            "texture": ext_mat.get("textureProperties", {}).keys()
            - mtoon.texture_index_dic.keys(),
            "keyword": ext_mat.get("keywordMap", {}).keys() - mtoon.keyword_dic.keys(),
        }
        for k, _subset in subset.items():
            if _subset:
                print(
                    "unknown {} properties {} in {}".format(
                        k, _subset, ext_mat.get("name")
                    )
                )
        # endregion check unknown props exit

        mtoon.float_props_dic.update(ext_mat.get("floatProperties", {}))
        mtoon.vector_props_dic.update(ext_mat.get("vectorProperties", {}))
        mtoon.texture_index_dic.update(ext_mat.get("textureProperties", {}))
        mtoon.keyword_dic.update(ext_mat.get("keywordMap", {}))
        mtoon.tag_dic.update(ext_mat.get("tagMap", {}))
        return mtoon

    if shader == "VRM/UnlitTransparentZWrite":
        transparent_z_write = vrm_types.MaterialTransparentZWrite()
        transparent_z_write.name = ext_mat.get("name", "")
        transparent_z_write.shader_name = ext_mat.get("shader", "")
        transparent_z_write.float_props_dic = ext_mat.get("floatProperties", {})
        transparent_z_write.vector_props_dic = ext_mat.get("vectorProperties", {})
        transparent_z_write.texture_index_dic = ext_mat.get("textureProperties", {})
        return transparent_z_write

    # ここには入らないはず
    print(
        f"Unknown(or legacy) shader :material {ext_mat['name']} is {ext_mat['shader']}"
    )
    return None
