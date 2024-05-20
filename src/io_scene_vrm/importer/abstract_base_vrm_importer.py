# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2018 iCyP

import base64
import contextlib
import functools
import math
import operator
import os
import re
import secrets
import shutil
import struct
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import bpy
import mathutils
from bpy.types import (
    Armature,
    Context,
    Image,
    Material,
    Mesh,
    Object,
    SpaceView3D,
)
from mathutils import Matrix

from ..common import deep, shader
from ..common.deep import Json, make_json
from ..common.fs import (
    create_unique_indexed_directory_path,
    create_unique_indexed_file_path,
)
from ..common.gl import GL_FLOAT, GL_LINEAR, GL_REPEAT, GL_UNSIGNED_SHORT
from ..common.gltf import FLOAT_NEGATIVE_MAX, FLOAT_POSITIVE_MAX, pack_glb, parse_glb
from ..common.logging import get_logger
from ..common.preferences import ImportPreferencesProtocol
from .gltf2_addon_importer_user_extension import Gltf2AddonImporterUserExtension
from .vrm_parser import ParseResult, remove_unsafe_path_chars

logger = get_logger(__name__)


class AbstractBaseVrmImporter(ABC):
    def __init__(
        self,
        context: Context,
        parse_result: ParseResult,
        preferences: ImportPreferencesProtocol,
    ) -> None:
        self.context = context
        self.parse_result = parse_result
        self.preferences = preferences

        self.meshes: dict[int, Object] = {}
        self.images: dict[int, Image] = {}
        self.armature: Optional[Object] = None
        self.bone_names: dict[int, str] = {}
        self.materials: dict[int, Material] = {}
        self.primitive_obj_dict: Optional[dict[Optional[int], list[float]]] = None
        self.mesh_joined_objects = None
        self.bone_child_object_world_matrices: dict[str, Matrix] = {}

        self.import_id = Gltf2AddonImporterUserExtension.update_current_import_id()
        self.temp_object_name_count = 0
        self.object_names: dict[int, str] = {}
        self.mesh_object_names: dict[int, str] = {}

    @abstractmethod
    def make_materials(self) -> None:
        pass

    @abstractmethod
    def load_gltf_extensions(self) -> None:
        pass

    @abstractmethod
    def find_vrm_bone_node_indices(self) -> list[int]:
        pass

    def import_vrm(self) -> None:
        wm = self.context.window_manager
        wm.progress_begin(0, 8)
        try:
            affected_object = self.scene_init()
            wm.progress_update(1)
            self.import_gltf2_with_indices()
            wm.progress_update(2)
            if self.preferences.extract_textures_into_folder:
                self.extract_textures(repack=False)
            elif bpy.app.version < (3, 1):
                self.extract_textures(repack=True)
            else:
                self.assign_packed_image_filepaths()

            wm.progress_update(3)
            self.use_fake_user_for_thumbnail()
            wm.progress_update(4)
            if self.parse_result.vrm1_extension or self.parse_result.vrm0_extension:
                self.make_materials()
            wm.progress_update(5)
            if self.parse_result.vrm1_extension or self.parse_result.vrm0_extension:
                self.load_gltf_extensions()
            wm.progress_update(6)
            self.finishing(affected_object)
            wm.progress_update(7)
            self.viewport_setup()
        finally:
            try:
                Gltf2AddonImporterUserExtension.clear_current_import_id()
            finally:
                wm.progress_end()

    @property
    def armature_data(self) -> Armature:
        if not self.armature:
            message = "armature is not set"
            raise AssertionError(message)
        armature_data = self.armature.data
        if not isinstance(armature_data, Armature):
            message = f"{type(armature_data)} is not an Armature"
            raise TypeError(message)
        return armature_data

    def save_bone_child_object_world_matrices(self, armature: Object) -> None:
        for obj in bpy.data.objects:
            if (
                obj.parent_type == "BONE"
                and obj.parent == armature
                and obj.parent_bone in self.armature_data.bones
            ):
                self.bone_child_object_world_matrices[obj.name] = (
                    obj.matrix_world.copy()
                )

    def load_bone_child_object_world_matrices(self, armature: Object) -> None:
        for obj in bpy.data.objects:
            if (
                obj.parent_type == "BONE"
                and obj.parent == armature
                and obj.parent_bone in self.armature_data.bones
                and obj.name in self.bone_child_object_world_matrices
            ):
                obj.matrix_world = self.bone_child_object_world_matrices[
                    obj.name
                ].copy()

    def scene_init(self) -> Optional[Object]:
        # active_objectがhideだとbpy.ops.object.mode_set.poll()に失敗してエラーが出るの
        # でその回避と、それを元に戻す
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

    def finishing(self, affected_object: Optional[Object]) -> None:
        # initで弄ったやつを戻す
        if affected_object is not None:
            affected_object.hide_viewport = True

        for obj in self.context.selected_objects:
            obj.select_set(False)

        # image_path_to Texture

    def use_fake_user_for_thumbnail(self) -> None:
        # サムネイルはVRMの仕様ではimageのインデックスとあるが、UniVRMの実装ではtexture
        # のインデックスになっている
        # https://github.com/vrm-c/UniVRM/blob/v0.67.0/Assets/VRM/Runtime/IO/VRMImporterContext.cs#L308
        json_texture_index = deep.get(
            self.parse_result.vrm0_extension, ["meta", "texture"]
        )
        if not isinstance(json_texture_index, int):
            return
        json_textures = self.parse_result.json_dict.get("textures", [])
        if not isinstance(json_textures, list):
            logger.warning('json["textures"] is not list')
            return
        if json_texture_index not in (-1, None) and (
            "textures" in self.parse_result.json_dict
            and len(json_textures) > json_texture_index
        ):
            json_texture = json_textures[json_texture_index]
            if isinstance(json_texture, dict):
                image_index = json_texture.get("source")
                if isinstance(image_index, int) and image_index in self.images:
                    self.images[image_index].use_fake_user = True

    @staticmethod
    def reset_material(material: Material) -> None:
        if not material.use_nodes:
            material.use_nodes = True
        shader.clear_node_tree(material.node_tree)
        if material.alpha_threshold != 0.5:
            material.alpha_threshold = 0.5
        if material.blend_method != "OPAQUE":
            material.blend_method = "OPAQUE"
        if material.shadow_method != "OPAQUE":
            material.shadow_method = "OPAQUE"
        if material.use_backface_culling:
            material.use_backface_culling = False
        if material.show_transparent_back:
            material.show_transparent_back = False
        if material.node_tree:
            material.node_tree.nodes.new("ShaderNodeOutputMaterial")
        else:
            logger.error(f"No node tree for material {material.name}")

    def assign_packed_image_filepaths(self) -> None:
        # Assign image filepath for fbx export
        for image in self.images.values():
            if image.packed_file is None:
                continue
            if image.filepath:
                continue
            image_name = Path(image.filepath_from_user()).stem
            if not image_name:
                image_name = remove_unsafe_path_chars(image.name)
            image_type = image.file_format.lower()
            if bpy.app.version >= (3, 4):
                image.filepath_raw = f"//textures{os.sep}{image_name}.{image_type}"
            else:
                image.filepath_raw = f"//{image_name}.{image_type}"

    def extract_textures(self, repack: bool) -> None:
        dir_path = self.parse_result.filepath.with_suffix(".vrm.textures").absolute()
        if self.preferences.make_new_texture_folder or repack:
            dir_path = create_unique_indexed_directory_path(dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)

        if bpy.app.version >= (3, 1) and not bpy.data.filepath:
            temp_blend_path = None
            for _ in range(10000):
                suffix = (
                    ".temp"
                    + "".join(str(secrets.randbelow(10)) for _ in range(10))
                    + ".blend"
                )
                temp_blend_path = self.parse_result.filepath.with_suffix(suffix)
                if not temp_blend_path.exists():
                    break
            if temp_blend_path is not None:
                bpy.ops.wm.save_as_mainfile(filepath=str(temp_blend_path))

        for image_index, image in self.images.items():
            image_name = Path(image.filepath_from_user()).name
            if image_name:
                legacy_image_name_prefix = self.import_id + "Image"
                if image_name.startswith(legacy_image_name_prefix):
                    image_name = re.sub(
                        r"^\d+_",
                        "",
                        image_name[
                            slice(len(legacy_image_name_prefix), len(image_name))
                        ],
                    )
            if not image_name:
                image_name = image.name
            image_type = image.file_format.lower()
            if len(image_name) >= 100:
                new_image_name = "texture_too_long_name_" + str(image_index)
                logger.warning(
                    f"too long name image: {image_name} is named {new_image_name}"
                )
                image_name = new_image_name

            image_name = remove_unsafe_path_chars(image_name)
            if not image_name:
                image_name = "_"
            image_path = dir_path / image_name
            if not image_name.lower().endswith("." + image_type.lower()) and not (
                image_name.lower().endswith(".jpg") and image_type.lower() == "jpeg"
            ):
                image_path = image_path.with_name(image_path.name + "." + image_type)

            try:
                image.unpack(method="WRITE_ORIGINAL")
            except RuntimeError:
                logger.exception(f"Failed to unpack {image.name}")
                continue

            image_original_path_str = image.filepath_from_user()
            if not image_original_path_str:
                continue
            image_original_file_path = Path(image_original_path_str)
            if not image_original_file_path.exists():
                continue
            image_bytes = image_original_file_path.read_bytes()
            with contextlib.suppress(OSError):
                image_original_file_path.unlink()
            image_path = create_unique_indexed_file_path(image_path, image_bytes)
            if image.filepath != str(image_path):
                image.filepath = str(image_path)
            image.reload()
            if repack:
                image.pack()

        if repack:
            shutil.rmtree(dir_path, ignore_errors=True)

    # VRM再インポートを繰り返すことでボーンが増殖しないように注意。
    # 特に注意するべきもの:
    # - ルートボーン
    # - メッシュがペアレンティングされているボーン
    def find_retain_node_indices(self, scene_dict: dict[str, Json]) -> list[int]:
        scene_node_index_jsons = scene_dict.get("nodes")
        if not isinstance(scene_node_index_jsons, list):
            return []
        scene_node_indices = [
            index for index in scene_node_index_jsons if isinstance(index, int)
        ]
        json_dict = self.parse_result.json_dict
        node_dict_jsons = json_dict.get("nodes")
        if not isinstance(node_dict_jsons, list):
            return []
        node_dicts = [
            node_dict for node_dict in node_dict_jsons if isinstance(node_dict, dict)
        ]
        skin_dict_jsons = json_dict.get("skins")
        if not isinstance(skin_dict_jsons, list):
            skin_dict_jsons = []
        skin_dicts = [
            skin_dict for skin_dict in skin_dict_jsons if isinstance(skin_dict, dict)
        ]

        bone_node_indices = self.find_vrm_bone_node_indices()

        # シーンノードツリーのうち、hipsボーンが存在するツリーの全てのノードを集める。
        # また、そのツリーのルートノードもボーン扱いする。
        all_scene_node_indices: list[int] = []
        hips_found = False
        for scene_node_index in scene_node_indices:
            all_scene_node_indices.clear()

            search_scene_node_indices = [scene_node_index]
            while search_scene_node_indices:
                search_scene_node_index = search_scene_node_indices.pop()
                if search_scene_node_index == self.parse_result.hips_node_index:
                    bone_node_indices.append(scene_node_index)
                    hips_found = True
                if not 0 <= search_scene_node_index < len(node_dicts):
                    continue
                node_dict = node_dicts[search_scene_node_index]
                all_scene_node_indices.append(search_scene_node_index)
                child_indices = node_dict.get("children")
                if not isinstance(child_indices, list):
                    continue
                for child_index in child_indices:
                    if not isinstance(child_index, int):
                        continue
                    if child_index in all_scene_node_indices:
                        # Avoid recursive nodes
                        continue
                    search_scene_node_indices.append(child_index)
            if hips_found:
                break
        if not hips_found:
            return []

        all_scene_node_indices = list(dict.fromkeys(all_scene_node_indices))  # Distinct

        # skinに登録されているインデックスもボーン扱いする
        for node_index in all_scene_node_indices:
            if not 0 <= node_index < len(node_dicts):
                continue
            node_dict = node_dicts[node_index]
            skin_index = node_dict.get("skin")
            if not isinstance(skin_index, int) or not 0 <= skin_index < len(skin_dicts):
                continue
            skin_dict = skin_dicts[skin_index]
            skeleton_index = skin_dict.get("skeleton")
            if isinstance(skeleton_index, int):
                bone_node_indices.append(skeleton_index)
            joint_indices = skin_dict.get("joints")
            if isinstance(joint_indices, list):
                for joint_index in joint_indices:
                    if isinstance(joint_index, int):
                        bone_node_indices.append(joint_index)

        # ボーンインデックスからシーンノードindexに入ってないヤツを削除
        for bone_node_index in list(bone_node_indices):
            if bone_node_index not in all_scene_node_indices:
                bone_node_indices.remove(bone_node_index)

        # 現在見つかっているボーンノードから、メッシュノードにぶつかるまで子供を追加
        search_bone_node_indices = list(bone_node_indices)
        while search_bone_node_indices:
            search_bone_node_index = search_bone_node_indices.pop()
            if not 0 <= search_bone_node_index < len(node_dicts):
                continue
            node_dict = node_dicts[search_bone_node_index]
            if isinstance(node_dict.get("mesh"), int):
                continue

            bone_node_indices.append(search_bone_node_index)

            child_indices = node_dict.get("children")
            if not isinstance(child_indices, list):
                continue
            for child_index in child_indices:
                if not isinstance(child_index, int):
                    continue
                if child_index in bone_node_indices:
                    continue
                search_bone_node_indices.append(child_index)

        # メッシュノードの子供にボーンノードが存在する場合は、
        # そのメッシュノードもボーン扱いする
        bone_node_indices.extend(
            functools.reduce(
                operator.iconcat,
                [
                    self.find_middle_bone_indices(
                        node_dicts, bone_node_indices, bone_node_index, []
                    )
                    for bone_node_index in bone_node_indices
                ],
                [],
            )
        )

        return list(dict.fromkeys(bone_node_indices))  # Distinct

    def find_middle_bone_indices(
        self,
        node_dicts: list[dict[str, Json]],
        bone_node_indices: list[int],
        bone_node_index: int,
        middle_bone_node_indices: list[int],
    ) -> list[int]:
        if not 0 <= bone_node_index < len(node_dicts):
            return []
        node_dict = node_dicts[bone_node_index]
        child_indices = node_dict.get("children")
        if not isinstance(child_indices, list):
            return []

        result = []
        for child_index in child_indices:
            if not isinstance(child_index, int):
                continue
            if not 0 <= child_index < len(node_dicts):
                continue
            if child_index in bone_node_indices:
                result.extend(middle_bone_node_indices)
                continue
            result.extend(
                self.find_middle_bone_indices(
                    node_dicts,
                    bone_node_indices,
                    child_index,
                    [*middle_bone_node_indices, bone_node_index],
                )
            )
        return result

    def import_gltf2_with_indices(self) -> None:
        json_dict, body_binary = parse_glb(self.parse_result.filepath.read_bytes())

        for key in ["nodes", "materials", "meshes"]:
            if key not in json_dict or not isinstance(json_dict[key], list):
                continue
            value_dicts = json_dict.get(key)
            if not isinstance(value_dicts, list):
                continue
            for index, value_dict in enumerate(value_dicts):
                if not isinstance(value_dict, dict):
                    continue
                extras_dict = value_dict.get("extras")
                if not isinstance(extras_dict, dict):
                    extras_dict = {}
                    value_dict["extras"] = extras_dict

                extras_dict.update({self.import_id + key.capitalize(): index})
                mesh_index = value_dict.get("mesh")
                if key == "nodes" and isinstance(mesh_index, int):
                    extras_dict.update({self.import_id + "Meshes": mesh_index})

        legacy_image_name_prefix = self.import_id + "Image"
        image_dicts = json_dict.get("images")
        if isinstance(image_dicts, list):
            for image_index, image_dict in enumerate(image_dicts):
                texture_dicts = json_dict.get("textures")
                if not isinstance(texture_dicts, list) or not [
                    True
                    for texture_dict in texture_dicts
                    if isinstance(texture_dict, dict)
                    and texture_dict.get("source") == image_index
                ]:
                    sampler_dicts = json_dict.get("samplers")
                    if not isinstance(sampler_dicts, list):
                        sampler_dicts = []
                        json_dict["samplers"] = sampler_dicts
                    sampler_index = len(sampler_dicts)
                    sampler_dicts.append(
                        {
                            "magFilter": GL_LINEAR,
                            "minFilter": GL_LINEAR,
                            "wrapS": GL_REPEAT,
                            "wrapT": GL_REPEAT,
                        }
                    )

                    if not isinstance(texture_dicts, list):
                        texture_dicts = []
                        json_dict["textures"] = texture_dicts
                    texture_dicts.append(
                        {
                            "sampler": sampler_index,
                            "source": image_index,
                        }
                    )

                if bpy.app.version < (3, 1):
                    if not isinstance(image_dict, dict):
                        continue
                    name = image_dict.get("name")
                    if not isinstance(name, str) or not name:
                        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/709630548cdc184af6ea50b2ff3ddc5450bc0af3/addons/io_scene_gltf2/blender/imp/gltf2_blender_image.py#L54
                        name = f"Image_{image_index}"
                    image_dict["name"] = (
                        legacy_image_name_prefix + str(image_index) + "_" + name
                    )

        mesh_dicts = json_dict.get("meshes")
        if isinstance(mesh_dicts, list):
            for mesh_dict in mesh_dicts:
                if not isinstance(mesh_dict, dict):
                    continue
                mesh_extras_dict = mesh_dict.get("extras")
                if not isinstance(mesh_extras_dict, dict):
                    mesh_extras_dict = {}
                    mesh_dict["extras"] = mesh_extras_dict
                mesh_target_names = mesh_extras_dict.get("targetNames")
                if isinstance(mesh_target_names, list):
                    continue
                primitive_dicts = mesh_dict.get("primitives")
                if not isinstance(primitive_dicts, list):
                    continue
                for primitive_dict in primitive_dicts:
                    if not isinstance(primitive_dict, dict):
                        continue
                    primitive_extras_dict = primitive_dict.get("extras")
                    if not isinstance(primitive_extras_dict, dict):
                        continue
                    primitive_target_names = primitive_extras_dict.get("targetNames")
                    if not isinstance(primitive_target_names, list):
                        continue
                    mesh_extras_dict["targetNames"] = primitive_target_names
                    break

        texture_dicts = json_dict.get("textures")
        if isinstance(texture_dicts, list) and texture_dicts:
            primitive_dicts = []

            for texture_index, _ in enumerate(texture_dicts):
                buffer_dicts = json_dict.get("buffers")
                if not isinstance(buffer_dicts, list):
                    buffer_dicts = []
                    json_dict["buffers"] = buffer_dicts
                position_buffer_index = len(buffer_dicts)
                position_buffer_bytes = struct.pack(
                    "<9f", 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0
                )
                buffer_dicts.append(
                    {
                        "uri": "data:application/gltf-buffer;base64,"
                        + base64.b64encode(position_buffer_bytes).decode("ascii"),
                        "byteLength": len(position_buffer_bytes),
                    }
                )
                texcoord_buffer_index = len(buffer_dicts)
                texcoord_buffer_bytes = struct.pack("<6f", 0.0, 0.0, 1.0, 0.0, 0.0, 1.0)
                buffer_dicts.append(
                    {
                        "uri": "data:application/gltf-buffer;base64,"
                        + base64.b64encode(texcoord_buffer_bytes).decode("ascii"),
                        "byteLength": len(texcoord_buffer_bytes),
                    }
                )

                buffer_view_dicts = json_dict.get("bufferViews")
                if not isinstance(buffer_view_dicts, list):
                    buffer_view_dicts = []
                    json_dict["bufferViews"] = buffer_view_dicts
                position_buffer_view_index = len(buffer_view_dicts)
                buffer_view_dicts.append(
                    {
                        "buffer": position_buffer_index,
                        "byteLength": len(position_buffer_bytes),
                    }
                )
                texcoord_buffer_view_index = len(buffer_view_dicts)
                buffer_view_dicts.append(
                    {
                        "buffer": texcoord_buffer_index,
                        "byteLength": len(texcoord_buffer_bytes),
                    }
                )

                accessor_dicts = json_dict.get("accessors")
                if not isinstance(accessor_dicts, list):
                    accessor_dicts = []
                    json_dict["accessors"] = accessor_dicts
                position_accessors_index = len(accessor_dicts)
                accessor_dicts.append(
                    {
                        "bufferView": position_buffer_view_index,
                        "type": "VEC3",
                        "componentType": GL_FLOAT,
                        "count": 3,
                        "min": [0, 0, 0],
                        "max": [1, 1, 0],
                    }
                )
                texcoord_accessors_index = len(accessor_dicts)
                accessor_dicts.append(
                    {
                        "bufferView": texcoord_buffer_view_index,
                        "type": "VEC2",
                        "componentType": GL_FLOAT,
                        "count": 3,
                    }
                )

                material_dicts = json_dict.get("materials")
                if not isinstance(material_dicts, list):
                    material_dicts = []
                    json_dict["materials"] = material_dicts
                tex_material_index = len(material_dicts)
                material_dicts.append(
                    {
                        "name": self.temp_object_name(),
                        "emissiveTexture": {"index": texture_index},
                    }
                )
                primitive_dicts.append(
                    {
                        "attributes": {
                            "POSITION": position_accessors_index,
                            "TEXCOORD_0": texcoord_accessors_index,
                        },
                        "material": tex_material_index,
                    }
                )

            mesh_dicts = json_dict.get("meshes")
            if not isinstance(mesh_dicts, list):
                mesh_dicts = []
                json_dict["meshes"] = mesh_dicts
            tex_mesh_index = len(mesh_dicts)
            mesh_dicts.append(
                {"name": self.temp_object_name(), "primitives": primitive_dicts}
            )

            node_dicts = json_dict.get("nodes")
            if not isinstance(node_dicts, list):
                node_dicts = []
                json_dict["nodes"] = node_dicts
            tex_node_index = len(node_dicts)
            node_dicts.append({"name": self.temp_object_name(), "mesh": tex_mesh_index})

            scene_dicts = json_dict.get("scenes")
            if not isinstance(scene_dicts, list):
                scene_dicts = []
                json_dict["scenes"] = scene_dicts
            scene_dicts.append(
                {"name": self.temp_object_name(), "nodes": [tex_node_index]}
            )

        scene_dicts = json_dict.get("scenes")
        node_dicts = json_dict.get("nodes")
        if isinstance(scene_dicts, list) and isinstance(node_dicts, list):
            for scene_dict in scene_dicts:
                if not isinstance(scene_dict, dict):
                    continue
                retain_node_indices = self.find_retain_node_indices(scene_dict)
                if not retain_node_indices:
                    continue

                buffer_dicts = json_dict.get("buffers")
                if not isinstance(buffer_dicts, list):
                    buffer_dicts = []
                    json_dict["buffers"] = buffer_dicts
                position_buffer_index = len(buffer_dicts)
                position_buffer_bytes = struct.pack(
                    "<9f", 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0
                )
                buffer_dicts.append(
                    {
                        "uri": "data:application/gltf-buffer;base64,"
                        + base64.b64encode(position_buffer_bytes).decode("ascii"),
                        "byteLength": len(position_buffer_bytes),
                    }
                )
                joints_buffer_index = len(buffer_dicts)
                joints_buffer_bytes = struct.pack(
                    "<12H", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
                )
                buffer_dicts.append(
                    {
                        "uri": "data:application/gltf-buffer;base64,"
                        + base64.b64encode(joints_buffer_bytes).decode("ascii"),
                        "byteLength": len(joints_buffer_bytes),
                    }
                )
                weights_buffer_index = len(buffer_dicts)
                weights_buffer_bytes = struct.pack(
                    "<12f", 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0
                )
                buffer_dicts.append(
                    {
                        "uri": "data:application/gltf-buffer;base64,"
                        + base64.b64encode(weights_buffer_bytes).decode("ascii"),
                        "byteLength": len(weights_buffer_bytes),
                    }
                )

                buffer_view_dicts = json_dict.get("bufferViews")
                if not isinstance(buffer_view_dicts, list):
                    buffer_view_dicts = []
                    json_dict["bufferViews"] = buffer_view_dicts
                position_buffer_view_index = len(buffer_view_dicts)
                buffer_view_dicts.append(
                    {
                        "buffer": position_buffer_index,
                        "byteLength": len(position_buffer_bytes),
                    }
                )
                joints_buffer_view_index = len(buffer_view_dicts)
                buffer_view_dicts.append(
                    {
                        "buffer": joints_buffer_index,
                        "byteLength": len(joints_buffer_bytes),
                    }
                )
                weights_buffer_view_index = len(buffer_view_dicts)
                buffer_view_dicts.append(
                    {
                        "buffer": weights_buffer_index,
                        "byteLength": len(weights_buffer_bytes),
                    }
                )

                accessor_dicts = json_dict.get("accessors")
                if not isinstance(accessor_dicts, list):
                    accessor_dicts = []
                    json_dict["accessors"] = accessor_dicts
                position_accessors_index = len(accessor_dicts)
                accessor_dicts.append(
                    {
                        "bufferView": position_buffer_view_index,
                        "type": "VEC3",
                        "componentType": GL_FLOAT,
                        "count": 3,
                        "min": [0, 0, 0],
                        "max": [1, 1, 0],
                    }
                )
                joints_accessors_index = len(accessor_dicts)
                accessor_dicts.append(
                    {
                        "bufferView": joints_buffer_view_index,
                        "type": "VEC4",
                        "componentType": GL_UNSIGNED_SHORT,
                        "count": 3,
                    }
                )
                weights_accessors_index = len(accessor_dicts)
                accessor_dicts.append(
                    {
                        "bufferView": weights_buffer_view_index,
                        "type": "VEC4",
                        "componentType": GL_FLOAT,
                        "count": 3,
                    }
                )

                primitive_dicts = [
                    {
                        "attributes": {
                            "POSITION": position_accessors_index,
                            "JOINTS_0": joints_accessors_index,
                            "WEIGHTS_0": weights_accessors_index,
                        }
                    }
                ]

                mesh_dicts = json_dict.get("meshes")
                if not isinstance(mesh_dicts, list):
                    mesh_dicts = []
                    json_dict["meshes"] = mesh_dicts
                skin_mesh_index = len(mesh_dicts)
                mesh_dicts.append(
                    make_json(
                        {"name": self.temp_object_name(), "primitives": primitive_dicts}
                    )
                )

                skin_dicts = json_dict.get("skins")
                if not isinstance(skin_dicts, list):
                    skin_dicts = []
                    json_dict["skins"] = skin_dicts
                skin_index = len(skin_dicts)
                skin_dicts.append({"joints": list(retain_node_indices)})

                node_dicts = json_dict.get("nodes")
                if not isinstance(node_dicts, list):
                    node_dicts = []
                    json_dict["nodes"] = node_dicts
                skin_node_index = len(node_dicts)
                node_dicts.append(
                    {
                        "name": self.temp_object_name(),
                        "mesh": skin_mesh_index,
                        "skin": skin_index,
                    }
                )

                scene_nodes = scene_dict.get("nodes")
                if not isinstance(scene_nodes, list):
                    scene_nodes = []
                    scene_dict["nodes"] = scene_nodes

                scene_nodes.append(skin_node_index)

        # glTF 2.0アドオンが未対応のエクステンションが
        # "extensionsRequired"に含まれている場合はエラーになる。それを抑止。
        extensions_required = json_dict.get("extensionsRequired")
        if isinstance(extensions_required, list):
            for supported_extension in [
                "VRM",
                "VRMC_vrm",
                "VRMC_springBone",
                "VRMC_node_constraint",
                "VRMC_materials_mtoon",
                "VRMC_materials_hdr_emissiveMultiplier",
            ]:
                while supported_extension in extensions_required:
                    extensions_required.remove(supported_extension)

        # Unfortunately such VRMs exist.
        accessor_dicts = json_dict.get("accessors")
        if isinstance(accessor_dicts, list):
            for accessor_dict in accessor_dicts:
                if not isinstance(accessor_dict, dict):
                    continue

                max_values = accessor_dict.get("max")
                if isinstance(max_values, list):
                    for i, max_value in enumerate(list(max_values)):
                        if not isinstance(max_value, (float, int)) or math.isnan(
                            max_value
                        ):
                            max_values[i] = FLOAT_POSITIVE_MAX
                        elif math.isinf(max_value):
                            max_values[i] = (
                                FLOAT_POSITIVE_MAX
                                if max_value > 0
                                else FLOAT_NEGATIVE_MAX
                            )

                min_values = accessor_dict.get("min")
                if isinstance(min_values, list):
                    for i, min_value in enumerate(list(min_values)):
                        if not isinstance(min_value, (float, int)) or math.isnan(
                            min_value
                        ):
                            min_values[i] = FLOAT_NEGATIVE_MAX
                        elif math.isinf(min_value):
                            min_values[i] = (
                                FLOAT_POSITIVE_MAX
                                if min_value > 0
                                else FLOAT_NEGATIVE_MAX
                            )

        if self.parse_result.spec_version_number < (1, 0):
            bone_heuristic = "FORTUNE"
        else:
            bone_heuristic = "BLENDER"
        full_vrm_import_success = False
        with tempfile.TemporaryDirectory() as temp_dir:
            indexed_vrm_filepath = Path(temp_dir, "indexed.vrm")
            indexed_vrm_filepath.write_bytes(pack_glb(json_dict, body_binary))
            try:
                bpy.ops.import_scene.gltf(
                    filepath=str(indexed_vrm_filepath),
                    import_pack_images=True,
                    bone_heuristic=bone_heuristic,
                    guess_original_bind_pose=False,
                )
                full_vrm_import_success = True
            except RuntimeError:
                logger.exception(
                    f'Failed to import "{indexed_vrm_filepath}"'
                    + f' generated from "{self.parse_result.filepath}"'
                    + " using glTF 2.0 Add-on"
                )
                self.cleanup_gltf2_with_indices()
        if not full_vrm_import_success:
            # Some VRMs have broken animations.
            # https://github.com/vrm-c/UniVRM/issues/1522
            # https://github.com/saturday06/VRM-Addon-for-Blender/issues/58
            json_dict.pop("animations", None)
            with tempfile.TemporaryDirectory() as temp_dir:
                indexed_vrm_filepath = Path(temp_dir, "indexed.vrm")
                indexed_vrm_filepath.write_bytes(pack_glb(json_dict, body_binary))
                try:
                    bpy.ops.import_scene.gltf(
                        filepath=str(indexed_vrm_filepath),
                        import_pack_images=True,
                        bone_heuristic=bone_heuristic,
                        guess_original_bind_pose=False,
                    )
                except RuntimeError:
                    logger.exception(
                        f'Failed to import "{indexed_vrm_filepath}"'
                        + f' generated from "{self.parse_result.filepath}"'
                        + " using glTF 2.0 Add-on without animations key"
                    )
                    self.cleanup_gltf2_with_indices()
                    raise

        extras_node_index_key = self.import_id + "Nodes"
        for obj in self.context.selectable_objects:
            node_index = obj.pop(extras_node_index_key, None)
            if isinstance(node_index, int):
                self.object_names[node_index] = obj.name
                if isinstance(obj.data, Mesh):
                    self.mesh_object_names[node_index] = obj.name
            data = obj.data
            if isinstance(data, Mesh):
                data.pop(extras_node_index_key, None)

            if not isinstance(data, Armature):
                continue

            for pose_bone in obj.pose.bones:
                pose_bone.pop(extras_node_index_key, None)

            for bone_name, bone in data.bones.items():
                bone_node_index = bone.pop(extras_node_index_key, None)
                if not isinstance(bone_node_index, int):
                    continue
                node_dicts = self.parse_result.json_dict.get("nodes")
                if not isinstance(node_dicts, list):
                    continue
                if 0 <= bone_node_index < len(node_dicts):
                    node_dict = node_dicts[bone_node_index]
                    if isinstance(node_dict, dict):
                        node_dict["name"] = bone_name
                self.bone_names[bone_node_index] = bone_name
                if (
                    self.armature is not None
                    or bone_node_index != self.parse_result.hips_node_index
                ):
                    continue

                if self.parse_result.spec_version_number < (1, 0):
                    vrm0_humanoid = data.vrm_addon_extension.vrm0.humanoid
                    vrm0_humanoid.initial_automatic_bone_assignment = False
                else:
                    vrm1_humanoid = data.vrm_addon_extension.vrm1.humanoid
                    vrm1_humanoid.human_bones.initial_automatic_bone_assignment = False
                self.armature = obj

        if (
            self.armature is not None
            and self.parse_result.spec_version_number < (1, 0)
            and self.armature.rotation_mode == "QUATERNION"
        ):
            obj = self.armature
            obj.rotation_quaternion.rotate(mathutils.Euler((0.0, 0.0, math.pi), "XYZ"))
            if self.context.object is not None:
                bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            previous_active = self.context.view_layer.objects.active
            try:
                self.context.view_layer.objects.active = obj

                bone_name_to_roll = {}
                bpy.ops.object.mode_set(mode="EDIT")
                if isinstance(obj.data, Armature):
                    for edit_bone in obj.data.edit_bones:
                        bone_name_to_roll[edit_bone.name] = edit_bone.roll
                bpy.ops.object.mode_set(mode="OBJECT")

                bpy.ops.object.transform_apply(
                    location=False, rotation=True, scale=False, properties=False
                )

                self.save_bone_child_object_world_matrices(obj)

                bpy.ops.object.mode_set(mode="EDIT")
                if isinstance(obj.data, Armature):
                    edit_bones = [
                        edit_bone
                        for edit_bone in obj.data.edit_bones
                        if not edit_bone.parent
                    ]
                    while edit_bones:
                        edit_bone = edit_bones.pop(0)
                        roll = bone_name_to_roll.get(edit_bone.name)
                        if roll is not None:
                            edit_bone.roll = roll
                        edit_bones.extend(edit_bone.children)
                bpy.ops.object.mode_set(mode="OBJECT")
            finally:
                self.context.view_layer.objects.active = previous_active

        extras_mesh_index_key = self.import_id + "Meshes"
        for obj in self.context.selectable_objects:
            data = obj.data
            if not isinstance(data, Mesh):
                continue
            custom_mesh_index = data.get(extras_mesh_index_key)
            if isinstance(custom_mesh_index, int):
                self.meshes[custom_mesh_index] = obj
            else:
                custom_mesh_index = obj.get(extras_mesh_index_key)
                if isinstance(custom_mesh_index, int):
                    self.meshes[custom_mesh_index] = obj

            obj.pop(extras_mesh_index_key, None)
            data.pop(extras_mesh_index_key, None)

            # ここでupdateしないとエクスポート時にCustom Propertyが復活することがある
            data.update()

        extras_material_index_key = self.import_id + "Materials"
        for material in bpy.data.materials:
            if self.is_temp_object_name(material.name):
                continue
            material_index = material.pop(extras_material_index_key, None)
            if isinstance(material_index, int):
                self.materials[material_index] = material

        for image in list(bpy.data.images):
            custom_image_index = image.get(self.import_id)
            if not isinstance(custom_image_index, int) and image.name.startswith(
                legacy_image_name_prefix
            ):
                custom_image_index_str = "".join(
                    image.name.split(legacy_image_name_prefix)[1:]
                ).split("_", maxsplit=1)[0]
                with contextlib.suppress(ValueError):
                    custom_image_index = int(custom_image_index_str)
            if not isinstance(custom_image_index, int):
                continue
            image_dicts = json_dict.get("images")
            if isinstance(image_dicts, list) and 0 <= custom_image_index < len(
                image_dicts
            ):
                # image.nameはインポート時に勝手に縮められてしまうことがあるので、
                # jsonの値から復元する
                image_dict = image_dicts[custom_image_index]
                indexed_image_name = None

                if isinstance(image_dict, dict):
                    indexed_image_name = image_dict.get("name")

                if isinstance(indexed_image_name, str):
                    if indexed_image_name.startswith(legacy_image_name_prefix):
                        indexed_image_name = "_".join(indexed_image_name.split("_")[1:])
                else:
                    indexed_image_name = None

                if indexed_image_name:
                    image.name = indexed_image_name
                else:
                    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/709630548cdc184af6ea50b2ff3ddc5450bc0af3/addons/io_scene_gltf2/blender/imp/gltf2_blender_image.py#L54
                    image.name = f"Image_{custom_image_index}"

            else:
                image.name = "_".join(image.name.split("_")[1:])

            self.images[custom_image_index] = image

        if self.context.object is not None and self.context.object.mode == "EDIT":
            bpy.ops.object.mode_set(mode="OBJECT")

        while True:
            temp_object = next(
                (
                    o
                    for o in bpy.data.objects
                    if o and o.users <= 1 and self.is_temp_object_name(o.name)
                ),
                None,
            )
            if not temp_object:
                break
            bpy.data.objects.remove(temp_object)

        while True:
            temp_mesh = next(
                (
                    m
                    for m in bpy.data.meshes
                    if m and m.users <= 1 and self.is_temp_object_name(m.name)
                ),
                None,
            )
            if not temp_mesh:
                break
            bpy.data.meshes.remove(temp_mesh)

        while True:
            temp_material = next(
                (
                    m
                    for m in bpy.data.materials
                    if m and m.users <= 1 and self.is_temp_object_name(m.name)
                ),
                None,
            )
            if not temp_material:
                break
            bpy.data.materials.remove(temp_material)

        if self.armature is None:
            logger.warning("Failed to read VRM Humanoid")

    def cleanup_gltf2_with_indices(self) -> None:
        if (
            self.context.view_layer.objects.active is not None
            and self.context.view_layer.objects.active.mode != "OBJECT"
        ):
            bpy.ops.object.mode_set(mode="OBJECT")
        meshes_key = self.import_id + "Meshes"
        nodes_key = self.import_id + "Nodes"
        remove_objs = []
        for obj in list(self.context.scene.collection.objects):
            if isinstance(obj.data, Armature):
                for bone in obj.data.bones:
                    if nodes_key in bone:
                        remove_objs.append(obj)
                        break
                continue

            if isinstance(obj.data, Mesh) and (
                nodes_key in obj.data
                or meshes_key in obj.data
                or self.is_temp_object_name(obj.data.name)
            ):
                remove_objs.append(obj)
                continue

            if (
                nodes_key in obj
                or meshes_key in obj
                or self.is_temp_object_name(obj.name)
            ):
                remove_objs.append(obj)

        bpy.ops.object.select_all(action="DESELECT")
        for obj in remove_objs:
            obj.select_set(True)
        bpy.ops.object.delete()

        retry = True
        while retry:
            retry = False
            for obj in bpy.data.objects:
                if obj in remove_objs and not obj.users:
                    retry = True
                    bpy.data.objects.remove(obj, do_unlink=True)

    def temp_object_name(self) -> str:
        self.temp_object_name_count += 1
        return f"{self.import_id}Temp_{self.temp_object_name_count}_"

    def is_temp_object_name(self, name: str) -> bool:
        return name.startswith(f"{self.import_id}Temp_")

    def viewport_setup(self) -> None:
        if self.armature:
            if self.preferences.set_armature_display_to_wire:
                self.armature.display_type = "WIRE"
            if self.preferences.set_armature_display_to_show_in_front:
                self.armature.show_in_front = True
            if self.preferences.set_armature_bone_shape_to_default:
                for bone in self.armature.pose.bones:
                    bone.custom_shape = None

        if self.preferences.set_view_transform_to_standard_on_import:
            # https://github.com/saturday06/VRM-Addon-for-Blender/issues/336#issuecomment-1760729404
            view_settings = self.context.scene.view_settings
            try:
                view_settings.view_transform = "Standard"
            except TypeError:
                logger.exception(
                    "scene.view_settings.view_transform"
                    + ' doesn\'t support "Standard".'
                )

        if self.preferences.set_shading_type_to_material_on_import:
            screen = self.context.screen
            for area in screen.areas:
                for space in area.spaces:
                    if space.type == "VIEW_3D" and isinstance(space, SpaceView3D):
                        space.shading.type = "MATERIAL"
