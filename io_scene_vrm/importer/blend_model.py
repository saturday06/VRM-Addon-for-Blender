"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""


import base64
import copy
import itertools
import json
import math
import os.path
import secrets
import shutil
import string
import struct
import sys
import tempfile
from math import radians, sqrt
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

import bpy
import mathutils
import numpy
from mathutils import Matrix, Vector

from .. import vrm_types
from ..gl_constants import GlConstants
from ..misc import glb_factory, make_armature, vrm_helper
from ..vrm_types import nested_json_value_getter as json_get
from .vrm_load import parse_glb, remove_unsafe_path_chars


class BlendModel:
    def __init__(
        self,
        context: bpy.types.Context,
        vrm_pydata: vrm_types.VrmPydata,
        extract_textures_into_folder: bool,
        make_new_texture_folder: bool,
        legacy_importer: bool,
    ) -> None:
        self.meshes: Dict[int, bpy.types.Mesh] = {}
        self.extract_textures_into_folder = extract_textures_into_folder
        self.make_new_texture_folder = make_new_texture_folder
        self.legacy_importer = legacy_importer
        self.import_id = "BlenderVrmAddon" + (
            "".join(secrets.choice(string.digits) for _ in range(10))
        )
        self.temp_object_name_count = 0

        self.context = context
        self.vrm_pydata = vrm_pydata
        self.images: Dict[int, bpy.types.Image] = {}
        self.armature: Optional[bpy.types.Object] = None
        self.bones: Dict[int, bpy.types.Bone] = {}
        self.gltf_materials: Dict[int, bpy.types.Material] = {}
        self.vrm_materials: Dict[int, bpy.types.Material] = {}
        self.primitive_obj_dict: Optional[Dict[Optional[int], List[float]]] = None
        self.mesh_joined_objects = None
        self.vrm_model_build()

    def vrm_model_build(self) -> None:
        wm = bpy.context.window_manager

        def prog(z: int) -> int:
            wm.progress_update(z)
            return z + 1

        wm.progress_begin(0, 11)
        try:
            i = 1
            affected_object = self.scene_init()
            i = prog(i)
            if self.legacy_importer:
                self.texture_load()
                i = prog(i)
                self.make_armature()
            else:
                self.summon()
                if self.extract_textures_into_folder:
                    i = prog(i)
                    self.extract_textures()
            i = prog(i)
            self.use_fake_user_for_thumbnail()
            i = prog(i)
            self.connect_bones()
            i = prog(i)
            self.make_material()
            i = prog(i)
            if self.legacy_importer:
                self.make_primitive_mesh_objects(wm, i)
                # i=prog(i) ↑関数内でやる
            self.json_dump()
            i = prog(i)
            self.attach_vrm_attributes()
            i = prog(i)
            self.cleaning_data()
            i = prog(i)
            self.set_bone_roll()
            i = prog(i)
            self.put_spring_bone_info()
            i = prog(i)
            self.finishing(affected_object)
        finally:
            wm.progress_end()
            if (2, 90) <= bpy.app.version < (2, 91):
                # https://developer.blender.org/T79182
                bpy.context.window.cursor_modal_set("HAND")
                bpy.context.window.cursor_modal_restore()

    @staticmethod
    def axis_glb_to_blender(vec3: Sequence[float]) -> List[float]:
        return [vec3[i] * t for i, t in zip([0, 2, 1], [-1, 1, 1])]

    def summon(self) -> None:
        with open(self.vrm_pydata.filepath, "rb") as f:
            json_dict, body_binary = parse_glb(f.read())

        for key in ["nodes", "materials", "meshes"]:
            if key not in json_dict or not isinstance(json_dict[key], list):
                continue
            for index, value in enumerate(json_dict[key]):
                if not isinstance(value, dict):
                    continue
                if "extras" not in value:
                    value["extras"] = {}
                value["extras"].update({self.import_id + key.capitalize(): index})

        image_name_prefix = "{" + self.import_id + "-"
        if isinstance(json_dict.get("images"), list):
            for image_index, image in enumerate(json_dict["images"]):
                if not isinstance(image, dict):
                    continue
                if not isinstance(image.get("name"), str) or not image["name"]:
                    image["name"] = f"Image{image_index}"
                image["name"] = (
                    image_name_prefix + str(image_index) + "}" + image["name"]
                )

        if isinstance(json_dict.get("meshes"), list):
            for mesh in json_dict["meshes"]:
                if (
                    isinstance(mesh.get("extras"), dict)
                    and isinstance(mesh["extras"].get("targetNames"), list)
                ) or not isinstance(mesh["primitives"], list):
                    continue
                for primitive in mesh["primitives"]:
                    if (
                        not isinstance(primitive, dict)
                        or not isinstance(primitive.get("extras"), dict)
                        or not isinstance(primitive["extras"].get("targetNames"), list)
                    ):
                        continue
                    if mesh.get("extras") is None:
                        mesh["extras"] = {}
                    mesh["extras"]["targetNames"] = primitive["extras"]["targetNames"]
                    break

        if (
            isinstance(json_dict.get("textures"), list)
            and len(json_dict["textures"]) > 0
        ):
            primitives = []

            for texture_index, _ in enumerate(json_dict["textures"]):
                if not isinstance(json_dict.get("buffers"), list):
                    json_dict["buffers"] = []
                position_buffer_index = len(json_dict["buffers"])
                position_buffer_bytes = struct.pack(
                    "<9f", 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0
                )
                json_dict["buffers"].append(
                    {
                        "uri": "data:application/gltf-buffer;base64,"
                        + base64.b64encode(position_buffer_bytes).decode("ascii"),
                        "byteLength": len(position_buffer_bytes),
                    }
                )
                texcoord_buffer_index = len(json_dict["buffers"])
                texcoord_buffer_bytes = struct.pack("<6f", 0.0, 0.0, 1.0, 0.0, 0.0, 1.0)
                json_dict["buffers"].append(
                    {
                        "uri": "data:application/gltf-buffer;base64,"
                        + base64.b64encode(texcoord_buffer_bytes).decode("ascii"),
                        "byteLength": len(texcoord_buffer_bytes),
                    }
                )

                if not isinstance(json_dict.get("bufferViews"), list):
                    json_dict["bufferViews"] = []
                position_buffer_view_index = len(json_dict["bufferViews"])
                json_dict["bufferViews"].append(
                    {
                        "buffer": position_buffer_index,
                        "byteOffset": 0,
                        "byteLength": len(position_buffer_bytes),
                    }
                )
                texcoord_buffer_view_index = len(json_dict["bufferViews"])
                json_dict["bufferViews"].append(
                    {
                        "buffer": texcoord_buffer_index,
                        "byteOffset": 0,
                        "byteLength": 24,
                    }
                )

                if not isinstance(json_dict.get("accessors"), list):
                    json_dict["accessors"] = []
                position_accessors_index = len(json_dict["accessors"])
                json_dict["accessors"].append(
                    {
                        "bufferView": position_buffer_view_index,
                        "byteOffset": 0,
                        "type": "VEC3",
                        "componentType": GlConstants.FLOAT,
                        "count": 3,
                        "min": [0, 0, 0],
                        "max": [1, 1, 0],
                    }
                )
                texcoord_accessors_index = len(json_dict["accessors"])
                json_dict["accessors"].append(
                    {
                        "bufferView": texcoord_buffer_view_index,
                        "byteOffset": 0,
                        "type": "VEC2",
                        "componentType": GlConstants.FLOAT,
                        "count": 3,
                    }
                )

                if not isinstance(json_dict.get("materials"), list):
                    json_dict["materials"] = []
                tex_material_index = len(json_dict["materials"])
                json_dict["materials"].append(
                    {
                        "name": self.temp_object_name(),
                        "emissiveTexture": {"index": texture_index},
                    }
                )
                primitives.append(
                    {
                        "attributes": {
                            "POSITION": position_accessors_index,
                            "TEXCOORD_0": texcoord_accessors_index,
                        },
                        "material": tex_material_index,
                    }
                )

            if not isinstance(json_dict.get("meshes"), list):
                json_dict["meshes"] = []
            tex_mesh_index = len(json_dict["meshes"])
            json_dict["meshes"].append(
                {"name": self.temp_object_name(), "primitives": primitives}
            )

            if not isinstance(json_dict.get("nodes"), list):
                json_dict["nodes"] = []
            tex_node_index = len(json_dict["nodes"])
            json_dict["nodes"].append(
                {"name": self.temp_object_name(), "mesh": tex_mesh_index}
            )

            if not isinstance(json_dict.get("scenes"), list):
                json_dict["scenes"] = []
            json_dict["scenes"].append(
                {"name": self.temp_object_name(), "nodes": [tex_node_index]}
            )

        if isinstance(json_dict.get("scenes"), list) and isinstance(
            json_dict.get("nodes"), list
        ):
            nodes = json_dict["nodes"]
            skins = json_dict.get("skins", [])
            for scene in json_dict["scenes"]:
                if not isinstance(scene.get("nodes"), list):
                    continue

                all_node_indices = list(scene["nodes"])
                referenced_node_indices = list(scene["nodes"])
                search_node_indices = list(scene["nodes"])
                while search_node_indices:
                    search_node_index = search_node_indices.pop()
                    if not isinstance(search_node_index, int):
                        continue
                    all_node_indices.append(search_node_index)
                    if search_node_index < 0 or len(nodes) <= search_node_index:
                        continue
                    node = nodes[search_node_index]
                    if isinstance(node.get("mesh"), int):
                        referenced_node_indices.append(search_node_index)
                    if isinstance(node.get("skin"), int):
                        referenced_node_indices.append(search_node_index)
                        if node["skin"] < 0 or len(skins) <= node["skin"]:
                            continue
                        skin = skins[node["skin"]]
                        if isinstance(skin.get("skeleton"), int):
                            referenced_node_indices.append(skin["skeleton"])
                        if isinstance(skin.get("joints"), list):
                            referenced_node_indices.extend(skin["joints"])
                    if isinstance(node.get("children"), list):
                        search_node_indices.extend(node["children"])

                retain_node_indices = list(dict.fromkeys(all_node_indices))  # distinct
                for referenced_node_index in referenced_node_indices:
                    if referenced_node_index in retain_node_indices:
                        retain_node_indices.remove(referenced_node_index)

                if not retain_node_indices:
                    continue

                if not isinstance(json_dict.get("buffers"), list):
                    json_dict["buffers"] = []
                position_buffer_index = len(json_dict["buffers"])
                position_buffer_bytes = struct.pack(
                    "<9f", 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0
                )
                json_dict["buffers"].append(
                    {
                        "uri": "data:application/gltf-buffer;base64,"
                        + base64.b64encode(position_buffer_bytes).decode("ascii"),
                        "byteLength": len(position_buffer_bytes),
                    }
                )
                joints_buffer_index = len(json_dict["buffers"])
                joints_buffer_bytes = struct.pack(
                    "<12H", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
                )
                json_dict["buffers"].append(
                    {
                        "uri": "data:application/gltf-buffer;base64,"
                        + base64.b64encode(joints_buffer_bytes).decode("ascii"),
                        "byteLength": len(joints_buffer_bytes),
                    }
                )
                weights_buffer_index = len(json_dict["buffers"])
                weights_buffer_bytes = struct.pack(
                    "<12f", 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0
                )
                json_dict["buffers"].append(
                    {
                        "uri": "data:application/gltf-buffer;base64,"
                        + base64.b64encode(weights_buffer_bytes).decode("ascii"),
                        "byteLength": len(weights_buffer_bytes),
                    }
                )

                if not isinstance(json_dict.get("bufferViews"), list):
                    json_dict["bufferViews"] = []
                position_buffer_view_index = len(json_dict["bufferViews"])
                json_dict["bufferViews"].append(
                    {
                        "buffer": position_buffer_index,
                        "byteOffset": 0,
                        "byteLength": len(position_buffer_bytes),
                    }
                )
                joints_buffer_view_index = len(json_dict["bufferViews"])
                json_dict["bufferViews"].append(
                    {
                        "buffer": joints_buffer_index,
                        "byteOffset": 0,
                        "byteLength": len(joints_buffer_bytes),
                    }
                )
                weights_buffer_view_index = len(json_dict["bufferViews"])
                json_dict["bufferViews"].append(
                    {
                        "buffer": weights_buffer_index,
                        "byteOffset": 0,
                        "byteLength": len(weights_buffer_bytes),
                    }
                )

                if not isinstance(json_dict.get("accessors"), list):
                    json_dict["accessors"] = []
                position_accessors_index = len(json_dict["accessors"])
                json_dict["accessors"].append(
                    {
                        "bufferView": position_buffer_view_index,
                        "byteOffset": 0,
                        "type": "VEC3",
                        "componentType": GlConstants.FLOAT,
                        "count": 3,
                        "min": [0, 0, 0],
                        "max": [1, 1, 0],
                    }
                )
                joints_accessors_index = len(json_dict["accessors"])
                json_dict["accessors"].append(
                    {
                        "bufferView": joints_buffer_view_index,
                        "byteOffset": 0,
                        "type": "VEC4",
                        "componentType": GlConstants.UNSIGNED_SHORT,
                        "count": 3,
                    }
                )
                weights_accessors_index = len(json_dict["accessors"])
                json_dict["accessors"].append(
                    {
                        "bufferView": weights_buffer_view_index,
                        "byteOffset": 0,
                        "type": "VEC4",
                        "componentType": GlConstants.FLOAT,
                        "count": 3,
                    }
                )

                primitives = [
                    {
                        "attributes": {
                            "POSITION": position_accessors_index,
                            "JOINTS_0": joints_accessors_index,
                            "WEIGHTS_0": weights_accessors_index,
                        }
                    }
                ]

                if not isinstance(json_dict.get("meshes"), list):
                    json_dict["meshes"] = []
                skin_mesh_index = len(json_dict["meshes"])
                json_dict["meshes"].append(
                    {"name": self.temp_object_name(), "primitives": primitives}
                )

                if not isinstance(json_dict.get("skins"), list):
                    json_dict["skins"] = []
                skin_index = len(json_dict["skins"])
                json_dict["skins"].append({"joints": list(retain_node_indices)})

                if not isinstance(json_dict.get("nodes"), list):
                    json_dict["nodes"] = []
                skin_node_index = len(json_dict["nodes"])
                json_dict["nodes"].append(
                    {
                        "name": self.temp_object_name(),
                        "mesh": skin_mesh_index,
                        "skin": skin_index,
                    }
                )

                scene["nodes"].append(skin_node_index)

        with tempfile.NamedTemporaryFile(delete=False) as indexed_vrm_file:
            indexed_vrm_file.write(glb_factory.pack_glb(json_dict, body_binary))
            indexed_vrm_file.flush()

            if bpy.app.version < (2, 83):
                bpy.ops.import_scene.gltf(
                    filepath=indexed_vrm_file.name,
                    import_pack_images=True,
                )
            else:
                bpy.ops.import_scene.gltf(
                    filepath=indexed_vrm_file.name,
                    import_pack_images=True,
                    bone_heuristic="FORTUNE",
                )

        human_bones = json_get(
            json_dict, ["extensions", "VRM", "humanoid", "humanBones"], []
        )

        hips_bone_node_index: Optional[int] = None
        if isinstance(human_bones, list):
            for human_bone in human_bones:
                if (
                    isinstance(human_bone, dict)
                    and human_bone.get("bone") == "hips"
                    and isinstance(human_bone.get("node"), int)
                ):
                    hips_bone_node_index = human_bone["node"]
                    break

        extras_node_index_key = self.import_id + "Nodes"
        if hips_bone_node_index is not None:
            for obj in bpy.context.selectable_objects:
                data = obj.data
                if not isinstance(data, bpy.types.Armature):
                    continue
                for bone in data.bones:
                    bone_node_index = bone.get(extras_node_index_key)
                    if not isinstance(bone_node_index, int):
                        continue
                    if 0 <= bone_node_index < len(self.vrm_pydata.json["nodes"]):
                        node = self.vrm_pydata.json["nodes"][bone_node_index]
                        node["name"] = bone.name
                    del bone[extras_node_index_key]
                    self.bones[bone_node_index] = bone
                    if (
                        self.armature is not None
                        or bone_node_index != hips_bone_node_index
                    ):
                        continue
                    # VRM 0.0 only
                    if obj.rotation_mode == "QUATERNION":
                        obj.rotation_quaternion.rotate(
                            mathutils.Euler((0.0, 0.0, math.pi), "XYZ")
                        )
                        obj.select_set(True)
                        previous_active = bpy.context.view_layer.objects.active
                        try:
                            bpy.context.view_layer.objects.active = obj
                            bpy.ops.object.transform_apply(rotation=True)
                        finally:
                            bpy.context.view_layer.objects.active = previous_active
                    self.armature = obj

        extras_mesh_index_key = self.import_id + "Meshes"
        for obj in bpy.context.selectable_objects:
            data = obj.data
            if not isinstance(data, bpy.types.Mesh):
                continue
            mesh_index = obj.data.get(extras_mesh_index_key)
            if not isinstance(mesh_index, int):
                continue
            del obj.data[extras_mesh_index_key]
            self.meshes[mesh_index] = obj

        extras_material_index_key = self.import_id + "Materials"
        for material in bpy.data.materials:
            material_index = material.get(extras_material_index_key)
            if not isinstance(material_index, int):
                continue
            del material[extras_material_index_key]
            self.gltf_materials[material_index] = material

        for image in bpy.data.images:
            if not image.name.startswith(image_name_prefix):
                continue
            image_index = int(
                "".join(image.name.split(image_name_prefix)[1:]).split("}")[0]
            )
            image.name = "".join(image.name.split("}")[1:])
            self.images[image_index] = image

        if bpy.context.object is not None and bpy.context.object.mode == "EDIT":
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        for obj in bpy.data.objects:
            if self.is_temp_object_name(obj.name):
                obj.select_set(True)
                bpy.ops.object.delete()

        for material in bpy.data.materials:
            if self.is_temp_object_name(material.name) and material.users == 0:
                print(material.name)
                bpy.data.materials.remove(material)

        armature = self.armature
        if armature is None:
            raise Exception("Failed to read VRM Humanoid")

    def temp_object_name(self) -> str:
        self.temp_object_name_count += 1
        return f"{self.import_id}Temp_{self.temp_object_name_count}_"

    def is_temp_object_name(self, name: str) -> bool:
        return name.startswith(f"{self.import_id}Temp_")

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
            if str(
                json_get(
                    self.vrm_pydata.json, ["extensions", "VRM", "exporterVersion"], ""
                )
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

            make_armature.connect_parent_tail_and_child_head_if_same_position(
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

    def texture_load(self) -> None:
        for (image_index, image_props) in enumerate(self.vrm_pydata.image_properties):
            img = bpy.data.images.load(image_props.filepath)
            if not self.extract_textures_into_folder:
                # https://github.com/KhronosGroup/glTF-Blender-IO/blob/blender-v2.82-release/addons/io_scene_gltf2/blender/imp/gltf2_blender_image.py#L100
                img.pack()
            self.images[image_index] = img

    def use_fake_user_for_thumbnail(self) -> None:
        # サムネイルはVRMの仕様ではimageのインデックスとあるが、UniVRMの実装ではtextureのインデックスになっている
        # https://github.com/vrm-c/UniVRM/blob/v0.67.0/Assets/VRM/Runtime/IO/VRMImporterContext.cs#L308
        json_texture_index = json_get(
            self.vrm_pydata.json, ["extensions", "VRM", "meta", "texture"], -1
        )
        if not isinstance(json_texture_index, int):
            raise Exception('json["extensions"]["VRM"]["meta"]["texture"] is not int')
        json_textures = self.vrm_pydata.json.get("textures", [])
        if not isinstance(json_textures, list):
            raise Exception('json["textures"] is not list')
        if json_texture_index not in (-1, None) and (
            "textures" in self.vrm_pydata.json
            and len(json_textures) > json_texture_index
        ):
            image_index = json_textures[json_texture_index].get("source")
            if image_index in self.images:
                self.images[image_index].use_fake_user = True

    def make_armature(self) -> None:
        # build bones as armature
        armature_data = bpy.data.armatures.new("Armature")
        self.armature = bpy.data.objects.new(armature_data.name, armature_data)
        self.context.scene.collection.objects.link(self.armature)
        bpy.context.view_layer.objects.active = self.armature
        bpy.ops.object.mode_set(mode="EDIT")
        self.bones = {}
        armature_edit_bones: Dict[int, bpy.types.Bone] = {}

        # region bone recursive func
        def bone_chain(node_id: int, parent_node_id: int) -> None:
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

            # region temporary tail pos(glTF doesn't have bone. there defines as joints )
            def vector_length(bone_vector: List[float]) -> float:
                return sqrt(
                    pow(bone_vector[0], 2)
                    + pow(bone_vector[1], 2)
                    + pow(bone_vector[2], 2)
                )

            # glTFは関節で定義されていて骨の長さとか向きとかないからまあなんかそれっぽい方向にボーンを向けて伸ばしたり縮めたり
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
                for child_id in py_bone.children:
                    mean_relate_pos += self.axis_glb_to_blender(
                        self.vrm_pydata.nodes_dict[child_id].position
                    )
                children_len = len(py_bone.children)
                if children_len > 0:
                    mean_relate_pos = mean_relate_pos / children_len
                    if (
                        vector_length(mean_relate_pos) <= 0.001
                    ):  # ボーンの長さが1mm以下なら上に10cm延ばす
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
        def find_connected_node_ids(parent_node_ids: Sequence[int]) -> Set[int]:
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
        while bone_nodes:
            bone_chain(*bone_nodes.pop())
        # call when bone built
        self.context.scene.view_layers.update()
        bpy.ops.object.mode_set(mode="OBJECT")

    def extract_textures(self) -> None:
        dir_path = os.path.abspath(self.vrm_pydata.filepath) + ".textures"
        if self.make_new_texture_folder:
            for i in range(100001):
                checking_dir_path = dir_path if i == 0 else f"{dir_path}.{i}"
                if not os.path.exists(checking_dir_path):
                    os.mkdir(checking_dir_path)
                    dir_path = checking_dir_path
                    break

        for image_index, image in self.images.items():
            image_name = image.name
            image_type = image.file_format.lower()
            if image_name == "":
                image_name = "texture_" + str(image_index)
                print(f"no name image is named {image_name}")
            elif len(image_name) >= 50:
                new_image_name = "texture_too_long_name_" + str(image_index)
                print(f"too long name image: {image_name} is named {new_image_name}")
                image_name = new_image_name

            image_name = remove_unsafe_path_chars(image_name)
            image_path = os.path.join(dir_path, image_name)
            if not image_name.lower().endswith("." + image_type.lower()):
                image_path += "." + image_type
            if not os.path.exists(image_path):
                image.unpack(method="WRITE_ORIGINAL")
                shutil.copyfile(image.filepath_from_user(), image_path)
                image.filepath = image_path
                image.reload()
            else:
                written_flag = False
                for i in range(100000):
                    root, ext = os.path.splitext(image_name)
                    second_image_name = root + "_" + str(i) + ext
                    image_path = os.path.join(dir_path, second_image_name)
                    if not os.path.exists(image_path):
                        image.unpack(method="WRITE_ORIGINAL")
                        shutil.copyfile(image.filepath_from_user, image_path)
                        image.filepath = image_path
                        image.reload()
                        written_flag = True
                        break
                if not written_flag:
                    print(
                        "There are more than 100000 images with the same name in the folder."
                        + f" Failed to write file: {image_name}"
                    )

    # region material
    def make_material(self) -> None:
        # 適当なので要調整
        for index, mat in enumerate(self.vrm_pydata.materials):
            b_mat = bpy.data.materials.new(mat.name)
            b_mat["shader_name"] = mat.shader_name
            if isinstance(mat, vrm_types.MaterialGltf):
                self.build_material_from_gltf(b_mat, mat)
            elif isinstance(mat, vrm_types.MaterialMtoon):
                self.build_material_from_mtoon(b_mat, mat)
            elif isinstance(mat, vrm_types.MaterialTransparentZWrite):
                self.build_material_from_transparent_z_write(b_mat, mat)
            else:
                print(f"unknown material {mat.name}")
            self.node_placer(b_mat.node_tree.nodes["Material Output"])
            self.vrm_materials[index] = b_mat

        for mesh in self.meshes.values():
            for material_index, material in enumerate(mesh.data.materials):
                for vrm_material_index, vrm_material in self.vrm_materials.items():
                    if material != self.gltf_materials[vrm_material_index]:
                        continue
                    material_name = material.name
                    material.name = "glTF_VRM_overridden_" + material_name
                    vrm_material.name = material_name
                    mesh.data.materials[material_index] = vrm_material
                    break

    # region material_util func
    def set_material_transparent(
        self,
        b_mat: bpy.types.Material,
        pymat: vrm_types.Material,
        transparent_mode: str,
    ) -> None:
        if transparent_mode == "OPAQUE":
            pass
        elif transparent_mode == "CUTOUT":
            b_mat.blend_method = "CLIP"
            if isinstance(pymat, vrm_types.MaterialMtoon):  # TODO: TransparentZWrite?
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
        tex = self.vrm_pydata.json["textures"][tex_index]
        image_index = tex["source"]
        sampler = (
            self.vrm_pydata.json["samplers"][tex["sampler"]]
            if "samplers" in self.vrm_pydata.json
            else [{"wrapS": GlConstants.REPEAT, "magFilter": GlConstants.LINEAR}]
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
        filter_type = (
            sampler["magFilter"] if "magFilter" in sampler else GlConstants.LINEAR
        )
        if filter_type == GlConstants.NEAREST:
            image_node.interpolation = "Closest"
        else:
            image_node.interpolation = "Linear"
        # blender is ('REPEAT', 'EXTEND', 'CLIP') glTF is CLAMP_TO_EDGE,MIRRORED_REPEAT,REPEAT
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
        self, b_mat: bpy.types.Material, pymat: vrm_types.MaterialGltf
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
        self, b_mat: bpy.types.Material, pymat: vrm_types.MaterialGltf
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
        self, b_mat: bpy.types.Material, pymat: vrm_types.MaterialMtoon
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

        float_prop_exchange_dic = vrm_types.MaterialMtoon.float_props_exchange_dic
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
        vector_props_dic = vrm_types.MaterialMtoon.vector_props_exchange_dic
        for k, vec in pymat.vector_props_dic.items():
            if k in ["_Color", "_ShadeColor", "_EmissionColor", "_OutlineColor"]:
                self.connect_rgb_node(b_mat, vec, sg.inputs[vector_props_dic[k]])
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

        tex_dic = vrm_types.MaterialMtoon.texture_kind_exchange_dic

        for tex_name, tex_index in pymat.texture_index_dic.items():
            if tex_index is None:
                continue
            image_index = self.vrm_pydata.json["textures"][tex_index]["source"]
            if image_index not in self.images:
                continue
            if tex_name not in tex_dic.keys():
                if "unknown_texture" not in b_mat:
                    b_mat["unknown_texture"] = {}
                b_mat["unknown_texture"].update(
                    {tex_name: self.vrm_pydata.json["textures"][tex_index]["name"]}
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
        elif math.fabs(transparent_mode_float - 2) < 0.001:
            transparent_mode = "Z_TRANSPARENCY"
        elif math.fabs(transparent_mode_float - 3) < 0.001:
            transparent_mode = "Z_TRANSPARENCY"
            # Trans_Zwrite(3)も2扱いで。
        self.set_material_transparent(b_mat, pymat, transparent_mode)

    def build_material_from_transparent_z_write(
        self, b_mat: bpy.types.Material, pymat: vrm_types.MaterialTransparentZWrite
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

    def make_primitive_mesh_objects(
        self, wm: bpy.types.WindowManager, progress: int
    ) -> None:
        armature = self.armature
        if armature is None:
            raise Exception("armature is None")
        self.primitive_obj_dict = {
            pymesh[0].object_id: [] for pymesh in self.vrm_pydata.meshes
        }
        morph_cache_dict: Dict[
            Tuple[int, int], List[List[float]]
        ] = {}  # key:tuple(POSITION,targets.POSITION),value:points_data
        # mesh_obj_build
        mesh_progress = 0.0
        mesh_progress_unit = 1 / max(1, len(self.vrm_pydata.meshes))
        for pymesh in self.vrm_pydata.meshes:
            b_mesh = bpy.data.meshes.new(pymesh[0].name)
            face_index = [tri for prim in pymesh for tri in prim.face_indices]
            if pymesh[0].POSITION is None:
                continue
            pos = list(map(self.axis_glb_to_blender, pymesh[0].POSITION))
            b_mesh.from_pydata(pos, [], face_index)
            b_mesh.update()
            obj = bpy.data.objects.new(pymesh[0].name, b_mesh)
            obj.parent = self.armature
            self.meshes[pymesh[0].object_id] = obj
            # region obj setting
            # origin 0:Vtype_Node 1:mesh 2:skin
            origin = None
            for key_is_node_id, node in self.vrm_pydata.origin_nodes_dict.items():
                if node[1] != pymesh[0].object_id:
                    continue
                # origin boneの場所に移動
                obj.location = self.axis_glb_to_blender(node[0].position)
                if len(node) == 3:
                    origin = node
                    continue
                # len=2 ≒ skinがない場合
                parent_node_id = None
                for node_id, py_node in self.vrm_pydata.nodes_dict.items():
                    if py_node.children is None:
                        continue
                    if key_is_node_id in py_node.children:
                        parent_node_id = node_id
                obj.parent_type = "BONE"
                if parent_node_id is not None:
                    obj.parent_bone = armature.data.bones[
                        self.vrm_pydata.nodes_dict[parent_node_id].name
                    ].name
                # boneのtail側にparentされるので、根元からmesh nodeのpositionに動かしなおす
                obj.matrix_world = Matrix.Translation(
                    [
                        armature.matrix_world.to_translation()[i]
                        + armature.data.bones[
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
                    if prim.JOINTS_0 is not None and prim.WEIGHTS_0 is not None:
                        # 使うkey(bone名)のvalueを空のリストで初期化(中身まで全部内包表記で?キモすぎるからしない。
                        vg_dict: Dict[str, List[Tuple[int, float]]] = {
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
                            def sort_by_vg_dict_key(
                                sort_data: Tuple[
                                    int,
                                    List[int],
                                    List[int],
                                    Dict[str, List[Tuple[int, float]]],
                                ]
                            ) -> int:
                                (
                                    sort_joint_id,
                                    sort_joint_ids,
                                    sort_nodes_index_list,
                                    sort_vg_dict,
                                ) = sort_data
                                name = self.vrm_pydata.nodes_dict[
                                    sort_nodes_index_list[sort_joint_id]
                                ].name
                                keys = list(sort_vg_dict.keys())
                                if name in keys:
                                    return keys.index(name)
                                return len(keys) + sort_joint_ids.index(sort_joint_id)

                            get_first_element: Callable[
                                [Tuple[int, Any, Any, Any]], int
                            ] = lambda input: input[0]
                            sorted_joint_ids = map(
                                get_first_element,
                                sorted(
                                    zip(
                                        normalized_joint_ids,
                                        itertools.repeat(joint_ids),
                                        itertools.repeat(nodes_index_list),
                                        itertools.repeat(vg_dict),
                                    ),
                                    key=sort_by_vg_dict_key,
                                ),
                            )

                            normalized_joint_dic: Dict[int, float] = {
                                joint_id: 0 for joint_id in sorted_joint_ids
                            }

                            for i, k in enumerate(joint_ids):
                                normalized_joint_dic[k] += weights[i]
                            # endregion VroidがJoints:[18,18,0,0]とかで格納してるからその処理を
                            for joint_id, weight in normalized_joint_dic.items():
                                node_id = nodes_index_list[joint_id]
                                # TODO bone名の不具合などでリネームが発生してるとうまくいかない
                                vg_dict[
                                    self.vrm_pydata.nodes_dict[node_id].name
                                ].append((v_index, weight))
                        vg_list = []  # VertexGroupのリスト
                        for vg_key in vg_dict.keys():
                            if vg_key not in obj.vertex_groups:
                                vg_list.append(obj.vertex_groups.new(name=vg_key))
                        # 頂点リストに辞書から書き込む
                        for vg in vg_list:
                            joint_id_and_weights = vg_dict[vg.name]
                            for (joint_id, weight) in joint_id_and_weights:
                                if weight != 0.0:
                                    # 頂点はまとめてリストで追加できるようにしかなってない
                                    vg.add([joint_id], weight, "REPLACE")
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
                        blender_uv_data = b_mesh.uv_layers[channel_name].data
                        vrm_texcoord = getattr(prim, channel_name)
                        for node_id, v_index in enumerate(flatten_vrm_mesh_vert_index):
                            blender_uv_data[node_id].uv = vrm_texcoord[v_index]
                            # to blender axis (上下反転)
                            blender_uv_data[node_id].uv[1] = (
                                blender_uv_data[node_id].uv[1] * -1 + 1
                            )
                        texcoord_num += 1
                    else:
                        uv_flag = False
                        break
            # endregion uv

            # region Normal #TODO
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")
            self.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.shade_smooth()  # this is need
            b_mesh.create_normals_split()
            # bpy.ops.mesh.customdata_custom_splitnormals_add()
            for prim in pymesh:
                if prim.NORMAL is None:
                    continue
                normalized_normal = prim.NORMAL
                if (
                    prim.vert_normal_normalized is None
                    or not prim.vert_normal_normalized
                ):
                    normalized_normal = [
                        Vector(n)
                        if abs(Vector(n).magnitude - 1.0) < sys.float_info.epsilon
                        else Vector(n).normalized()
                        for n in prim.NORMAL
                    ]
                    prim.vert_normal_normalized = True
                    prim.NORMAL = normalized_normal
                b_mesh.normals_split_custom_set_from_vertices(
                    list(map(self.axis_glb_to_blender, normalized_normal))
                )
            b_mesh.use_auto_smooth = True
            # endregion Normal

            # region material適用
            face_length = 0
            for prim in pymesh:
                if prim.material_index is None:
                    continue
                if (
                    self.vrm_materials[prim.material_index].name
                    not in obj.data.materials
                ):
                    obj.data.materials.append(self.vrm_materials[prim.material_index])
                mat_index = 0
                for i, mat in enumerate(obj.material_slots):
                    if (
                        mat.material.name
                        == self.vrm_materials[prim.material_index].name
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
                base_points: List[List[float]],
                morph_target_pos_and_index: List[Any],
                prim: vrm_types.Mesh,
            ) -> List[List[float]]:
                shape_key_positions = []
                morph_target_pos = morph_target_pos_and_index[0]
                morph_target_index = morph_target_pos_and_index[1]

                if prim.POSITION_accessor is None:
                    return []

                # すでに変換したことがあるならそれを使う
                if (
                    prim.POSITION_accessor,
                    morph_target_index,
                ) in morph_cache_dict:
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
                if (
                    prim.morph_target_point_list_and_accessor_index_dict is None
                    or b_mesh is None
                ):
                    continue
                if b_mesh.shape_keys is None:
                    obj.shape_key_add(name="Basis")
                for (
                    morph_name,
                    morph_pos_and_index,
                ) in prim.morph_target_point_list_and_accessor_index_dict.items():
                    if (
                        b_mesh.shape_keys is None
                        or morph_name not in b_mesh.shape_keys.key_blocks
                    ):
                        obj.shape_key_add(name=morph_name)
                    if b_mesh.shape_keys is None:
                        continue
                    keyblock = b_mesh.shape_keys.key_blocks[morph_name]
                    if prim.POSITION is not None:
                        shape_data = absolutize_morph_positions(
                            prim.POSITION, morph_pos_and_index, prim
                        )
                    else:
                        shape_data = []
                    for i, co in enumerate(shape_data):
                        keyblock.data[i].co = co
            # endregion shape_key

            # progress update
            mesh_progress += mesh_progress_unit
            wm.progress_update(progress + mesh_progress)
        wm.progress_update(progress + 1)

    def attach_vrm_attributes(self) -> None:
        armature = self.armature
        if armature is None:
            raise Exception("armature is None")
        vrm_extensions = json_get(self.vrm_pydata.json, ["extensions", "VRM"], {})
        if not isinstance(vrm_extensions, dict):
            raise Exception("json extensions.VRM is not dict")
        humanbones_relations = json_get(vrm_extensions, ["humanoid", "humanBones"], [])
        if not isinstance(humanbones_relations, list):
            raise Exception("extensions.VRM.humanoid.humanBones is not list")
        for (i, humanbone) in enumerate(humanbones_relations):
            if not isinstance(humanbone, dict):
                raise Exception(f"extensions.VRM.humanoid.humanBones[{i}] is not dict")
            node_index = humanbone["node"]
            if not isinstance(node_index, int):
                raise Exception(
                    f'json extensions.VRM.humanoid.humanBones[{i}]["node"] is not int but {node_index}'
                )
            armature.data.bones[self.vrm_pydata.json["nodes"][node_index]["name"]][
                "humanBone"
            ] = node_index
            armature.data[humanbone["bone"]] = armature.data.bones[
                self.vrm_pydata.json["nodes"][node_index]["name"]
            ].name

        vrm_meta = json_get(vrm_extensions, ["meta"], {})
        if not isinstance(vrm_meta, dict):
            raise Exception("json extensions.VRM.meta is not dict")
        for metatag, metainfo in vrm_meta.items():
            if metatag == "texture":
                if (
                    "textures" in self.vrm_pydata.json
                    # extensions.VRM.meta.texture could be -1
                    # https://github.com/vrm-c/UniVRM/issues/91#issuecomment-454284964
                    and 0 <= metainfo < len(self.vrm_pydata.json["textures"])
                ):
                    image_index = self.vrm_pydata.json["textures"][metainfo]["source"]
                    if image_index in self.images:
                        armature[metatag] = self.images[image_index].name
            else:
                armature[metatag] = metainfo

    def json_dump(self) -> None:
        vrm_ext_dic = json_get(self.vrm_pydata.json, ["extensions", "VRM"])
        if not isinstance(vrm_ext_dic, dict):
            raise Exception("json extensions VRM is not dict")
        textblock = bpy.data.texts.new(name="raw.json")
        textblock.write(json.dumps(self.vrm_pydata.json, indent=4))

        def write_textblock_and_assign_to_armature(block_name: str, value: str) -> None:
            text_block = bpy.data.texts.new(name=f"{block_name}.json")
            text_block.write(json.dumps(value, indent=4))
            armature = self.armature
            if armature is None:
                raise Exception("armature is None")
            armature[f"{block_name}"] = text_block.name

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
        if "meshAnnotations" in firstperson_params:
            # TODO VRM1.0 is using node index that has mesh
            for mesh_annotation in firstperson_params["meshAnnotations"]:
                mesh_annotation["mesh"] = self.vrm_pydata.json["meshes"][
                    mesh_annotation["mesh"]
                ]["name"]

        write_textblock_and_assign_to_armature("firstPerson_params", firstperson_params)
        # endregion first_person

        # region blendshape_master
        blendshape_groups = copy.deepcopy(
            vrm_ext_dic["blendShapeMaster"]["blendShapeGroups"]
        )
        # meshをidから名前に
        # weightを0-100から0-1に
        # shape_indexを名前に
        # TODO VRM1.0 is using node index that has mesh
        # materialValuesはそのままで行けるハズ・・・
        legacy_vrm0 = False
        for blendshape_group in blendshape_groups:
            for bind_dic in blendshape_group["binds"]:
                try:
                    bind_dic["index"] = self.vrm_pydata.json["meshes"][
                        bind_dic["mesh"]
                    ]["primitives"][0]["extras"]["targetNames"][bind_dic["index"]]
                except KeyError:
                    legacy_vrm0 = True
                    break
                bind_dic["mesh"] = self.meshes[bind_dic["mesh"]].name
                bind_dic["weight"] = bind_dic["weight"] / 100
            if legacy_vrm0:
                break
        if legacy_vrm0:
            blendshape_groups = []
        write_textblock_and_assign_to_armature("blendshape_group", blendshape_groups)
        # endregion blendshape_master

        # region springbone
        spring_bonegroup_list = copy.deepcopy(
            vrm_ext_dic["secondaryAnimation"]["boneGroups"]
        )
        collider_groups_list = vrm_ext_dic["secondaryAnimation"]["colliderGroups"]
        # node_idを管理するのは面倒なので、名前に置き換える
        # collider_groupも同じく
        for bone_group in spring_bonegroup_list:
            center_node_id = bone_group.get("center")
            if isinstance(center_node_id, int) and 0 <= center_node_id < len(
                self.vrm_pydata.json["nodes"]
            ):
                bone_group["center"] = self.vrm_pydata.json["nodes"][center_node_id][
                    "name"
                ]
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

    def cleaning_data(self) -> None:
        # collection setting
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        for obj in self.meshes.values():
            self.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.shade_smooth()
            bpy.ops.object.select_all(action="DESELECT")

    def set_bone_roll(self) -> None:
        armature = self.armature
        if armature is None:
            raise Exception("armature is None")

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        armature.select_set(True)
        self.context.view_layer.objects.active = self.armature
        bpy.ops.object.mode_set(mode="EDIT")
        hb = vrm_types.HumanBones
        stop_bone_names = {*armature.data.values()[:]}

        def set_children_roll(bone_name: str, roll: float) -> None:
            armature = self.armature
            if armature is None:
                raise Exception("armature is None")

            if bone_name in armature.data and armature.data[bone_name] != "":
                bone = armature.data.edit_bones[armature.data[bone_name]]
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

    def put_spring_bone_info(self) -> None:
        armature = self.armature
        if armature is None:
            raise Exception("armature is None")

        if "secondaryAnimation" not in self.vrm_pydata.json["extensions"]["VRM"]:
            print("no secondary animation object")
            return
        secondary_animation_json = self.vrm_pydata.json["extensions"]["VRM"][
            "secondaryAnimation"
        ]
        spring_rootbone_groups_json = secondary_animation_json["boneGroups"]
        collider_groups_json = secondary_animation_json["colliderGroups"]
        nodes_json = self.vrm_pydata.json["nodes"]
        for bone_group in spring_rootbone_groups_json:
            for bone_id in bone_group["bones"]:
                bone = armature.data.bones[nodes_json[bone_id]["name"]]
                for key, val in bone_group.items():
                    if key == "bones":
                        continue
                    bone[key] = val

        coll = bpy.data.collections.new("Colliders")
        self.context.scene.collection.children.link(coll)
        bpy.context.view_layer.depsgraph.update()
        bpy.context.scene.view_layers.update()
        for collider_group in collider_groups_json:
            collider_base_node = self.vrm_pydata.json["nodes"][collider_group["node"]]
            node_name = collider_base_node["name"]
            for i, collider in enumerate(collider_group["colliders"]):
                if node_name not in armature.data.bones:
                    continue
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

                # boneのtail側にparentされるので、根元からのpositionに動かしなおす
                obj.matrix_world = Matrix.Translation(
                    [
                        armature.matrix_world.to_translation()[i]
                        + armature.data.bones[node_name].matrix_local.to_translation()[
                            i
                        ]
                        + offset[i]
                        for i in range(3)
                    ]
                )

                obj.empty_display_size = collider["radius"]
                obj.empty_display_type = "SPHERE"
                coll.objects.link(obj)

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
        edit_bones = armature.data.edit_bones  # noqa: F841

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
        vrm_helper.Bones_rename(bpy.context)


# DeprecationWarning
class ICYP_OT_select_helper(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "mesh.icyp_select_helper"
    bl_label = "VRM importer internal only func"
    bl_description = "VRM importer internal only"
    bl_options = {"REGISTER", "UNDO"}

    bpy.types.Scene.icyp_select_helper_select_list = list()

    def execute(self, context: bpy.types.Context) -> Set[str]:
        bpy.ops.object.mode_set(mode="OBJECT")
        for vid in bpy.types.Scene.icyp_select_helper_select_list:
            bpy.context.active_object.data.vertices[vid].select = True
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.types.Scene.icyp_select_helper_select_list = list()
        return {"FINISHED"}


def shader_node_group_import(shader_node_group_name: str) -> None:
    if shader_node_group_name in bpy.data.node_groups:
        return
    filedir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "resources",
        "material_node_groups.blend",
        "NodeTree",
    )
    filepath = os.path.join(filedir, shader_node_group_name)
    bpy.ops.wm.append(
        filepath=filepath,
        filename=shader_node_group_name,
        directory=filedir,
    )
