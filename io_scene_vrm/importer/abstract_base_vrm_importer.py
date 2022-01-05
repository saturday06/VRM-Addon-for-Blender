"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""


import collections
import copy
import json
import math
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence, Set

import bgl
import bpy
from mathutils import Matrix

from .. import common
from ..common import convert, deep
from ..common.human_bone import HumanBones
from ..common.mtoon_constants import MaterialMtoon
from ..common.shader import shader_node_group_import
from ..editor import migration, operator, panel
from ..editor.extension import VrmAddonArmatureExtensionPropertyGroup
from ..editor.vrm0.property_group import (
    Vrm0BlendShapeMasterPropertyGroup,
    Vrm0FirstPersonPropertyGroup,
    Vrm0HumanoidPropertyGroup,
    Vrm0MetaPropertyGroup,
    Vrm0PropertyGroup,
    Vrm0SecondaryAnimationPropertyGroup,
)
from .vrm_parser import (
    ParseResult,
    PyMaterial,
    PyMaterialGltf,
    PyMaterialMtoon,
    PyMaterialTransparentZWrite,
)


class AbstractBaseVrmImporter(ABC):
    def __init__(
        self,
        context: bpy.types.Context,
        parse_result: ParseResult,
        extract_textures_into_folder: bool,
        make_new_texture_folder: bool,
    ) -> None:
        self.context = context
        self.parse_result = parse_result
        self.extract_textures_into_folder = extract_textures_into_folder
        self.make_new_texture_folder = make_new_texture_folder

        self.meshes: Dict[int, bpy.types.Object] = {}
        self.images: Dict[int, bpy.types.Image] = {}
        self.armature: Optional[bpy.types.Object] = None
        self.bone_names: Dict[int, str] = {}
        self.gltf_materials: Dict[int, bpy.types.Material] = {}
        self.vrm_materials: Dict[int, bpy.types.Material] = {}
        self.primitive_obj_dict: Optional[Dict[Optional[int], List[float]]] = None
        self.mesh_joined_objects = None

    @abstractmethod
    def import_vrm(self) -> None:
        pass

    @staticmethod
    def axis_glb_to_blender(vec3: Sequence[float]) -> List[float]:
        return [vec3[i] * t for i, t in zip([0, 2, 1], [-1, 1, 1])]

    def connect_bones(self) -> None:
        armature = self.armature
        if armature is None:
            raise Exception("armature is None")

        # Blender_VRMAutoIKSetup (MIT License)
        # https://booth.pm/ja/items/1697977
        previous_active = bpy.context.view_layer.objects.active
        try:
            bpy.context.view_layer.objects.active = self.armature  # アーマチャーをアクティブに
            bpy.ops.object.mode_set(mode="EDIT")  # エディットモードに入る
            disconnected_bone_names = []  # 結合されてないボーンのリスト
            vrm0_extension = self.parse_result.vrm0_extension
            if vrm0_extension is not None and str(
                vrm0_extension.get("exporterVersion")
            ).startswith("VRoidStudio-"):
                disconnected_bone_names = [
                    "J_Bip_R_Hand",
                    "J_Bip_L_Hand",
                    "J_Bip_L_LowerLeg",
                    "J_Bip_R_LowerLeg",
                ]
            bpy.ops.armature.select_all(action="SELECT")  # 全てのボーンを選択
            for bone in bpy.context.selected_bones:  # 選択しているボーンに対して繰り返し処理
                for (
                    disconnected_bone_name
                ) in disconnected_bone_names:  # 結合されてないボーンのリスト分繰り返し処理
                    # リストに該当するオブジェクトがシーン中にあったら処理
                    if bone.name == disconnected_bone_name:
                        # disconnected_bone変数に処理ボーンを代入
                        disconnected_bone = armature.data.edit_bones[
                            disconnected_bone_name
                        ]
                        # 処理対象の親ボーンのTailと処理対象のHeadを一致させる
                        disconnected_bone.parent.tail = disconnected_bone.head

            panel.make_armature.connect_parent_tail_and_child_head_if_same_position(
                armature.data
            )
            bpy.ops.object.mode_set(mode="OBJECT")
        finally:
            bpy.context.view_layer.objects.active = previous_active

    def scene_init(self) -> bpy.types.Object:
        # active_objectがhideだとbpy.ops.object.mode_set.poll()に失敗してエラーが出るのでその回避と、それを元に戻す
        affected_object = None
        if self.context.active_object is not None:
            if (
                hasattr(self.context.active_object, "hide_viewport")
                and self.context.active_object.hide_viewport
            ):
                self.context.active_object.hide_viewport = False
                affected_object = self.context.active_object
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")
        return affected_object

    def finishing(self, affected_object: bpy.types.Object) -> None:
        # initで弄ったやつを戻す
        if affected_object is not None:
            affected_object.hide_viewport = True

        for obj in bpy.context.selected_objects:
            obj.select_set(False)

        # image_path_to Texture

    def use_fake_user_for_thumbnail(self) -> None:
        # サムネイルはVRMの仕様ではimageのインデックスとあるが、UniVRMの実装ではtextureのインデックスになっている
        # https://github.com/vrm-c/UniVRM/blob/v0.67.0/Assets/VRM/Runtime/IO/VRMImporterContext.cs#L308
        json_texture_index = deep.get(
            self.parse_result.vrm0_extension, ["meta", "texture"], -1
        )
        if not isinstance(json_texture_index, int):
            raise Exception('json["extensions"]["VRM"]["meta"]["texture"] is not int')
        json_textures = self.parse_result.json_dict.get("textures", [])
        if not isinstance(json_textures, list):
            raise Exception('json["textures"] is not list')
        if json_texture_index not in (-1, None) and (
            "textures" in self.parse_result.json_dict
            and len(json_textures) > json_texture_index
        ):
            image_index = json_textures[json_texture_index].get("source")
            if image_index in self.images:
                self.images[image_index].use_fake_user = True

    # region material
    def make_material(self) -> None:
        # 適当なので要調整
        for index, mat in enumerate(self.parse_result.materials):
            if (
                bpy.app.version >= (2, 83)
                and isinstance(mat, PyMaterialGltf)
                and not mat.vrm_addon_for_blender_legacy_gltf_material
            ):
                continue
            b_mat = bpy.data.materials.new(mat.name)
            b_mat["shader_name"] = mat.shader_name
            if isinstance(mat, PyMaterialGltf):
                self.build_material_from_gltf(b_mat, mat)
            elif isinstance(mat, PyMaterialMtoon):
                self.build_material_from_mtoon(b_mat, mat)
            elif isinstance(mat, PyMaterialTransparentZWrite):
                self.build_material_from_transparent_z_write(b_mat, mat)
            else:
                print(f"unknown material {mat.name}")
            self.node_placer(b_mat.node_tree.nodes["Material Output"])
            self.vrm_materials[index] = b_mat

        gltf_material_original_names = {
            vrm_material_index: self.gltf_materials[vrm_material_index].name
            for vrm_material_index in self.vrm_materials
            if vrm_material_index in self.gltf_materials
        }
        for mesh in self.meshes.values():
            for material_index, material in enumerate(mesh.data.materials):
                if not material:
                    continue
                for vrm_material_index, vrm_material in self.vrm_materials.items():
                    material_original_name = gltf_material_original_names.get(
                        vrm_material_index
                    )
                    if (
                        material_original_name is None
                        or material != self.gltf_materials.get(vrm_material_index)
                    ):
                        continue
                    material.name = "~glTF_VRM_overridden_" + material_original_name
                    vrm_material.name = material_original_name
                    mesh.data.materials[material_index] = vrm_material
                    break

    # region material_util func
    def set_material_transparent(
        self,
        b_mat: bpy.types.Material,
        pymat: PyMaterial,
        transparent_mode: str,
    ) -> None:
        if transparent_mode == "OPAQUE":
            pass
        elif transparent_mode == "CUTOUT":
            b_mat.blend_method = "CLIP"
            if isinstance(pymat, PyMaterialMtoon):  # TODO: TransparentZWrite?
                b_mat.alpha_threshold = pymat.float_props_dic.get("_Cutoff", 0.5)
            else:
                b_mat.alpha_threshold = getattr(pymat, "alphaCutoff", 0.5)

            b_mat.shadow_method = "CLIP"
        else:  # Z_TRANSPARENCY or Z()_zwrite
            if "transparent_shadow_method" in dir(b_mat):  # old blender 2.80 beta
                b_mat.blend_method = "HASHED"
                b_mat.transparent_shadow_method = "HASHED"
            else:
                b_mat.blend_method = "HASHED"
                b_mat.shadow_method = "HASHED"

    def material_init(self, b_mat: bpy.types.Material) -> None:
        b_mat.use_nodes = True
        for node in b_mat.node_tree.nodes:
            if node.type != "OUTPUT_MATERIAL":
                b_mat.node_tree.nodes.remove(node)

    def connect_value_node(
        self,
        material: bpy.types.ShaderNode,
        value: float,
        socket_to_connect: bpy.types.NodeSocketFloat,
    ) -> bpy.types.ShaderNodeValue:
        value_node = material.node_tree.nodes.new("ShaderNodeValue")
        value_node.label = socket_to_connect.name
        value_node.outputs[0].default_value = value
        material.node_tree.links.new(socket_to_connect, value_node.outputs[0])
        return value_node

    def connect_rgb_node(
        self,
        material: bpy.types.ShaderNode,
        color: Optional[Sequence[float]],
        socket_to_connect: bpy.types.NodeSocketColor,
        default_color: Optional[List[float]] = None,
    ) -> bpy.types.ShaderNodeRGB:
        rgb_node = material.node_tree.nodes.new("ShaderNodeRGB")
        rgb_node.label = socket_to_connect.name
        rgb_node.outputs[0].default_value = (
            color if color else (default_color if default_color else [1, 1, 1, 1])
        )
        material.node_tree.links.new(socket_to_connect, rgb_node.outputs[0])
        return rgb_node

    def connect_texture_node(
        self,
        material: bpy.types.ShaderNode,
        tex_index: int,
        color_socket_to_connect: Optional[bpy.types.NodeSocketColor] = None,
        alpha_socket_to_connect: Optional[bpy.types.NodeSocketFloat] = None,
    ) -> bpy.types.ShaderNodeTexImage:
        tex = self.parse_result.json_dict["textures"][tex_index]
        image_index = tex["source"]
        sampler = (
            self.parse_result.json_dict["samplers"][tex["sampler"]]
            if "samplers" in self.parse_result.json_dict
            else [{"wrapS": bgl.GL_REPEAT, "magFilter": bgl.GL_LINEAR}]
        )
        image_node = material.node_tree.nodes.new("ShaderNodeTexImage")
        if image_index in self.images:
            image_node.image = self.images[image_index]
        if color_socket_to_connect is not None:
            image_node.label = color_socket_to_connect.name
        elif alpha_socket_to_connect is not None:
            image_node.label = alpha_socket_to_connect.name
        else:
            image_node.label = "what_is_this_node"
        # blender is ('Linear', 'Closest', 'Cubic', 'Smart') glTF is Linear, Closest
        filter_type = sampler["magFilter"] if "magFilter" in sampler else bgl.GL_LINEAR
        if filter_type == bgl.GL_NEAREST:
            image_node.interpolation = "Closest"
        else:
            image_node.interpolation = "Linear"
        # blender is ('REPEAT', 'EXTEND', 'CLIP') glTF is CLAMP_TO_EDGE,MIRRORED_REPEAT,REPEAT
        wrap_type = sampler["wrapS"] if "wrapS" in sampler else bgl.GL_REPEAT
        if wrap_type in (bgl.GL_REPEAT, bgl.GL_MIRRORED_REPEAT):
            image_node.extension = "REPEAT"
        else:
            image_node.extension = "EXTEND"
        if None not in (color_socket_to_connect, tex_index):
            material.node_tree.links.new(
                color_socket_to_connect, image_node.outputs["Color"]
            )
        if None not in (alpha_socket_to_connect, tex_index):
            material.node_tree.links.new(
                alpha_socket_to_connect, image_node.outputs["Alpha"]
            )
        return image_node

    def connect_with_color_multiply_node(
        self,
        material: bpy.types.ShaderNode,
        color: List[float],
        tex_index: int,
        socket_to_connect: bpy.types.NodeSocketColor,
    ) -> bpy.types.ShaderNodeMixRGB:
        multiply_node = material.node_tree.nodes.new("ShaderNodeMixRGB")
        multiply_node.blend_type = "MULTIPLY"
        self.connect_rgb_node(material, color, multiply_node.inputs[1])
        self.connect_texture_node(material, tex_index, multiply_node.inputs[2])
        material.node_tree.links.new(socket_to_connect, multiply_node.outputs[0])
        return multiply_node

    def node_group_create(
        self, material: bpy.types.ShaderNode, shader_node_group_name: str
    ) -> bpy.types.ShaderNodeGroup:
        node_group = material.node_tree.nodes.new("ShaderNodeGroup")
        node_group.node_tree = bpy.data.node_groups[shader_node_group_name]
        return node_group

    def node_placer(self, parent_node: bpy.types.ShaderNode) -> None:
        bottom_pos = [parent_node.location[0] - 200, parent_node.location[1]]
        for child_node in [
            link.from_node for socket in parent_node.inputs for link in socket.links
        ]:
            if child_node.type != "GROUP":
                child_node.hide = True
            child_node.location = bottom_pos
            bottom_pos[1] -= 40
            for _ in [
                link.from_node for socket in child_node.inputs for link in socket.links
            ]:
                self.node_placer(child_node)

    # endregion material_util func

    def build_principle_from_gltf_mat(
        self, b_mat: bpy.types.Material, pymat: PyMaterialGltf
    ) -> None:
        self.material_init(b_mat)
        principled_node = b_mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")

        b_mat.node_tree.links.new(
            b_mat.node_tree.nodes["Material Output"].inputs["Surface"],
            principled_node.outputs["BSDF"],
        )
        # self.connect_with_color_multiply_node(
        #     b_mat, pymat.base_color, pymat.color_texture_index, principled_node.inputs["Base Color"]
        # )
        if pymat.color_texture_index is not None:
            self.connect_texture_node(
                b_mat,
                pymat.color_texture_index,
                principled_node.inputs["Base Color"],
                principled_node.inputs["Alpha"],
            )
        # self.connect_value_node(b_mat, pymat.metallic_factor,sg.inputs["metallic"])
        # self.connect_value_node(b_mat, pymat.roughness_factor,sg.inputs["roughness"])
        # self.connect_value_node(b_mat, pymat.metallic_factor,sg.inputs["metallic"])
        # self.connect_value_node(b_mat, pymat.roughness_factor,sg.inputs["roughness"])
        if pymat.normal_texture_index is not None:
            self.connect_texture_node(
                b_mat, pymat.normal_texture_index, principled_node.inputs["Normal"]
            )

        transparent_exchange_dic = {
            "OPAQUE": "OPAQUE",
            "MASK": "CUTOUT",
            "Z_TRANSPARENCY": "Z_TRANSPARENCY",
        }
        self.set_material_transparent(
            b_mat, pymat, transparent_exchange_dic[pymat.alpha_mode]
        )
        b_mat.use_backface_culling = not pymat.double_sided

    def build_material_from_gltf(
        self, b_mat: bpy.types.Material, pymat: PyMaterialGltf
    ) -> None:
        self.material_init(b_mat)
        gltf_node_name = "GLTF"
        shader_node_group_import(gltf_node_name)
        sg = self.node_group_create(b_mat, gltf_node_name)
        b_mat.node_tree.links.new(
            b_mat.node_tree.nodes["Material Output"].inputs["Surface"],
            sg.outputs["BSDF"],
        )

        self.connect_rgb_node(b_mat, pymat.base_color, sg.inputs["base_Color"])
        if pymat.color_texture_index is not None:
            self.connect_texture_node(
                b_mat, pymat.color_texture_index, sg.inputs["color_texture"]
            )
        self.connect_value_node(b_mat, pymat.metallic_factor, sg.inputs["metallic"])
        self.connect_value_node(b_mat, pymat.roughness_factor, sg.inputs["roughness"])
        if pymat.metallic_roughness_texture_index is not None:
            self.connect_texture_node(
                b_mat,
                pymat.metallic_roughness_texture_index,
                sg.inputs["metallic_roughness_texture"],
            )
        if isinstance(pymat.emissive_factor, collections.Iterable):
            self.connect_rgb_node(
                b_mat, [*pymat.emissive_factor, 1], sg.inputs["emissive_color"]
            )
        if pymat.emissive_texture_index is not None:
            self.connect_texture_node(
                b_mat, pymat.emissive_texture_index, sg.inputs["emissive_texture"]
            )
        if pymat.normal_texture_index is not None:
            self.connect_texture_node(
                b_mat, pymat.normal_texture_index, sg.inputs["normal"]
            )
        if pymat.occlusion_texture_index is not None:
            self.connect_texture_node(
                b_mat, pymat.occlusion_texture_index, sg.inputs["occlusion_texture"]
            )
        self.connect_value_node(b_mat, pymat.shadeless, sg.inputs["unlit"])

        transparent_exchange_dic = {
            "OPAQUE": "OPAQUE",
            "MASK": "CUTOUT",
            "Z_TRANSPARENCY": "Z_TRANSPARENCY",
        }
        self.set_material_transparent(
            b_mat, pymat, transparent_exchange_dic[pymat.alpha_mode]
        )
        b_mat.use_backface_culling = not pymat.double_sided

    def build_material_from_mtoon(
        self, b_mat: bpy.types.Material, pymat: PyMaterialMtoon
    ) -> None:
        self.material_init(b_mat)

        shader_node_group_name = "MToon_unversioned"
        sphere_add_vector_node_group_name = "matcap_vector"
        shader_node_group_import(shader_node_group_name)
        shader_node_group_import(sphere_add_vector_node_group_name)

        sg = self.node_group_create(b_mat, shader_node_group_name)
        b_mat.node_tree.links.new(
            b_mat.node_tree.nodes["Material Output"].inputs["Surface"],
            sg.outputs["Emission"],
        )

        float_prop_exchange_dic = MaterialMtoon.float_props_exchange_dic
        for k, v in pymat.float_props_dic.items():
            if k == "_CullMode":
                if v == 2:  # 0: no cull 1:front cull 2:back cull
                    b_mat.use_backface_culling = True
                elif v == 0:
                    b_mat.use_backface_culling = False
            if k in [
                key for key, val in float_prop_exchange_dic.items() if val is not None
            ]:
                if v is not None:
                    self.connect_value_node(
                        b_mat, v, sg.inputs[float_prop_exchange_dic[k]]
                    )
            else:
                b_mat[k] = v

        for k, v in pymat.keyword_dic.items():
            b_mat[k] = v

        uv_offset_tiling_value: Sequence[float] = [0, 0, 1, 1]
        vector_props_dic = MaterialMtoon.vector_props_exchange_dic
        for k, vec in pymat.vector_props_dic.items():
            if k in ["_Color", "_ShadeColor", "_EmissionColor", "_OutlineColor"]:
                self.connect_rgb_node(
                    b_mat,
                    vec,
                    sg.inputs[vector_props_dic[k]],
                    default_color=[1, 1, 1, 1],
                )
            elif k == "_RimColor":
                self.connect_rgb_node(
                    b_mat,
                    vec,
                    sg.inputs[vector_props_dic[k]],
                    default_color=[0, 0, 0, 1],
                )
            elif k == "_MainTex" and vec is not None:
                uv_offset_tiling_value = vec
            else:
                b_mat[k] = vec

        uv_map_node = b_mat.node_tree.nodes.new("ShaderNodeUVMap")
        uv_offset_tiling_node = b_mat.node_tree.nodes.new("ShaderNodeMapping")
        if bpy.app.version < (2, 81):
            uv_offset_tiling_node.translation[0] = uv_offset_tiling_value[0]
            uv_offset_tiling_node.translation[1] = uv_offset_tiling_value[1]
            uv_offset_tiling_node.scale[0] = uv_offset_tiling_value[2]
            uv_offset_tiling_node.scale[1] = uv_offset_tiling_value[3]
        else:
            uv_offset_tiling_node.inputs["Location"].default_value[
                0
            ] = uv_offset_tiling_value[0]
            uv_offset_tiling_node.inputs["Location"].default_value[
                1
            ] = uv_offset_tiling_value[1]
            uv_offset_tiling_node.inputs["Scale"].default_value[
                0
            ] = uv_offset_tiling_value[2]
            uv_offset_tiling_node.inputs["Scale"].default_value[
                1
            ] = uv_offset_tiling_value[3]

        b_mat.node_tree.links.new(
            uv_offset_tiling_node.inputs[0], uv_map_node.outputs[0]
        )

        def connect_uv_map_to_texture(texture_node: bpy.types.ShaderNode) -> None:
            b_mat.node_tree.links.new(
                texture_node.inputs[0], uv_offset_tiling_node.outputs[0]
            )

        tex_dic = MaterialMtoon.texture_kind_exchange_dic

        for tex_name, tex_index in pymat.texture_index_dic.items():
            if tex_index is None:
                continue
            image_index = self.parse_result.json_dict["textures"][tex_index]["source"]
            if image_index not in self.images:
                continue
            if tex_name not in tex_dic:
                if "unknown_texture" not in b_mat:
                    b_mat["unknown_texture"] = {}
                b_mat["unknown_texture"].update(
                    {
                        tex_name: self.parse_result.json_dict["textures"][tex_index][
                            "name"
                        ]
                    }
                )
                print(f"unknown texture {tex_name}")
            elif tex_name == "_MainTex":
                main_tex_node = self.connect_texture_node(
                    b_mat,
                    tex_index,
                    sg.inputs[tex_dic[tex_name]],
                    sg.inputs[tex_dic[tex_name] + "Alpha"],
                )
                connect_uv_map_to_texture(main_tex_node)
            elif tex_name == "_BumpMap":
                # If .blend file already has VRM that is imported by older version,
                # 'sg' has old 'MToon_unversioned', which has 'inputs["NomalmapTexture"]'. # noqa: SC100
                # But 'tex_dic' holds name that is corrected, and it causes KeyError to reference 'sg' with it
                color_socket_name = "NomalmapTexture"
                if tex_dic[tex_name] in sg.inputs:
                    color_socket_name = tex_dic[tex_name]

                normalmap_node = self.connect_texture_node(
                    b_mat,
                    tex_index,
                    color_socket_to_connect=sg.inputs[color_socket_name],
                )
                try:
                    normalmap_node.image.colorspace_settings.name = "Non-Color"
                except TypeError:  # non-colorが無いとき
                    normalmap_node.image.colorspace_settings.name = (
                        "Linear"  # 2.80 beta互換性コード
                    )
                connect_uv_map_to_texture(normalmap_node)
            elif tex_name == "_ReceiveShadowTexture":
                rs_tex_node = self.connect_texture_node(
                    b_mat,
                    tex_index,
                    alpha_socket_to_connect=sg.inputs[tex_dic[tex_name] + "_alpha"],
                )
                connect_uv_map_to_texture(rs_tex_node)
            elif tex_name == "_SphereAdd":
                tex_node = self.connect_texture_node(
                    b_mat,
                    tex_index,
                    color_socket_to_connect=sg.inputs[tex_dic[tex_name]],
                )
                b_mat.node_tree.links.new(
                    tex_node.inputs["Vector"],
                    self.node_group_create(
                        b_mat, sphere_add_vector_node_group_name
                    ).outputs["Vector"],
                )
            else:
                if tex_dic.get(tex_name) is not None:  # Shade,Emissive,Rim,UVanimMask
                    other_tex_node = self.connect_texture_node(
                        b_mat,
                        tex_index,
                        color_socket_to_connect=sg.inputs[tex_dic[tex_name]],
                    )
                    connect_uv_map_to_texture(other_tex_node)
                else:
                    print(f"{tex_name} is unknown texture")

        transparent_mode_float = pymat.float_props_dic["_BlendMode"]
        transparent_mode = "OPAQUE"
        if transparent_mode_float is None:
            pass
        elif math.fabs(transparent_mode_float - 1) < 0.001:
            transparent_mode = "CUTOUT"
        elif (
            math.fabs(transparent_mode_float - 2) < 0.001
            or math.fabs(transparent_mode_float - 3) < 0.001
        ):
            # Trans_Zwrite(3)も2扱いで。
            transparent_mode = "Z_TRANSPARENCY"
        self.set_material_transparent(b_mat, pymat, transparent_mode)

    def build_material_from_transparent_z_write(
        self, b_mat: bpy.types.Material, pymat: PyMaterialTransparentZWrite
    ) -> None:
        self.material_init(b_mat)

        z_write_transparent_sg = "TRANSPARENT_ZWRITE"
        shader_node_group_import(z_write_transparent_sg)
        sg = self.node_group_create(b_mat, z_write_transparent_sg)
        b_mat.node_tree.links.new(
            b_mat.node_tree.nodes["Material Output"].inputs["Surface"],
            sg.outputs["Emission"],
        )

        for k, float_value in pymat.float_props_dic.items():
            b_mat[k] = float_value
        for k, vec_value in pymat.vector_props_dic.items():
            b_mat[k] = vec_value
        for tex_name, tex_index_value in pymat.texture_index_dic.items():
            if tex_name == "_MainTex" and tex_index_value is not None:
                self.connect_texture_node(
                    b_mat,
                    tex_index_value,
                    sg.inputs["Main_Texture"],
                    sg.inputs["Main_Alpha"],
                )
        self.set_material_transparent(b_mat, pymat, "Z_TRANSPARENCY")

    # endregion material

    def attach_vrm_attributes(self) -> None:
        armature = self.armature
        if not armature:
            return
        addon_extension = armature.data.vrm_addon_extension
        if not isinstance(addon_extension, VrmAddonArmatureExtensionPropertyGroup):
            return
        vrm0 = addon_extension.vrm0
        if not isinstance(vrm0, Vrm0PropertyGroup):
            return

        if self.parse_result.spec_version_number >= (1, 0):
            return

        vrm0_extension = self.parse_result.vrm0_extension

        addon_extension.addon_version = common.version.version()

        textblock = bpy.data.texts.new(name="vrm.json")
        textblock.write(json.dumps(self.parse_result.json_dict, indent=4))

        self.load_vrm0_meta(vrm0.meta, vrm0_extension.get("meta"))
        self.load_vrm0_humanoid(vrm0.humanoid, vrm0_extension.get("humanoid"))
        self.load_vrm0_first_person(
            vrm0.first_person, vrm0_extension.get("firstPerson")
        )
        self.load_vrm0_blend_shape_master(
            vrm0.blend_shape_master, vrm0_extension.get("blendShapeMaster")
        )
        self.load_vrm0_secondary_animation(
            vrm0.secondary_animation, vrm0_extension.get("secondaryAnimation")
        )
        migration.migrate(armature.name, defer=False)

    def load_vrm0_meta(self, meta_props: Vrm0MetaPropertyGroup, meta_dict: Any) -> None:
        if not isinstance(meta_dict, dict):
            return

        title = meta_dict.get("title")
        if isinstance(title, str):
            meta_props.title = title

        version = meta_dict.get("version")
        if isinstance(version, str):
            meta_props.version = version

        author = meta_dict.get("author")
        if isinstance(author, str):
            meta_props.author = author

        contact_information = meta_dict.get("contactInformation")
        if isinstance(contact_information, str):
            meta_props.contact_information = contact_information

        reference = meta_dict.get("reference")
        if isinstance(reference, str):
            meta_props.reference = reference

        allowed_user_name = meta_dict.get("allowedUserName")
        if isinstance(allowed_user_name, str):
            meta_props.allowed_user_name = allowed_user_name

        violent_ussage_name = meta_dict.get("violentUssageName")  # noqa: SC200
        if isinstance(violent_ussage_name, str):  # noqa: SC200
            meta_props.violent_ussage_name = violent_ussage_name  # noqa: SC200

        sexual_ussage_name = meta_dict.get("sexualUssageName")  # noqa: SC200
        if isinstance(sexual_ussage_name, str):  # noqa: SC200
            meta_props.sexual_ussage_name = sexual_ussage_name  # noqa: SC200

        commercial_ussage_name = meta_dict.get("commercialUssageName")  # noqa: SC200
        if isinstance(commercial_ussage_name, str):  # noqa: SC200
            meta_props.commercial_ussage_name = commercial_ussage_name  # noqa: SC200

        other_permission_url = meta_dict.get("otherPermissionUrl")
        if isinstance(other_permission_url, str):
            meta_props.other_permission_url = other_permission_url

        license_name = meta_dict.get("licenseName")
        if isinstance(license_name, str):
            meta_props.license_name = license_name

        other_license_url = meta_dict.get("otherLicenseUrl")
        if isinstance(other_license_url, str):
            meta_props.other_license_url = other_license_url

        texture = meta_dict.get("texture")
        if (
            isinstance(texture, int)
            and "textures" in self.parse_result.json_dict
            # extensions.VRM.meta.texture could be -1
            # https://github.com/vrm-c/UniVRM/issues/91#issuecomment-454284964
            and 0 <= texture < len(self.parse_result.json_dict["textures"])
        ):
            image_index = self.parse_result.json_dict["textures"][texture]["source"]
            if image_index in self.images:
                meta_props.texture = self.images[image_index]

    def load_vrm0_humanoid(
        self, humanoid_props: Vrm0HumanoidPropertyGroup, humanoid_dict: Any
    ) -> None:
        if not isinstance(humanoid_dict, dict):
            return
        human_bones = humanoid_dict.get("humanBones")
        if isinstance(human_bones, collections.Iterable):
            for human_bone_dict in human_bones:
                if not isinstance(human_bone_dict, dict):
                    continue

                bone = human_bone_dict.get("bone")
                if bone not in HumanBones.all_names:
                    continue
                if any(
                    human_bone_props.bone == bone
                    for human_bone_props in humanoid_props.human_bones
                ):
                    print(f'Duplicated bone: "{bone}"')
                    continue

                node = human_bone_dict.get("node")
                if not isinstance(node, int) or node not in self.bone_names:
                    continue

                human_bone_props = humanoid_props.human_bones.add()
                human_bone_props.bone = bone
                human_bone_props.node.value = self.bone_names[node]

                use_default_values = human_bone_dict.get("useDefaultValues")
                if isinstance(use_default_values, bool):
                    human_bone_props.use_default_values = use_default_values

                min_ = convert.vrm_json_vector3_to_tuple(human_bone_dict.get("min"))
                if min_ is not None:
                    human_bone_props.min = min_

                max_ = convert.vrm_json_vector3_to_tuple(human_bone_dict.get("max"))
                if max_ is not None:
                    human_bone_props.max = max_

                center = convert.vrm_json_vector3_to_tuple(
                    human_bone_dict.get("center")
                )
                if center is not None:
                    human_bone_props.center = center

                axis_length = human_bone_dict.get("axisLength")
                if isinstance(axis_length, (int, float)):
                    human_bone_props.axis_length = axis_length

        arm_stretch = humanoid_dict.get("armStretch")
        if isinstance(arm_stretch, (int, float)):
            humanoid_props.arm_stretch = arm_stretch

        leg_stretch = humanoid_dict.get("legStretch")
        if isinstance(leg_stretch, (int, float)):
            humanoid_props.leg_stretch = leg_stretch

        upper_arm_twist = humanoid_dict.get("upperArmTwist")
        if isinstance(upper_arm_twist, (int, float)):
            humanoid_props.upper_arm_twist = upper_arm_twist

        lower_arm_twist = humanoid_dict.get("lowerArmTwist")
        if isinstance(lower_arm_twist, (int, float)):
            humanoid_props.lower_arm_twist = lower_arm_twist

        upper_leg_twist = humanoid_dict.get("upperLegTwist")
        if isinstance(upper_leg_twist, (int, float)):
            humanoid_props.upper_leg_twist = upper_leg_twist

        lower_leg_twist = humanoid_dict.get("lowerLegTwist")
        if isinstance(lower_leg_twist, (int, float)):
            humanoid_props.lower_leg_twist = lower_leg_twist

        feet_spacing = humanoid_dict.get("feetSpacing")
        if isinstance(feet_spacing, (int, float)):
            humanoid_props.feet_spacing = feet_spacing

        has_translation_dof = humanoid_dict.get("hasTranslationDoF")
        if isinstance(has_translation_dof, bool):
            humanoid_props.has_translation_dof = has_translation_dof

    def load_vrm0_first_person(
        self,
        first_person_props: Vrm0FirstPersonPropertyGroup,
        first_person_dict: Any,
    ) -> None:
        if not isinstance(first_person_dict, dict):
            return

        first_person_bone = first_person_dict.get("firstPersonBone")
        if isinstance(first_person_bone, int) and first_person_bone in self.bone_names:
            first_person_props.first_person_bone.value = self.bone_names[
                first_person_bone
            ]

        first_person_bone_offset = convert.vrm_json_vector3_to_tuple(
            first_person_dict.get("firstPersonBoneOffset")
        )
        if first_person_bone_offset is not None:
            # Axis confusing
            (x, y, z) = first_person_bone_offset
            first_person_props.first_person_bone_offset = (x, z, y)

        mesh_annotations = first_person_dict.get("meshAnnotations")
        if isinstance(mesh_annotations, collections.Iterable):
            for mesh_annotation_dict in mesh_annotations:
                mesh_annotation_props = first_person_props.mesh_annotations.add()

                if not isinstance(mesh_annotation_dict, dict):
                    continue

                mesh = mesh_annotation_dict.get("mesh")
                if isinstance(mesh, int) and mesh in self.meshes:
                    mesh_annotation_props.mesh.value = self.meshes[mesh].data.name

                first_person_flag = mesh_annotation_dict.get("firstPersonFlag")
                if isinstance(first_person_flag, str):
                    mesh_annotation_props.first_person_flag = first_person_flag

        look_at_type_name = first_person_dict.get("lookAtTypeName")
        if look_at_type_name in ["Bone", "BlendShape"]:
            first_person_props.look_at_type_name = look_at_type_name

        for (look_at_props, look_at_dict) in [
            (
                first_person_props.look_at_horizontal_inner,
                first_person_dict.get("lookAtHorizontalInner"),
            ),
            (
                first_person_props.look_at_horizontal_outer,
                first_person_dict.get("lookAtHorizontalOuter"),
            ),
            (
                first_person_props.look_at_vertical_down,
                first_person_dict.get("lookAtVerticalDown"),
            ),
            (
                first_person_props.look_at_vertical_up,
                first_person_dict.get("lookAtVerticalUp"),
            ),
        ]:
            if not isinstance(look_at_dict, dict):
                continue

            curve = convert.vrm_json_curve_to_list(look_at_dict.get("curve"))
            if curve is not None:
                look_at_props.curve = curve

            x_range = look_at_dict.get("xRange")
            if isinstance(x_range, (float, int)):
                look_at_props.x_range = x_range

            y_range = look_at_dict.get("yRange")
            if isinstance(y_range, (float, int)):
                look_at_props.y_range = y_range

    def load_vrm0_blend_shape_master(
        self,
        blend_shape_master_props: Vrm0BlendShapeMasterPropertyGroup,
        blend_shape_master_dict: Any,
    ) -> None:
        if not isinstance(blend_shape_master_dict, dict):
            return
        blend_shape_groups = blend_shape_master_dict.get("blendShapeGroups")
        if not isinstance(blend_shape_groups, collections.Iterable):
            return

        for blend_shape_group_dict in blend_shape_groups:
            blend_shape_group_props = blend_shape_master_props.blend_shape_groups.add()

            if not isinstance(blend_shape_group_dict, dict):
                continue

            name = blend_shape_group_dict.get("name")
            if name is not None:
                blend_shape_group_props.name = name

            preset_name = blend_shape_group_dict.get("presetName")
            if preset_name is not None:
                blend_shape_group_props.preset_name = preset_name

            binds = blend_shape_group_dict.get("binds")
            if isinstance(binds, collections.Iterable):
                for bind_dict in binds:
                    if not isinstance(bind_dict, dict):
                        continue

                    mesh = bind_dict.get("mesh")
                    if not isinstance(mesh, int) or mesh not in self.meshes:
                        continue

                    index = bind_dict.get("index")
                    if not isinstance(index, int) or not (
                        1
                        <= (index + 1)
                        < len(self.meshes[mesh].data.shape_keys.key_blocks)
                    ):
                        continue

                    weight = bind_dict.get("weight")
                    if not isinstance(weight, (int, float)):
                        weight = 0

                    bind_props = blend_shape_group_props.binds.add()
                    bind_props.mesh.value = self.meshes[mesh].data.name
                    bind_props.index = self.meshes[
                        mesh
                    ].data.shape_keys.key_blocks.keys()[index + 1]
                    bind_props.weight = min(max(weight / 100.0, 0), 1)

            material_values = blend_shape_group_dict.get("materialValues")
            if isinstance(material_values, collections.Iterable):
                for material_value_dict in material_values:
                    material_value_props = blend_shape_group_props.material_values.add()

                    if not isinstance(material_value_dict, dict):
                        continue

                    material_name = material_value_dict.get("materialName")
                    if (
                        isinstance(material_name, str)
                        and material_name in bpy.data.materials
                    ):
                        material_value_props.material = bpy.data.materials[
                            material_name
                        ]

                    property_name = material_value_dict.get("propertyName")
                    if isinstance(property_name, str):
                        material_value_props.property_name = property_name

                    target_value = material_value_dict.get("targetValue")
                    if isinstance(target_value, collections.Iterable):
                        for target_value_element in target_value:
                            if not isinstance(target_value_element, (int, float)):
                                target_value_element = 0
                            target_value_element_props = (
                                material_value_props.target_value.add()
                            )
                            target_value_element_props.value = target_value_element

            is_binary = blend_shape_group_dict.get("isBinary")
            if isinstance(is_binary, bool):
                blend_shape_group_props.is_binary = is_binary

    def load_vrm0_secondary_animation(
        self,
        secondary_animation_props: Vrm0SecondaryAnimationPropertyGroup,
        secondary_animation_dict: Any,
    ) -> None:
        if not isinstance(secondary_animation_dict, dict):
            return
        armature = self.armature
        if armature is None:
            raise Exception("armature is None")

        collider_groups = secondary_animation_dict.get("colliderGroups")
        if not isinstance(collider_groups, collections.Iterable):
            collider_groups = []

        bpy.context.view_layer.depsgraph.update()
        bpy.context.scene.view_layers.update()
        collider_objs = []
        for collider_group_dict in collider_groups:
            collider_group_props = secondary_animation_props.collider_groups.add()
            collider_group_props.uuid = uuid.uuid4().hex

            if not isinstance(collider_group_dict, dict):
                continue

            node = collider_group_dict.get("node")
            if not isinstance(node, int) or node not in self.bone_names:
                continue

            bone_name = self.bone_names[node]
            collider_group_props.node.value = bone_name
            colliders = collider_group_dict.get("colliders")
            if not isinstance(colliders, collections.Iterable):
                continue

            for collider_index, collider_dict in enumerate(colliders):
                collider_props = collider_group_props.colliders.add()

                if not isinstance(collider_dict, dict):
                    continue

                offset = convert.vrm_json_vector3_to_tuple(collider_dict.get("offset"))
                if offset is None:
                    offset = (0, 0, 0)

                radius = collider_dict.get("radius")
                if not isinstance(radius, (int, float)):
                    radius = 0

                collider_name = f"{bone_name}_collider_{collider_index}"
                obj = bpy.data.objects.new(name=collider_name, object_data=None)
                collider_props.blender_object = obj
                obj.parent = self.armature
                obj.parent_type = "BONE"
                obj.parent_bone = bone_name
                fixed_offset = [
                    offset[axis] * inv for axis, inv in zip([0, 2, 1], [-1, -1, 1])
                ]  # TODO: Y軸反転はUniVRMのシリアライズに合わせてる

                # boneのtail側にparentされるので、根元からのpositionに動かしなおす
                obj.matrix_world = Matrix.Translation(
                    [
                        armature.matrix_world.to_translation()[i]
                        + armature.data.bones[bone_name].matrix_local.to_translation()[
                            i
                        ]
                        + fixed_offset[i]
                        for i in range(3)
                    ]
                )

                obj.empty_display_size = radius
                obj.empty_display_type = "SPHERE"
                collider_objs.append(obj)
        if collider_objs:
            colliders_collection = bpy.data.collections.new("Colliders")
            self.context.scene.collection.children.link(colliders_collection)
            for collider_obj in collider_objs:
                colliders_collection.objects.link(collider_obj)

        bone_groups = secondary_animation_dict.get("boneGroups")
        if not isinstance(bone_groups, collections.Iterable):
            bone_groups = []

        for bone_group_dict in bone_groups:
            bone_group_props = secondary_animation_props.bone_groups.add()

            if not isinstance(bone_group_dict, dict):
                bone_group_props.refresh(armature)
                continue

            comment = bone_group_dict.get("comment")
            if isinstance(comment, str):
                bone_group_props.comment = comment

            stiffiness = bone_group_dict.get("stiffiness")  # noqa: SC200
            if isinstance(stiffiness, (int, float)):  # noqa: SC200
                bone_group_props.stiffiness = stiffiness  # noqa: SC200

            gravity_power = bone_group_dict.get("gravityPower")
            if isinstance(gravity_power, (int, float)):
                bone_group_props.gravity_power = gravity_power

            gravity_dir = convert.vrm_json_vector3_to_tuple(
                bone_group_dict.get("gravityDir")
            )
            if gravity_dir is not None:
                # Axis confusing
                (x, y, z) = gravity_dir
                bone_group_props.gravity_dir = (x, z, y)

            drag_force = bone_group_dict.get("dragForce")
            if isinstance(drag_force, (int, float)):
                bone_group_props.drag_force = drag_force

            center = bone_group_dict.get("center")
            if isinstance(center, int) and center in self.bone_names:
                bone_group_props.center.value = self.bone_names[center]

            hit_radius = bone_group_dict.get("hitRadius")
            if isinstance(hit_radius, (int, float)):
                bone_group_props.hit_radius = hit_radius

            bones = bone_group_dict.get("bones")
            if isinstance(bones, collections.Iterable):
                for bone in bones:
                    bone_prop = bone_group_props.bones.add()
                    if not isinstance(bone, int) or bone not in self.bone_names:
                        continue

                    bone_prop.value = self.bone_names[bone]

            collider_groups = bone_group_dict.get("colliderGroups")
            if isinstance(collider_groups, collections.Iterable):
                for collider_group in collider_groups:
                    if not isinstance(collider_group, int) and not (
                        0
                        <= collider_group
                        < len(secondary_animation_props.collider_groups)
                    ):
                        continue
                    collider_group_uuid_props = bone_group_props.collider_groups.add()
                    collider_group_uuid_props.value = (
                        secondary_animation_props.collider_groups[collider_group].uuid
                    )

        for bone_group_props in secondary_animation_props.bone_groups:
            bone_group_props.refresh(armature)

        for collider_group_props in secondary_animation_props.collider_groups:
            collider_group_props.refresh(armature)

    def cleaning_data(self) -> None:
        # collection setting
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        for obj in self.meshes.values():
            self.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.shade_smooth()
            bpy.ops.object.select_all(action="DESELECT")

    def make_pole_target(
        self, rl: str, upper_leg_name: str, lower_leg_name: str, foot_name: str
    ) -> None:
        armature = self.armature
        if armature is None:
            raise Exception("armature is None")

        bpy.ops.object.mode_set(mode="EDIT")
        edit_bones = armature.data.edit_bones

        ik_foot = armature.data.edit_bones.new(f"IK_LEG_TARGET_{rl}")
        ik_foot.head = [f + o for f, o in zip(edit_bones[foot_name].head[:], [0, 0, 0])]
        ik_foot.tail = [
            f + o for f, o in zip(edit_bones[foot_name].head[:], [0, -0.2, 0])
        ]

        pole = armature.data.edit_bones.new(f"leg_pole_{rl}")
        pole.parent = ik_foot
        pole.head = [
            f + o for f, o in zip(edit_bones[lower_leg_name].head[:], [0, -0.1, 0])
        ]
        pole.tail = [
            f + o for f, o in zip(edit_bones[lower_leg_name].head[:], [0, -0.2, 0])
        ]

        pole_name = copy.copy(pole.name)
        ik_foot_name = copy.copy(ik_foot.name)
        bpy.context.view_layer.depsgraph.update()
        bpy.context.scene.view_layers.update()
        bpy.ops.object.mode_set(mode="POSE")
        ikc = armature.pose.bones[lower_leg_name].constraints.new("IK")
        ikc.target = armature
        ikc.subtarget = armature.pose.bones[ik_foot_name].name

        def chain_solver(armature: bpy.types.Armature, child: str, parent: str) -> int:
            current_bone = armature.pose.bones[child]
            for i in range(10):
                if current_bone.name == parent:
                    return i + 1
                current_bone = current_bone.parent
            return 11

        ikc.chain_count = chain_solver(armature, lower_leg_name, upper_leg_name)

        ikc.pole_target = self.armature
        ikc.pole_subtarget = pole_name
        bpy.context.view_layer.depsgraph.update()
        bpy.context.scene.view_layers.update()

    def blendfy(self) -> None:
        armature = self.armature
        if armature is None:
            raise Exception("armature is None")
        bpy.context.view_layer.objects.active = self.armature
        bpy.ops.object.mode_set(mode="EDIT")

        right_upper_leg_name = armature.data["rightUpperLeg"]
        right_lower_leg_name = armature.data["rightLowerLeg"]
        right_foot_name = armature.data["rightFoot"]

        left_upper_leg_name = armature.data["leftUpperLeg"]
        left_lower_leg_name = armature.data["leftLowerLeg"]
        left_foot_name = armature.data["leftFoot"]

        self.make_pole_target(
            "R", right_upper_leg_name, right_lower_leg_name, right_foot_name
        )
        self.make_pole_target(
            "L", left_upper_leg_name, left_lower_leg_name, left_foot_name
        )

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.view_layer.depsgraph.update()
        bpy.context.scene.view_layers.update()
        operator.VRM_OT_simplify_vroid_bones(bpy.context)


# DeprecationWarning
class ICYP_OT_select_helper(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "mesh.icyp_select_helper"
    bl_label = "VRM importer internal only func"
    bl_description = "VRM importer internal only"
    bl_options = {"REGISTER", "UNDO"}

    bpy.types.Scene.icyp_select_helper_select_list = []

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        bpy.ops.object.mode_set(mode="OBJECT")
        for vid in bpy.types.Scene.icyp_select_helper_select_list:
            bpy.context.active_object.data.vertices[vid].select = True
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.types.Scene.icyp_select_helper_select_list = []
        return {"FINISHED"}
