"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""


import bpy
from mathutils import Vector, Matrix
from .. import vrm_types
from ..misc import vrm_helper
from ..vrm_types import nested_json_value_getter as json_get
from ..gl_constants import GlConstants
from math import sqrt, pow, radians
import numpy
import sys
import os.path
import json
import copy


class BlendModel:
    def __init__(self, context, vrm_pydata, addon_context):
        self.is_put_spring_bone_info = addon_context.is_put_spring_bone_info
        self.import_normal = addon_context.import_normal
        self.remove_doubles = addon_context.remove_doubles
        self.use_simple_principled_material = (
            addon_context.use_simple_principled_material
        )
        self.is_set_bone_roll = addon_context.set_bone_roll
        self.use_in_blender = addon_context.use_in_blender

        self.context = context
        self.vrm_pydata = vrm_pydata
        self.textures = None  # TODO: The index of self.textures is image index. See self.texture_load(). Will fix it.
        self.armature = None
        self.bones = None
        self.material_dict = None
        self.primitive_obj_dict = None
        self.mesh_joined_objects = None
        model_name = json_get(
            self.vrm_pydata.json,
            ["extensions", vrm_types.VRM, "meta", "title"],
            "vrm_model",
        )
        self.model_collection = bpy.data.collections.new(f"{model_name}_collection")
        self.context.scene.collection.children.link(self.model_collection)
        self.vrm_model_build()

    def vrm_model_build(self):
        wm = bpy.context.window_manager
        wm.progress_begin(0, 11)
        i = 1

        def prog(z):
            z = z + 1
            wm.progress_update(i)
            return z

        affected_object = self.scene_init()
        i = prog(i)
        self.texture_load()
        i = prog(i)
        self.make_armature()
        i = prog(i)
        self.make_material()
        i = prog(i)
        self.make_primitive_mesh_objects(wm, i)
        # i=prog(i) ↑関数内でやる
        self.json_dump()
        i = prog(i)
        self.attach_vrm_attributes()
        i = prog(i)
        self.cleaning_data()
        i = prog(i)
        if self.is_set_bone_roll:
            self.set_bone_roll()
        if self.is_put_spring_bone_info:
            self.put_spring_bone_info()
        if self.use_in_blender:
            pass
            # self.blendfy()
        i = prog(i)
        self.connect_bones()
        i = prog(i)
        self.finishing(affected_object)
        wm.progress_end()
        return 0

    @staticmethod
    def axis_glb_to_blender(vec3):
        return [vec3[i] * t for i, t in zip([0, 2, 1], [-1, 1, 1])]

    def connect_bones(self):
        # Blender_VRMAutoIKSetup (MIT License)
        # https://booth.pm/ja/items/1697977
        previous_active = bpy.context.view_layer.objects.active
        try:
            bpy.context.view_layer.objects.active = self.armature  # アーマチャーをアクティブに
            bpy.ops.object.mode_set(mode="EDIT")  # エディットモードに入る
            disconnected_bone_names = []  # 結合されてないボーンのリスト
            if self.vrm_pydata.json["extensions"][vrm_types.VRM][
                "exporterVersion"
            ].startswith("VRoidStudio-"):
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
                        disconnected_bone = self.armature.data.edit_bones[
                            disconnected_bone_name
                        ]
                        # 処理対象の親ボーンのTailと処理対象のHeadを一致させる
                        disconnected_bone.parent.tail = disconnected_bone.head
                if bone.parent:  # 親ボーンがある場合
                    # ボーンのヘッドと親ボーンのテールが一致していたら
                    if (
                        numpy.abs(
                            numpy.array(bone.head) - numpy.array(bone.parent.tail)
                        )
                        < sys.float_info.epsilon
                    ).all():
                        bone.use_connect = True  # ボーンの関係の接続を有効に
            bpy.ops.object.mode_set(mode="OBJECT")
        finally:
            bpy.context.view_layer.objects.active = previous_active

    def scene_init(self):
        # active_objectがhideだとbpy.ops.object.mode_set.poll()に失敗してエラーが出るのでその回避と、それを元に戻す
        affected_object = None
        if self.context.active_object is not None:
            if hasattr(self.context.active_object, "hide_viewport"):
                if self.context.active_object.hide_viewport:
                    self.context.active_object.hide_viewport = False
                    affected_object = self.context.active_object
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")
        return affected_object

    def finishing(self, affected_object):
        # initで弄ったやつを戻す
        if affected_object is not None:
            affected_object.hide_viewport = True
        return

        # image_path_to Texture

    def texture_load(self):
        self.textures = []
        for image_props in self.vrm_pydata.image_properties:
            img = bpy.data.images.load(image_props.filepath)
            tex = bpy.data.textures.new(name=image_props.name, type="IMAGE")
            tex.image = img
            self.textures.append(tex)

        json_texture_index = json_get(
            self.vrm_pydata.json, ["extensions", vrm_types.VRM, "meta", "texture"]
        )
        if json_texture_index not in (-1, None):
            if (
                "textures" in self.vrm_pydata.json
                and len(self.vrm_pydata.json["textures"]) > json_texture_index
            ):
                texture_index = self.vrm_pydata.json["textures"][json_texture_index][
                    "source"
                ]
                self.textures[texture_index].image.use_fake_user = True

        return

    def make_armature(self):
        # build bones as armature
        bpy.ops.object.add(type="ARMATURE", enter_editmode=True, location=(0, 0, 0))
        self.armature = self.context.object
        self.model_collection.objects.link(self.armature)
        self.armature.name = "skeleton"
        self.armature.show_in_front = True
        self.armature.data.display_type = "STICK"
        self.bones = dict()
        armature_edit_bones = dict()

        # region bone recursive func
        def bone_chain(node_id, parent_node_id):
            if node_id == -1:  # 自身がrootのrootの時
                return

            py_bone = self.vrm_pydata.nodes_dict[node_id]
            if py_bone.blend_bone:  # すでに割り当て済みのボーンが出てきたとき、その親の位置に動かす
                if parent_node_id == -1 or py_bone.blend_bone.parent is not None:
                    return
                py_bone.blend_bone.parent = self.bones[parent_node_id]
                li = [py_bone.blend_bone]
                while li:
                    bo = li.pop()
                    bo.translate(self.bones[parent_node_id].head)
                    for ch in bo.children:
                        li.append(ch)
                return
            if py_bone.mesh_id is not None and py_bone.children is None:
                return  # 子がなく、mesh属性を持つnodeはboneを生成しない
            b = armature_edit_bones[node_id]
            py_bone.name = b.name
            py_bone.blend_bone = b
            if parent_node_id == -1:
                parent_pos = [0, 0, 0]
            else:
                parent_pos = self.bones[parent_node_id].head
            b.head = numpy.array(parent_pos) + numpy.array(
                self.axis_glb_to_blender(py_bone.position)
            )

            # region temporary tail pos(gltf doesn't have bone. there defines as joints )
            def vector_length(bone_vector):
                return sqrt(
                    pow(bone_vector[0], 2)
                    + pow(bone_vector[1], 2)
                    + pow(bone_vector[2], 2)
                )

            # gltfは関節で定義されていて骨の長さとか向きとかないからまあなんかそれっぽい方向にボーンを向けて伸ばしたり縮めたり
            if py_bone.children is None:
                if parent_node_id == -1:  # 唯我独尊:上向けとけ
                    b.tail = [b.head[0], b.head[1] + 0.05, b.head[2]]
                else:  # normalize length to 0.03 末代:親から距離をちょっととる感じ
                    # 0除算除けと気分
                    length = max(
                        0.01,
                        vector_length(self.axis_glb_to_blender(py_bone.position)) * 30,
                    )
                    pos_diff = [
                        self.axis_glb_to_blender(py_bone.position)[i] / length
                        for i in range(3)
                    ]
                    if vector_length(pos_diff) <= 0.001:
                        # ボーンの長さが1mm以下なら上に10cm延ばす 長さが0だとOBJECT MODEに戻った時にボーンが消えるので上向けとく
                        pos_diff[1] += 0.01
                    b.tail = [b.head[i] + pos_diff[i] for i in range(3)]
            else:  # 子供たちの方向の中間を見る
                mean_relate_pos = numpy.array([0.0, 0.0, 0.0], dtype=numpy.float)
                count = 0
                for child_id in py_bone.children:
                    count += 1
                    mean_relate_pos += self.axis_glb_to_blender(
                        self.vrm_pydata.nodes_dict[child_id].position
                    )
                mean_relate_pos = mean_relate_pos / count
                if vector_length(mean_relate_pos) <= 0.001:  # ボーンの長さが1mm以下なら上に10cm延ばす
                    mean_relate_pos[1] += 0.1

                b.tail = [b.head[i] + mean_relate_pos[i] for i in range(3)]

            # endregion tail pos
            self.bones[node_id] = b

            if parent_node_id != -1:
                b.parent = self.bones[parent_node_id]
            if py_bone.children is not None:
                for x in py_bone.children:
                    bone_nodes.append((x, node_id))

        # endregion bone recursive func
        root_node_set = list(dict.fromkeys(self.vrm_pydata.skins_root_node_list))
        root_nodes = (
            root_node_set
            if root_node_set
            else [
                node
                for scene in self.vrm_pydata.json["scenes"]
                for node in scene["nodes"]
            ]
        )

        # generate edit_bones sorted by node_id for deterministic vrm output
        def find_connected_node_ids(parent_node_ids):
            node_ids = set(parent_node_ids)
            for parent_node_id in parent_node_ids:
                py_bone = self.vrm_pydata.nodes_dict[parent_node_id]
                if py_bone.children is not None:
                    node_ids |= find_connected_node_ids(py_bone.children)
            return node_ids

        for node_id in sorted(find_connected_node_ids(root_nodes)):
            bone_name = self.vrm_pydata.nodes_dict[node_id].name
            armature_edit_bones[node_id] = self.armature.data.edit_bones.new(bone_name)

        bone_nodes = [(root_node, -1) for root_node in root_nodes]
        while len(bone_nodes):
            bone_chain(*bone_nodes.pop())
        # call when bone built
        self.context.scene.view_layers.update()
        bpy.ops.object.mode_set(mode="OBJECT")
        try:
            for coll in self.armature.users_collection:
                if coll.name != self.model_collection.name:
                    coll.objects.unlink(self.armature)
        except Exception:
            print("Master collection doesn't have armature obj")
            pass
        return

    # region material
    def make_material(self):
        # Material_datas 適当なので要調整
        self.material_dict = dict()
        for index, mat in enumerate(self.vrm_pydata.materials):
            b_mat = bpy.data.materials.new(mat.name)
            if self.use_simple_principled_material:
                self.build_principle_from_gltf_mat(b_mat, mat)
            else:
                b_mat["shader_name"] = mat.shader_name
                if type(mat) == vrm_types.MaterialGltf:
                    self.build_material_from_gltf(b_mat, mat)
                elif type(mat) == vrm_types.MaterialMtoon:
                    self.build_material_from_mtoon(b_mat, mat)
                elif type(mat) == vrm_types.MaterialTransparentZWrite:
                    self.build_material_from_transparent_z_write(b_mat, mat)
                else:
                    print(f"unknown material {mat.name}")
            self.node_placer(b_mat.node_tree.nodes["Material Output"])
            self.material_dict[index] = b_mat
        return

    # region material_util func
    def set_material_transparent(self, b_mat, pymat, transparent_mode):
        if transparent_mode == "OPAQUE":
            pass
        elif transparent_mode == "CUTOUT":
            b_mat.blend_method = "CLIP"
            if pymat.shader_name == "VRM/MToon":
                b_mat.alpha_threshold = (
                    pymat.float_props_dic.get("_Cutoff")
                    if pymat.float_props_dic.get("_Cutoff")
                    else 0.5
                )
            else:
                b_mat.alpha_threshold = (
                    pymat.alphaCutoff if "alphaCutoff" in dir(pymat) else 0.5
                )
            b_mat.shadow_method = "CLIP"
        else:  # Z_TRANSPARENCY or Z()_zwrite
            if "transparent_shadow_method" in dir(b_mat):  # old blender280_beta
                b_mat.blend_method = "HASHED"
                b_mat.transparent_shadow_method = "HASHED"
            else:
                b_mat.blend_method = "HASHED"
                b_mat.shadow_method = "HASHED"
        return

    def material_init(self, b_mat):
        b_mat.use_nodes = True
        for node in b_mat.node_tree.nodes:
            if node.type != "OUTPUT_MATERIAL":
                b_mat.node_tree.nodes.remove(node)
        return

    def connect_value_node(self, material, value, socket_to_connect):
        if value is None:
            return None
        value_node = material.node_tree.nodes.new("ShaderNodeValue")
        value_node.label = socket_to_connect.name
        value_node.outputs[0].default_value = value
        material.node_tree.links.new(socket_to_connect, value_node.outputs[0])
        return value_node

    def connect_rgb_node(self, material, color, socket_to_connect, default_color=None):
        rgb_node = material.node_tree.nodes.new("ShaderNodeRGB")
        rgb_node.label = socket_to_connect.name
        rgb_node.outputs[0].default_value = (
            color if color else (default_color if default_color else [1, 1, 1, 1])
        )
        material.node_tree.links.new(socket_to_connect, rgb_node.outputs[0])
        return rgb_node

    def connect_texture_node(
        self,
        material,
        tex_index,
        color_socket_to_connect=None,
        alpha_socket_to_connect=None,
    ):
        if tex_index is None:
            return None
        tex = self.vrm_pydata.json["textures"][tex_index]
        sampler = (
            self.vrm_pydata.json["samplers"][tex["sampler"]]
            if "samplers" in self.vrm_pydata.json
            else [{"wrapS": GlConstants.REPEAT, "magFilter": GlConstants.LINEAR}]
        )
        image_node = material.node_tree.nodes.new("ShaderNodeTexImage")
        image_node.image = self.textures[tex["source"]].image
        if color_socket_to_connect is not None:
            image_node.label = color_socket_to_connect.name
        elif alpha_socket_to_connect is not None:
            image_node.label = alpha_socket_to_connect.name
        else:
            image_node.label = "what_is_this_node"
        # blender is ('Linear', 'Closest', 'Cubic', 'Smart') gltf is Linear, Closest
        filter_type = (
            sampler["magFilter"] if "magFilter" in sampler else GlConstants.LINEAR
        )
        if filter_type == GlConstants.NEAREST:
            image_node.interpolation = "Closest"
        else:
            image_node.interpolation = "Linear"
        # blender is ('REPEAT', 'EXTEND', 'CLIP') gltf is CLAMP_TO_EDGE,MIRRORED_REPEAT,REPEAT
        wrap_type = sampler["wrapS"] if "wrapS" in sampler else GlConstants.REPEAT
        if wrap_type in (GlConstants.REPEAT, GlConstants.MIRRORED_REPEAT):
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
        self, material, color, tex_index, socket_to_connect
    ):
        multiply_node = material.node_tree.nodes.new("ShaderNodeMixRGB")
        multiply_node.blend_type = "MULTIPLY"
        self.connect_rgb_node(material, color, multiply_node.inputs[1])
        self.connect_texture_node(material, tex_index, multiply_node.inputs[2])
        material.node_tree.links.new(socket_to_connect, multiply_node.outputs[0])
        return multiply_node

    def node_group_import(self, shader_node_group_name):
        if shader_node_group_name not in bpy.data.node_groups:
            filedir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "resources",
                "material_node_groups.blend",
                "NodeTree",
            )
            filepath = os.path.join(filedir, shader_node_group_name)
            bpy.ops.wm.append(
                filepath=filepath, filename=shader_node_group_name, directory=filedir
            )

    def node_group_create(self, material, shader_node_group_name):
        node_group = material.node_tree.nodes.new("ShaderNodeGroup")
        node_group.node_tree = bpy.data.node_groups[shader_node_group_name]
        return node_group

    def node_placer(self, parent_node):
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
        return

    # endregion material_util func

    def build_principle_from_gltf_mat(self, b_mat, pymat):
        self.material_init(b_mat)
        principled_node = b_mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")

        b_mat.node_tree.links.new(
            b_mat.node_tree.nodes["Material Output"].inputs["Surface"],
            principled_node.outputs["BSDF"],
        )
        # self.connect_with_color_multiply_node(
        #     b_mat, pymat.base_color, pymat.color_texture_index, principled_node.inputs["Base Color"]
        # )
        self.connect_texture_node(
            b_mat,
            pymat.color_texture_index,
            principled_node.inputs["Base Color"],
            principled_node.inputs["Alpha"],
        )
        """
        self.connect_value_node(b_mat, pymat.metallic_factor,sg.inputs["metallic"])
        self.connect_value_node(b_mat, pymat.roughness_factor,sg.inputs["roughness"])
        self.connect_value_node(b_mat, pymat.metallic_factor,sg.inputs["metallic"])
        self.connect_value_node(b_mat, pymat.roughness_factor,sg.inputs["roughness"])
        """
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
        b_mat.use_backface_culling = pymat.double_sided

    def build_material_from_gltf(self, b_mat, pymat):
        self.material_init(b_mat)
        gltf_node_name = "GLTF"
        self.node_group_import(gltf_node_name)
        sg = self.node_group_create(b_mat, gltf_node_name)
        b_mat.node_tree.links.new(
            b_mat.node_tree.nodes["Material Output"].inputs["Surface"],
            sg.outputs["BSDF"],
        )

        self.connect_rgb_node(b_mat, pymat.base_color, sg.inputs["base_Color"])
        self.connect_texture_node(
            b_mat, pymat.color_texture_index, sg.inputs["color_texture"]
        )
        self.connect_value_node(b_mat, pymat.metallic_factor, sg.inputs["metallic"])
        self.connect_value_node(b_mat, pymat.roughness_factor, sg.inputs["roughness"])
        self.connect_texture_node(
            b_mat,
            pymat.metallic_roughness_texture_index,
            sg.inputs["metallic_roughness_texture"],
        )
        self.connect_rgb_node(
            b_mat, [*pymat.emissive_factor, 1], sg.inputs["emissive_color"]
        )
        self.connect_texture_node(
            b_mat, pymat.emissive_texture_index, sg.inputs["emissive_texture"]
        )
        self.connect_texture_node(
            b_mat, pymat.normal_texture_index, sg.inputs["normal"]
        )
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
        b_mat.use_backface_culling = pymat.double_sided

        return

    def build_material_from_mtoon(self, b_mat, pymat):
        self.material_init(b_mat)

        shader_node_group_name = "MToon_unversioned"
        sphere_add_vector_node_group_name = "matcap_vector"
        self.node_group_import(shader_node_group_name)
        self.node_group_import(sphere_add_vector_node_group_name)

        sg = self.node_group_create(b_mat, shader_node_group_name)
        b_mat.node_tree.links.new(
            b_mat.node_tree.nodes["Material Output"].inputs["Surface"],
            sg.outputs["Emission"],
        )

        float_prop_exchange_dic = vrm_types.MaterialMtoon.float_props_exchange_dic
        for k, v in pymat.float_props_dic.items():
            if k in [
                key for key, val in float_prop_exchange_dic.items() if val is not None
            ]:
                self.connect_value_node(b_mat, v, sg.inputs[float_prop_exchange_dic[k]])
                if k == "_CullMode":
                    if v == 2:  # 0: no cull 1:front cull 2:back cull
                        b_mat.use_backface_culling = True
                    elif v == 0:
                        b_mat.use_backface_culling = False
            else:
                b_mat[k] = v

        for k, v in pymat.keyword_dic.items():
            b_mat[k] = v

        uv_offset_tiling_value = [0, 0, 1, 1]
        vector_props_dic = vrm_types.MaterialMtoon.vector_props_exchange_dic
        for k, v in pymat.vector_props_dic.items():
            if k in ["_Color", "_ShadeColor", "_EmissionColor", "_OutlineColor"]:
                self.connect_rgb_node(b_mat, v, sg.inputs[vector_props_dic[k]])
            elif k == "_RimColor":
                self.connect_rgb_node(
                    b_mat, v, sg.inputs[vector_props_dic[k]], default_color=[0, 0, 0, 1]
                )
            elif k == "_MainTex" and v is not None:
                uv_offset_tiling_value = v
            else:
                b_mat[k] = v

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

        def connect_uv_map_to_texture(texture_node):
            b_mat.node_tree.links.new(
                texture_node.inputs[0], uv_offset_tiling_node.outputs[0]
            )

        tex_dic = vrm_types.MaterialMtoon.texture_kind_exchange_dic

        for tex_name, tex_index in pymat.texture_index_dic.items():
            if tex_index is None:
                continue
            if tex_name not in tex_dic.keys():
                if "unknown_texture" not in b_mat:
                    b_mat["unknown_texture"] = {}
                b_mat["unknown_texture"].update(
                    {tex_name: self.textures[tex_index].name}
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
                normalmap_node = self.connect_texture_node(
                    b_mat,
                    tex_index,
                    color_socket_to_connect=sg.inputs[tex_dic[tex_name]],
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

        transparent_exchange_dic = {
            0: "OPAQUE",
            1: "CUTOUT",
            2: "Z_TRANSPARENCY",
            3: "Z_TRANSPARENCY",
        }  # Trans_Zwrite(3)も2扱いで。
        transparent_mode = transparent_exchange_dic[pymat.float_props_dic["_BlendMode"]]
        self.set_material_transparent(b_mat, pymat, transparent_mode)

        return

    def build_material_from_transparent_z_write(self, b_mat, pymat):
        self.material_init(b_mat)

        z_write_transparent_sg = "TRANSPARENT_ZWRITE"
        self.node_group_import(z_write_transparent_sg)
        sg = self.node_group_create(b_mat, z_write_transparent_sg)
        b_mat.node_tree.links.new(
            b_mat.node_tree.nodes["Material Output"].inputs["Surface"],
            sg.outputs["Emission"],
        )

        for k, v in pymat.float_props_dic.items():
            b_mat[k] = v
        for k, v in pymat.vector_props_dic.items():
            b_mat[k] = v
        for tex_name, tex_index in pymat.texture_index_dic.items():
            if tex_name == "_MainTex":
                self.connect_texture_node(
                    b_mat, tex_index, sg.inputs["Main_Texture"], sg.inputs["Main_Alpha"]
                )
        self.set_material_transparent(b_mat, pymat, "Z_TRANSPARENCY")
        return

    # endregion material

    def make_primitive_mesh_objects(self, wm, progress):
        self.meshes = {}
        self.primitive_obj_dict = {
            pymesh[0].object_id: [] for pymesh in self.vrm_pydata.meshes
        }
        morph_cache_dict = {}  # key:tuple(POSITION,targets.POSITION),value:points_data
        # mesh_obj_build
        mesh_progress = 0
        mesh_progress_unit = 1 / max(1, len(self.vrm_pydata.meshes))
        for pymesh in self.vrm_pydata.meshes:
            b_mesh = bpy.data.meshes.new(pymesh[0].name)
            face_index = [tri for prim in pymesh for tri in prim.face_indices]
            pos = list(map(tuple, map(self.axis_glb_to_blender, pymesh[0].POSITION)))
            b_mesh.from_pydata(pos, [], face_index)
            b_mesh.update()
            obj = bpy.data.objects.new(pymesh[0].name, b_mesh)
            self.meshes[pymesh[0].object_id] = obj
            # region obj setting
            # origin 0:Vtype_Node 1:mesh 2:skin
            origin = None
            for key_is_node_id, node in self.vrm_pydata.origin_nodes_dict.items():
                if node[1] == pymesh[0].object_id:
                    # origin boneの場所に移動
                    obj.location = self.axis_glb_to_blender(node[0].position)
                    if len(node) == 3:
                        origin = node
                    else:  # len=2 ≒ skinがない場合
                        parent_node_id = None
                        for node_id, py_node in self.vrm_pydata.nodes_dict.items():
                            if py_node.children is None:
                                continue
                            if key_is_node_id in py_node.children:
                                parent_node_id = node_id
                        obj.parent = self.armature
                        obj.parent_type = "BONE"
                        obj.parent_bone = self.armature.data.bones[
                            self.vrm_pydata.nodes_dict[parent_node_id].name
                        ].name
                        # boneのtail側にparentされるので、根元からmesh nodeのpositionに動かしなおす
                        obj.matrix_world = Matrix.Translation(
                            [
                                self.armature.matrix_world.to_translation()[i]
                                + self.armature.data.bones[
                                    obj.parent_bone
                                ].matrix_local.to_translation()[i]
                                + self.axis_glb_to_blender(node[0].position)[i]
                                for i in range(3)
                            ]
                        )
            scene = self.context.scene
            scene.collection.objects.link(obj)
            # endregion obj setting

            # region  vertex groupの作成
            if origin is not None:
                # TODO bone名の不具合などでリネームが発生してるとうまくいかない
                nodes_index_list = self.vrm_pydata.skins_joints_list[origin[2]]
                # TODO bone名の不具合などでリネームが発生してるとうまくいかない
                # VertexGroupに頂点属性から一個ずつウェイトを入れる用の辞書作り
                for prim in pymesh:
                    if hasattr(prim, "JOINTS_0") and hasattr(prim, "WEIGHTS_0"):
                        # 使うkey(bone名)のvalueを空のリストで初期化(中身まで全部内包表記で?キモすぎるからしない。
                        vg_dict = {
                            self.vrm_pydata.nodes_dict[
                                nodes_index_list[joint_id]
                            ].name: list()
                            for joint_id in [
                                joint_id
                                for joint_ids in prim.JOINTS_0
                                for joint_id in joint_ids
                            ]
                        }
                        for v_index, (joint_ids, weights) in enumerate(
                            zip(prim.JOINTS_0, prim.WEIGHTS_0)
                        ):
                            # region VroidがJoints:[18,18,0,0]とかで格納してるからその処理を
                            normalized_joint_ids = list(dict.fromkeys(joint_ids))

                            # for deterministic export
                            def sort_by_vg_dict_key(joint_id):
                                name = self.vrm_pydata.nodes_dict[
                                    nodes_index_list[joint_id]
                                ].name
                                keys = list(vg_dict.keys())
                                if name in keys:
                                    return keys.index(name)
                                else:
                                    return len(keys) + joint_ids.index(joint_id)

                            normalized_joint_dic = {
                                jid: 0
                                for jid in sorted(
                                    normalized_joint_ids, key=sort_by_vg_dict_key
                                )
                            }
                            for i, k in enumerate(joint_ids):
                                normalized_joint_dic[k] += weights[i]
                            # endregion VroidがJoints:[18,18,0,0]とかで格納してるからその処理を
                            for joint_id, weight in normalized_joint_dic.items():
                                node_id = nodes_index_list[joint_id]
                                # TODO bone名の不具合などでリネームが発生してるとうまくいかない
                                vg_dict[
                                    self.vrm_pydata.nodes_dict[node_id].name
                                ].append([v_index, weight])
                        vg_list = []  # VertexGroupのリスト
                        for vg_key in vg_dict.keys():
                            if vg_key not in obj.vertex_groups:
                                vg_list.append(obj.vertex_groups.new(name=vg_key))
                        # 頂点リストに辞書から書き込む
                        for vg in vg_list:
                            weights = vg_dict[vg.name]
                            for w in weights:
                                if w[1] != 0.0:
                                    # 頂点はまとめてリストで追加できるようにしかなってない
                                    vg.add([w[0]], w[1], "REPLACE")
                obj.modifiers.new("amt", "ARMATURE").object = self.armature
            # endregion  vertex groupの作成

            # region uv
            flatten_vrm_mesh_vert_index = [
                ind for prim in pymesh for ind in prim.face_indices.flatten()
            ]

            for prim in pymesh:
                texcoord_num = 0
                uv_flag = True
                while uv_flag:
                    channel_name = "TEXCOORD_" + str(texcoord_num)
                    if hasattr(prim, channel_name):
                        if channel_name not in b_mesh.uv_layers:
                            b_mesh.uv_layers.new(name=channel_name)
                        blen_uv_data = b_mesh.uv_layers[channel_name].data
                        vrm_texcoord = getattr(prim, channel_name)
                        for node_id, v_index in enumerate(flatten_vrm_mesh_vert_index):
                            blen_uv_data[node_id].uv = vrm_texcoord[v_index]
                            # blender axisnaize(上下反転)
                            blen_uv_data[node_id].uv[1] = (
                                blen_uv_data[node_id].uv[1] * -1 + 1
                            )
                        texcoord_num += 1
                    else:
                        uv_flag = False
                        break
            # endregion uv

            # region Normal #TODO
            if self.import_normal:
                bpy.ops.object.mode_set(mode="OBJECT")
                bpy.ops.object.select_all(action="DESELECT")
                self.context.view_layer.objects.active = obj
                obj.select_set(True)
                bpy.ops.object.shade_smooth()  # this is need
                b_mesh.create_normals_split()
                # bpy.ops.mesh.customdata_custom_splitnormals_add()
                for prim in pymesh:
                    if hasattr(prim, "NORMAL"):
                        normalized_normal = prim.NORMAL
                        if not hasattr(prim, "vert_normal_normalized"):
                            normalized_normal = [
                                Vector(n)
                                if abs(Vector(n).magnitude - 1.0)
                                < sys.float_info.epsilon
                                else Vector(n).normalized()
                                for n in prim.NORMAL
                            ]
                            prim.vert_normal_normalized = True
                            prim.NORMAL = normalized_normal
                        b_mesh.normals_split_custom_set_from_vertices(
                            list(
                                map(
                                    tuple,
                                    map(self.axis_glb_to_blender, normalized_normal),
                                )
                            )
                        )
                b_mesh.use_auto_smooth = True
            # endregion Normal

            # region material適用
            face_length = 0
            for prim in pymesh:
                if (
                    self.material_dict[prim.material_index].name
                    not in obj.data.materials
                ):
                    obj.data.materials.append(self.material_dict[prim.material_index])
                mat_index = 0
                for i, mat in enumerate(obj.material_slots):
                    if (
                        mat.material.name
                        == self.material_dict[prim.material_index].name
                    ):
                        mat_index = i
                tris = len(prim.face_indices)
                for n in range(tris):
                    b_mesh.polygons[face_length + n].material_index = mat_index
                face_length = face_length + tris

            # endregion material適用

            # region vertex_color
            # なぜかこれだけ面基準で、loose verts and edgesに色は塗れない
            # また、2.79では頂点カラーにalpha(4要素目)がないから完全対応は無理だったが
            # 2.80では4要素になった模様
            # TODO: テスト (懸案:cleaningで頂点結合でデータ物故割れる説)

            for prim in pymesh:
                vcolor_count = 0
                vc_flag = True
                while vc_flag:
                    vc_color_name = f"COLOR_{vcolor_count}"
                    if hasattr(prim, vc_color_name):
                        vc = None
                        if vc_color_name in b_mesh.vertex_colors:
                            vc = b_mesh.vertex_colors[vc_color_name]
                        else:
                            vc = b_mesh.vertex_colors.new(name=vc_color_name)
                        for v_index, _ in enumerate(vc.data):
                            vc.data[v_index].color = getattr(prim, vc_color_name)[
                                flatten_vrm_mesh_vert_index[v_index]
                            ]
                        vcolor_count += 1
                    else:
                        vc_flag = False
                        break
            # endregion vertex_color

            # region shape_key
            # shapekey_data_factory with cache
            def absolutize_morph_positions(
                base_points, morph_target_pos_and_index, prim
            ):
                shape_key_positions = []
                morph_target_pos = morph_target_pos_and_index[0]
                morph_target_index = morph_target_pos_and_index[1]

                # すでに変換したことがあるならそれを使う
                if (
                    prim.POSITION_accessor,
                    morph_target_index,
                ) in morph_cache_dict.keys():
                    return morph_cache_dict[
                        (prim.POSITION_accessor, morph_target_index)
                    ]

                for base_pos, morph_pos in zip(base_points, morph_target_pos):
                    # numpy.array毎回作るのは見た目きれいだけど8倍くらい遅い
                    shape_key_positions.append(
                        self.axis_glb_to_blender(
                            [base_pos[i] + morph_pos[i] for i in range(3)]
                        )
                    )
                morph_cache_dict[
                    (prim.POSITION_accessor, morph_target_index)
                ] = shape_key_positions
                return shape_key_positions

            # shapeKeys
            for prim in pymesh:
                if hasattr(prim, "morph_target_point_list_and_accessor_index_dict"):
                    if b_mesh.shape_keys is None:
                        obj.shape_key_add(name="Basis")
                    for (
                        morph_name,
                        morph_pos_and_index,
                    ) in prim.morph_target_point_list_and_accessor_index_dict.items():
                        if morph_name not in b_mesh.shape_keys.key_blocks:
                            obj.shape_key_add(name=morph_name)
                        keyblock = b_mesh.shape_keys.key_blocks[morph_name]
                        shape_data = absolutize_morph_positions(
                            prim.POSITION, morph_pos_and_index, prim
                        )
                        for i, co in enumerate(shape_data):
                            keyblock.data[i].co = co
            # endregion shape_key

            # region vertices_merging
            if self.remove_doubles:
                bpy.ops.object.mode_set(mode="OBJECT")
                bpy.ops.object.select_all(action="DESELECT")
                self.context.view_layer.objects.active = obj
                obj.select_set(True)
                bpy.ops.object.mode_set(mode="EDIT")
                bpy.ops.mesh.remove_doubles(use_unselected=True)
            # endregion vertices_merging

            # progress update
            mesh_progress += mesh_progress_unit
            wm.progress_update(progress + mesh_progress)
        wm.progress_update(progress + 1)
        return

    def attach_vrm_attributes(self):
        vrm_extensions = json_get(
            self.vrm_pydata.json, ["extensions", vrm_types.VRM], {}
        )
        humanbones_relations = json_get(vrm_extensions, ["humanoid", "humanBones"], [])

        for humanbone in humanbones_relations:
            self.armature.data.bones[
                self.vrm_pydata.json["nodes"][humanbone["node"]]["name"]
            ]["humanBone"] = humanbone["bone"]
            self.armature.data[humanbone["bone"]] = self.armature.data.bones[
                self.vrm_pydata.json["nodes"][humanbone["node"]]["name"]
            ].name

        for metatag, metainfo in json_get(vrm_extensions, ["meta"], {}).items():
            if metatag == "texture":
                if (
                    "textures" in self.vrm_pydata.json
                    # extensions.VRM.meta.texture could be -1
                    # https://github.com/vrm-c/UniVRM/issues/91#issuecomment-454284964
                    and 0 <= metainfo < len(self.vrm_pydata.json["textures"])
                ):
                    texture_index = self.vrm_pydata.json["textures"][metainfo]["source"]
                    self.armature[metatag] = self.textures[texture_index].image.name
            else:
                self.armature[metatag] = metainfo

        return

    def json_dump(self):
        vrm_ext_dic = json_get(self.vrm_pydata.json, ["extensions", vrm_types.VRM])
        model_name = json_get(vrm_ext_dic, ["meta", "title"], "vrm_model")
        textblock = bpy.data.texts.new(name=f"{model_name}_raw.json")
        textblock.write(json.dumps(self.vrm_pydata.json, indent=4))

        def write_textblock_and_assign_to_armature(block_name, value):
            text_block = bpy.data.texts.new(name=f"{model_name}_{block_name}.json")
            text_block.write(json.dumps(value, indent=4))
            self.armature[f"{block_name}"] = text_block.name

        # region humanoid_parameter
        humanoid_params = copy.deepcopy(vrm_ext_dic["humanoid"])
        del humanoid_params["humanBones"]
        write_textblock_and_assign_to_armature("humanoid_params", humanoid_params)
        # endregion humanoid_parameter
        # region first_person
        firstperson_params = copy.deepcopy(vrm_ext_dic["firstPerson"])
        fp_bone = json_get(firstperson_params, ["firstPersonBone"], -1)
        if fp_bone != -1:
            firstperson_params["firstPersonBone"] = self.vrm_pydata.json["nodes"][
                firstperson_params["firstPersonBone"]
            ]["name"]
        if "meshAnnotations" in firstperson_params.keys():
            # TODO VRM1.0 is using node index that has mesh
            for mesh_annotation in firstperson_params["meshAnnotations"]:
                mesh_annotation["mesh"] = self.vrm_pydata.json["meshes"][
                    mesh_annotation["mesh"]
                ]["name"]

        write_textblock_and_assign_to_armature("firstPerson_params", firstperson_params)
        # endregion first_person

        # region blendshape_master
        blendshape_groups_list = copy.deepcopy(
            vrm_ext_dic["blendShapeMaster"]["blendShapeGroups"]
        )
        # meshをidから名前に
        # weightを0-100から0-1に
        # shape_indexを名前に
        # TODO VRM1.0 is using node index that has mesh
        # materialValuesはそのままで行けるハズ・・・
        for bsg in blendshape_groups_list:
            for bind_dic in bsg["binds"]:
                bind_dic["index"] = self.vrm_pydata.json["meshes"][bind_dic["mesh"]][
                    "primitives"
                ][0]["extras"]["targetNames"][bind_dic["index"]]
                bind_dic["mesh"] = self.meshes[bind_dic["mesh"]].name
                bind_dic["weight"] = bind_dic["weight"] / 100
        write_textblock_and_assign_to_armature(
            "blendshape_group", blendshape_groups_list
        )
        # endregion blendshape_master

        # region springbone
        spring_bonegroup_list = copy.deepcopy(
            vrm_ext_dic["secondaryAnimation"]["boneGroups"]
        )
        collider_groups_list = vrm_ext_dic["secondaryAnimation"]["colliderGroups"]
        # node_idを管理するのは面倒なので、名前に置き換える
        # collider_groupも同じく
        for bone_group in spring_bonegroup_list:
            bone_group["bones"] = [
                self.vrm_pydata.json["nodes"][node_id]["name"]
                for node_id in bone_group["bones"]
            ]
            bone_group["colliderGroups"] = [
                self.vrm_pydata.json["nodes"][
                    collider_groups_list[collider_gp_id]["node"]
                ]["name"]
                for collider_gp_id in bone_group["colliderGroups"]
            ]

        write_textblock_and_assign_to_armature("spring_bone", spring_bonegroup_list)
        # endregion springbone

        return

    def cleaning_data(self):
        # collection setting
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        for obj in self.meshes.values():
            self.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.shade_smooth()
            self.model_collection.objects.link(self.context.active_object)
            self.context.scene.collection.objects.unlink(self.context.active_object)
            bpy.ops.object.select_all(action="DESELECT")
        return

    def set_bone_roll(self):
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        self.armature.select_set(True)
        self.context.view_layer.objects.active = self.armature
        bpy.ops.object.mode_set(mode="EDIT")
        hb = vrm_types.HumanBones
        stop_bone_names = {*self.armature.data.values()[:]}

        def set_children_roll(bone_name, roll):
            if bone_name in self.armature.data and self.armature.data[bone_name] != "":
                bone = self.armature.data.edit_bones[self.armature.data[bone_name]]
                bone.roll = radians(roll)
                roll_list = [*bone.children]
                while roll_list:
                    bone = roll_list.pop()
                    if bone.name in stop_bone_names:
                        continue
                    bone.roll = radians(roll)
                    roll_list.extend(bone.children)
                return

        for b in hb.center_req + hb.center_def:
            if b == "hips":
                set_children_roll(b, 90)
            else:
                set_children_roll(b, -90)
        for deg, bs in zip(
            [0, 180],
            [hb.left_arm_req + hb.left_arm_def, hb.right_arm_req + hb.right_arm_def],
        ):
            for b in bs:
                set_children_roll(b, deg)
        for b in (
            hb.left_leg_req + hb.right_leg_req + hb.left_leg_def + hb.right_leg_def
        ):
            set_children_roll(b, 90)
        bpy.ops.object.mode_set(mode="OBJECT")
        return

    def put_spring_bone_info(self):

        if (
            "secondaryAnimation"
            not in self.vrm_pydata.json["extensions"][vrm_types.VRM]
        ):
            print("no secondary animation object")
            return
        secondary_animation_json = self.vrm_pydata.json["extensions"][vrm_types.VRM][
            "secondaryAnimation"
        ]
        spring_rootbone_groups_json = secondary_animation_json["boneGroups"]
        collider_groups_json = secondary_animation_json["colliderGroups"]
        nodes_json = self.vrm_pydata.json["nodes"]
        for bone_group in spring_rootbone_groups_json:
            for bone_id in bone_group["bones"]:
                bone = self.armature.data.bones[nodes_json[bone_id]["name"]]
                for key, val in bone_group.items():
                    if key == "bones":
                        continue
                    bone[key] = val

        model_name = self.vrm_pydata.json["extensions"][vrm_types.VRM]["meta"]["title"]
        coll = bpy.data.collections.new(f"{model_name}_colliders")
        self.model_collection.children.link(coll)
        for collider_group in collider_groups_json:
            collider_base_node = nodes_json[collider_group["node"]]
            node_name = collider_base_node["name"]
            for i, collider in enumerate(collider_group["colliders"]):
                collider_name = f"{node_name}_collider_{i}"
                obj = bpy.data.objects.new(name=collider_name, object_data=None)
                obj.parent = self.armature
                obj.parent_type = "BONE"
                obj.parent_bone = node_name
                offset = [
                    collider["offset"]["x"],
                    collider["offset"]["y"],
                    collider["offset"]["z"],
                ]  # values直接はindexアクセス出来ないのでしゃあなし
                offset = [
                    offset[axis] * inv for axis, inv in zip([0, 2, 1], [-1, -1, 1])
                ]  # TODO: Y軸反転はUniVRMのシリアライズに合わせてる

                obj.matrix_world = (
                    self.armature.matrix_world
                    @ Matrix.Translation(offset)
                    @ self.armature.data.bones[node_name].matrix_local
                )
                obj.empty_display_size = collider["radius"]
                obj.empty_display_type = "SPHERE"
                coll.objects.link(obj)

        return

    def blendfy(self):
        bpy.context.view_layer.objects.active = self.armature

        def make_pole_target(rl, upper_leg_name, lower_leg_name, foot_name):
            bpy.ops.object.mode_set(mode="EDIT")
            ebd = self.armature.data.edit_bones

            ik_foot = self.armature.data.edit_bones.new(f"IK_LEG_TARGET_{rl}")
            ik_foot.head = [f + o for f, o in zip(ebd[foot_name].head[:], [0, 0, 0])]
            ik_foot.tail = [f + o for f, o in zip(ebd[foot_name].head[:], [0, -0.2, 0])]

            pole = self.armature.data.edit_bones.new(f"leg_pole_{rl}")
            pole.parent = ik_foot
            pole.head = [
                f + o for f, o in zip(ebd[lower_leg_name].head[:], [0, -0.1, 0])
            ]
            pole.tail = [
                f + o for f, o in zip(ebd[lower_leg_name].head[:], [0, -0.2, 0])
            ]

            pole_name = copy.copy(pole.name)
            ik_foot_name = copy.copy(ik_foot.name)
            bpy.context.view_layer.depsgraph.update()
            bpy.context.scene.view_layers.update()
            bpy.ops.object.mode_set(mode="POSE")
            ikc = self.armature.pose.bones[lower_leg_name].constraints.new("IK")
            ikc.target = self.armature
            ikc.subtarget = self.armature.pose.bones[ik_foot_name].name

            def chain_solver(child, parent):
                current_bone = self.armature.pose.bones[child]
                for i in range(10):
                    if current_bone.name == parent:
                        return i + 1
                    current_bone = current_bone.parent
                return 11

            ikc.chain_count = chain_solver(lower_leg_name, upper_leg_name)

            ikc.pole_target = self.armature
            ikc.pole_subtarget = pole_name
            bpy.context.view_layer.depsgraph.update()
            bpy.context.scene.view_layers.update()
            return

        bpy.ops.object.mode_set(mode="EDIT")
        edit_bones = self.armature.data.edit_bones  # noqa: F841

        right_upper_leg_name = self.armature.data["rightUpperLeg"]
        right_lower_leg_name = self.armature.data["rightLowerLeg"]
        right_foot_name = self.armature.data["rightFoot"]

        left_upper_leg_name = self.armature.data["leftUpperLeg"]
        left_lower_leg_name = self.armature.data["leftLowerLeg"]
        left_foot_name = self.armature.data["leftFoot"]

        make_pole_target(
            "R", right_upper_leg_name, right_lower_leg_name, right_foot_name
        )
        make_pole_target("L", left_upper_leg_name, left_lower_leg_name, left_foot_name)

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.view_layer.depsgraph.update()
        bpy.context.scene.view_layers.update()
        vrm_helper.Bones_rename(bpy.context)
        return


# DeprecationWarning
class ICYP_OT_select_helper(bpy.types.Operator):  # noqa: N801
    bl_idname = "mesh.icyp_select_helper"
    bl_label = "VRM importer internal only func"
    bl_description = "VRM importer internal only"
    bl_options = {"REGISTER", "UNDO"}

    bpy.types.Scene.icyp_select_helper_select_list = list()

    def execute(self, context):
        bpy.ops.object.mode_set(mode="OBJECT")
        for vid in bpy.types.Scene.icyp_select_helper_select_list:
            bpy.context.active_object.data.vertices[vid].select = True
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.types.Scene.icyp_select_helper_select_list = list()
        return {"FINISHED"}
