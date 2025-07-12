# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
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
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import bpy
from bpy.path import clean_name
from bpy.types import (
    Armature,
    Context,
    Image,
    Material,
    Mesh,
    Object,
    SpaceView3D,
)
from mathutils import Euler, Matrix

from ..common import shader
from ..common.convert import Json
from ..common.deep import make_json
from ..common.fs import (
    create_unique_indexed_directory_path,
    create_unique_indexed_file_path,
)
from ..common.gl import GL_FLOAT, GL_LINEAR, GL_REPEAT, GL_UNSIGNED_SHORT
from ..common.gltf import FLOAT_NEGATIVE_MAX, FLOAT_POSITIVE_MAX, pack_glb, parse_glb
from ..common.logger import get_logger
from ..common.preferences import ImportPreferencesProtocol
from ..common.progress import PartialProgress, create_progress
from ..common.rotation import (
    get_rotation_as_quaternion,
    set_rotation_without_mode_change,
)
from ..common.workspace import save_workspace
from ..editor.extension import get_armature_extension
from ..external.io_scene_gltf2_support import (
    ImportSceneGltfArguments,
    import_scene_gltf,
)
from .gltf2_addon_importer_user_extension import Gltf2AddonImporterUserExtension
from .license_validation import validate_license

logger = get_logger(__name__)


@dataclass(frozen=True)
class ParseResult:
    filepath: Path
    json_dict: Mapping[str, Json]
    spec_version_number: tuple[int, int]
    spec_version_str: str
    spec_version_is_stable: bool
    vrm0_extension_dict: Mapping[str, Json]
    vrm1_extension_dict: Mapping[str, Json]
    hips_node_index: Optional[int]


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
        self.bone_child_object_world_matrices: dict[str, Matrix] = {}
        self.import_id = Gltf2AddonImporterUserExtension.update_current_import_id()
        self.temp_object_name_count = 0
        self.object_names: dict[int, str] = {}
        self.mesh_object_names: dict[int, str] = {}
        self.imported_object_names: Optional[list[str]] = None

    @abstractmethod
    def load_materials(self, progress: PartialProgress) -> None:
        pass

    @abstractmethod
    def load_gltf_extensions(self) -> None:
        pass

    @abstractmethod
    def find_vrm_bone_node_indices(self) -> list[int]:
        pass

    def import_vrm(self) -> None:
        try:
            with create_progress(self.context) as progress:
                with save_workspace(self.context):
                    progress.update(0.1)
                    self.import_gltf2_with_indices()
                    progress.update(0.3)
                    self.use_fake_user_for_thumbnail()
                    progress.update(0.4)
                    if (
                        self.parse_result.vrm1_extension_dict
                        or self.parse_result.vrm0_extension_dict
                    ):
                        self.load_materials(progress.partial_progress(0.9))
                    if (
                        self.parse_result.vrm1_extension_dict
                        or self.parse_result.vrm0_extension_dict
                    ):
                        self.load_gltf_extensions()
                    progress.update(0.92)
                    self.setup_viewport()
                    progress.update(0.94)
                    self.context.view_layer.update()
                    progress.update(0.96)

                    # Texture extraction occurs. During this process, .blend file saving
                    # may occur and save callbacks may run, so be careful not to apply
                    # those callbacks to incompletely imported VRM data
                    if self.preferences.extract_textures_into_folder:
                        self.extract_textures(repack=False)
                    elif bpy.app.version < (3, 1):
                        self.extract_textures(repack=True)
                    else:
                        self.assign_packed_image_filepaths()

                self.save_t_pose_action()
                progress.update(0.97)
                self.setup_object_selection_and_activation()
                progress.update(0.98)
        finally:
            Gltf2AddonImporterUserExtension.clear_current_import_id()

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

    @staticmethod
    def enter_save_bone_child_object_transforms(
        context: Context, armature_object: Object
    ) -> Optional[Mapping[str, Matrix]]:
        armature_data = armature_object.data
        if not isinstance(armature_data, Armature):
            return None

        # Save the world matrices of child objects of bones before editing
        context.view_layer.update()
        bone_child_object_world_matrices: dict[str, Matrix] = {}
        for obj in context.blend_data.objects:
            if (
                obj.parent_type == "BONE"
                and obj.parent == armature_object
                and obj.parent_bone in armature_data.bones
            ):
                bone_child_object_world_matrices[obj.name] = obj.matrix_world.copy()

        return bone_child_object_world_matrices

    @staticmethod
    def leave_save_bone_child_object_transforms(
        context: Context,
        armature_object: Object,
        bone_child_object_world_matrices: Mapping[str, Matrix],
    ) -> None:
        armature_data = armature_object.data
        if not isinstance(armature_data, Armature):
            message = f"{type(armature_data)} is not an Armature"
            raise TypeError(message)
        # Restore the world matrices of child objects of bones before editing
        context.view_layer.update()
        for name, matrix_world in bone_child_object_world_matrices.items():
            restore_obj = context.blend_data.objects.get(name)
            if (
                restore_obj
                and restore_obj.parent_type == "BONE"
                and restore_obj.parent == armature_object
                and restore_obj.parent_bone in armature_data.bones
            ):
                restore_obj.matrix_world = matrix_world.copy()
        context.view_layer.update()

    @staticmethod
    @contextlib.contextmanager
    def save_bone_child_object_transforms(
        context: Context, armature: Object
    ) -> Iterator[Armature]:
        bone_child_object_world_matrices = (
            AbstractBaseVrmImporter.enter_save_bone_child_object_transforms(
                context, armature
            )
        )
        try:
            with save_workspace(context, armature, mode="EDIT"):
                armature_data = armature.data
                if not isinstance(armature_data, Armature):
                    message = f"{type(armature_data)} is not an Armature"
                    raise TypeError(message)
                yield armature_data
                # After yield, bpy native objects may be deleted or frames may advance
                # making them invalid. Accessing them in this state can cause crashes,
                # so be careful not to access such native objects after yield
        finally:
            if bone_child_object_world_matrices is not None:
                AbstractBaseVrmImporter.leave_save_bone_child_object_transforms(
                    context, armature, bone_child_object_world_matrices
                )

    def use_fake_user_for_thumbnail(self) -> None:
        # The thumbnail is specified as an image index in the VRM specification,
        # but in UniVRM's implementation it's a texture index
        # https://github.com/vrm-c/UniVRM/blob/v0.67.0/Assets/VRM/Runtime/IO/VRMImporterself.context.cs#L308
        meta_dict = self.parse_result.vrm0_extension_dict.get("meta")
        if not isinstance(meta_dict, dict):
            return

        thumbnail_texture_index = meta_dict.get("texture")
        if not isinstance(thumbnail_texture_index, int):
            return

        texture_dicts = self.parse_result.json_dict.get("textures", [])
        if not isinstance(texture_dicts, list):
            logger.warning('json["textures"] is not list')
            return

        if not (0 <= thumbnail_texture_index < len(texture_dicts)):
            return

        thumbnail_texture_dict = texture_dicts[thumbnail_texture_index]
        if not isinstance(thumbnail_texture_dict, dict):
            return

        thumbnail_image_index = thumbnail_texture_dict.get("source")
        if not isinstance(thumbnail_image_index, int):
            return

        thumbnail_image = self.images.get(thumbnail_image_index)
        if not thumbnail_image:
            return

        thumbnail_image.use_fake_user = True

    @staticmethod
    def reset_material(material: Material) -> None:
        if not material.use_nodes:
            material.use_nodes = True
        shader.clear_node_tree(material.node_tree)
        if material.alpha_threshold != 0.5:
            material.alpha_threshold = 0.5
        if material.blend_method != "OPAQUE":
            material.blend_method = "OPAQUE"
        if bpy.app.version < (4, 3) and material.shadow_method != "OPAQUE":
            material.shadow_method = "OPAQUE"
        if material.use_backface_culling:
            material.use_backface_culling = False
        if material.show_transparent_back:
            material.show_transparent_back = False
        node_tree = material.node_tree
        if node_tree:
            node_tree.nodes.new("ShaderNodeOutputMaterial")
        else:
            logger.error("No node tree for material %s", material.name)

    def assign_packed_image_filepaths(self) -> None:
        # Assign image filepath for fbx export
        for image in self.images.values():
            if image.packed_file is None:
                continue
            if image.filepath:
                continue
            image_name = Path(image.filepath_from_user()).stem
            if not image_name:
                image_name = clean_name(image.name)
            image_type = image.file_format.lower()
            if bpy.app.version >= (3, 4):
                image.filepath_raw = f"//textures{os.sep}{image_name}.{image_type}"
            else:
                image.filepath_raw = f"//{image_name}.{image_type}"

    def extract_textures(self, *, repack: bool) -> None:
        """Extract textures to a folder as files.

        In Blender 3.1 and later, texture extraction requires saving the .blend file.
        Therefore, the file is saved, but be careful that file save callbacks may run
        during this process.
        """
        dir_path = self.parse_result.filepath.with_suffix(".vrm.textures").absolute()
        if self.preferences.make_new_texture_folder or repack:
            dir_path = create_unique_indexed_directory_path(dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)

        if bpy.app.version >= (3, 1) and not self.context.blend_data.filepath:
            temp_blend_path = None
            for _ in range(10000):
                image_suffix = (
                    ".temp"
                    + "".join(str(secrets.randbelow(10)) for _ in range(10))
                    + ".blend"
                )
                temp_blend_path = self.parse_result.filepath.with_suffix(image_suffix)
                if not temp_blend_path.exists():
                    break
            if temp_blend_path is not None:
                bpy.ops.wm.save_as_mainfile(filepath=str(temp_blend_path))

        for image_index, image in self.images.items():
            image_original_file_path = Path(image.filepath_from_user())
            image_path_stem = image_original_file_path.stem
            if image_path_stem:
                legacy_image_name_prefix = self.import_id + "Image"
                if image_path_stem.startswith(legacy_image_name_prefix):
                    image_path_stem = re.sub(
                        r"^\d+_",
                        "",
                        image_path_stem[len(legacy_image_name_prefix) :],
                    )
            if not image_path_stem:
                image_path_stem = image.name
            if not image_path_stem:
                image_path_stem = f"Image_{image_index}"
            image_path_stem = clean_name(image_path_stem[:100])

            original_image_path_suffix = image_original_file_path.suffix
            detected_image_path_suffix = "." + image.file_format.lower()
            if original_image_path_suffix.lower() != detected_image_path_suffix and (
                original_image_path_suffix.lower(),
                detected_image_path_suffix,
            ) != (".jpg", ".jpeg"):
                image_path_suffix = detected_image_path_suffix
            else:
                image_path_suffix = original_image_path_suffix

            image_path = dir_path / (image_path_stem + image_path_suffix)

            try:
                image.unpack(method="WRITE_ORIGINAL")
            except RuntimeError:
                logger.exception("Failed to unpack %s", image.name)
                continue

            image_unpacked_path_str = image.filepath_from_user()
            if not image_unpacked_path_str:
                continue
            image_unpacked_file_path = Path(image_unpacked_path_str)
            if not image_unpacked_file_path.exists():
                continue

            image_bytes = image_unpacked_file_path.read_bytes()
            with contextlib.suppress(OSError):
                image_unpacked_file_path.unlink()
            image_path = create_unique_indexed_file_path(image_path, image_bytes)
            if image.filepath != str(image_path):
                image.filepath = str(image_path)
            image.reload()
            if repack:
                image.pack()

        if repack:
            shutil.rmtree(dir_path, ignore_errors=True)

    # Be careful not to let bones proliferate by repeating VRM re-import.
    # Things to pay special attention to:
    # - Root bones
    # - Bones that have meshes parented to them
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

        # Collect all nodes in the scene node tree where the hips bone exists.
        # Also treat the root node of that tree as a bone.
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

        # Also treat indices registered in skin as bones
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

        # Remove bone indices that are not in the scene node index
        for bone_node_index in list(bone_node_indices):
            if bone_node_index not in all_scene_node_indices:
                bone_node_indices.remove(bone_node_index)

        # Add children from currently found bone nodes until hitting mesh nodes
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

        # If a mesh node has bone nodes as children,
        # treat that mesh node as a bone too
        bone_node_indices.extend(
            functools.reduce(
                operator.iconcat,
                [
                    self.find_middle_bone_indices(
                        node_dicts, bone_node_indices, bone_node_index, []
                    )
                    for bone_node_index in bone_node_indices
                ],
                list[int](),
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

        result: list[int] = []
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
        json_dict, buffer0_bytes = parse_glb(self.parse_result.filepath.read_bytes())

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
            primitive_dicts = list[Json]()

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

        # Prevent errors when extensions not supported by the glTF 2.0 add-on
        # are included in "extensionsRequired"
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
            indexed_vrm_filepath.write_bytes(pack_glb(json_dict, buffer0_bytes))
            try:
                import_scene_gltf(
                    ImportSceneGltfArguments(
                        filepath=str(indexed_vrm_filepath),
                        import_pack_images=True,
                        bone_heuristic=bone_heuristic,
                        guess_original_bind_pose=False,
                        disable_bone_shape=True,
                        import_scene_as_collection=False,
                    )
                )
                full_vrm_import_success = True
            except RuntimeError:
                logger.exception(
                    'Failed to import "%s" generated from "%s" using glTF 2.0 Add-on',
                    indexed_vrm_filepath,
                    self.parse_result.filepath,
                )
                self.cleanup_gltf2_with_indices()
        if not full_vrm_import_success:
            # Some VRMs have broken animations.
            # https://github.com/vrm-c/UniVRM/issues/1522
            # https://github.com/saturday06/VRM-Addon-for-Blender/issues/58
            json_dict.pop("animations", None)
            with tempfile.TemporaryDirectory() as temp_dir:
                indexed_vrm_filepath = Path(temp_dir, "indexed.vrm")
                indexed_vrm_filepath.write_bytes(pack_glb(json_dict, buffer0_bytes))
                try:
                    import_scene_gltf(
                        ImportSceneGltfArguments(
                            filepath=str(indexed_vrm_filepath),
                            import_pack_images=True,
                            bone_heuristic=bone_heuristic,
                            guess_original_bind_pose=False,
                            disable_bone_shape=True,
                            import_scene_as_collection=False,
                        )
                    )
                except RuntimeError:
                    logger.exception(
                        'Failed to import "%s" generated from "%s"'
                        " using glTF 2.0 Add-on without animations key",
                        indexed_vrm_filepath,
                        self.parse_result.filepath,
                    )
                    self.cleanup_gltf2_with_indices()
                    raise
        # Save the selection state of objects immediately after glTF import
        self.imported_object_names = [
            selected_object.name for selected_object in self.context.selected_objects
        ]

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

                vrm0_humanoid = get_armature_extension(data).vrm0.humanoid
                vrm1_humanoid = get_armature_extension(data).vrm1.humanoid
                if self.parse_result.spec_version_number < (1, 0):
                    vrm0_humanoid.initial_automatic_bone_assignment = False
                else:
                    vrm1_humanoid.human_bones.initial_automatic_bone_assignment = False
                vrm0_humanoid.pose = vrm0_humanoid.POSE_CURRENT_POSE.identifier
                vrm1_humanoid.pose = vrm1_humanoid.POSE_CURRENT_POSE.identifier
                self.armature = obj

        if (
            (armature := self.armature) is not None
            and isinstance(armature.data, Armature)
            and self.parse_result.spec_version_number < (1, 0)
        ):
            bone_name_to_roll: dict[str, float] = {}
            with save_workspace(self.context, armature, mode="EDIT"):
                for edit_bone in armature.data.edit_bones:
                    bone_name_to_roll[edit_bone.name] = edit_bone.roll

            with save_workspace(self.context, armature):
                armature_rotation = get_rotation_as_quaternion(armature)
                armature_rotation.rotate(Euler((0.0, 0.0, math.pi), "XYZ"))
                set_rotation_without_mode_change(armature, armature_rotation)

                bpy.ops.object.select_all(action="DESELECT")
                armature.select_set(True)
                bpy.ops.object.transform_apply(
                    location=False, rotation=True, scale=False, properties=False
                )

            with self.save_bone_child_object_transforms(self.context, armature):
                edit_bones = [
                    edit_bone
                    for edit_bone in armature.data.edit_bones
                    if not edit_bone.parent
                ]
                while edit_bones:
                    edit_bone = edit_bones.pop(0)
                    roll = bone_name_to_roll.get(edit_bone.name)
                    if roll is not None:
                        edit_bone.roll = roll
                    edit_bones.extend(edit_bone.children)

        extras_material_index_key = self.import_id + "Materials"
        for material in self.context.blend_data.materials:
            if self.is_temp_object_name(material.name):
                continue
            material_index = material.pop(extras_material_index_key, None)
            if isinstance(material_index, int):
                self.materials[material_index] = material

        extras_mesh_index_key = self.import_id + "Meshes"
        for obj in self.context.blend_data.objects:
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

            # In Blender 3.6, custom properties of materials referenced from
            # evaluated meshes may remain as cache forever if not deleted
            restore_modifiers_names: list[str] = []
            for modifier in obj.modifiers:
                if modifier.show_viewport:
                    modifier.show_viewport = False
                    restore_modifiers_names.append(modifier.name)
            depsgraph = self.context.evaluated_depsgraph_get()
            evaluated_mesh_owner = obj.evaluated_get(depsgraph)
            evaluated_mesh = evaluated_mesh_owner.to_mesh(
                preserve_all_data_layers=True, depsgraph=depsgraph
            )
            for evaluated_material in evaluated_mesh.materials:
                if evaluated_material:
                    evaluated_material.pop(extras_material_index_key, None)
            for modifier in obj.modifiers:
                if modifier.name in restore_modifiers_names:
                    modifier.show_viewport = True

            # If not updated here, Custom Property may revive during export
            data.update()

        for image in list(self.context.blend_data.images):
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
                # image.name may be automatically shortened during import, so
                # restore it from the json value
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

        for scene in list(self.context.blend_data.scenes):
            if not self.is_temp_object_name(scene.name):
                continue
            if bpy.app.version >= (3, 2):
                scene.use_extra_user = False
            if scene.users:
                logger.warning(
                    'Failed to remove "%s" with %d users while removing temp scenes',
                    scene.name,
                    scene.users,
                )
            else:
                self.context.blend_data.scenes.remove(scene)

        for collection in [
            *[scene.collection for scene in self.context.blend_data.scenes],
            *self.context.blend_data.collections,
        ]:
            for obj in list(collection.objects):
                if self.is_temp_object_name(obj.name):
                    collection.objects.unlink(obj)

        for obj in list(self.context.blend_data.objects):
            if not self.is_temp_object_name(obj.name):
                continue
            if obj.users:
                logger.warning(
                    'Failed to remove "%s" with %d users while removing temp objects',
                    obj.name,
                    obj.users,
                )
            else:
                self.context.blend_data.objects.remove(obj)

        for mesh in list(self.context.blend_data.meshes):
            if not self.is_temp_object_name(mesh.name):
                continue
            if mesh.users:
                logger.warning(
                    'Failed to remove "%s" with %d users while removing temp meshes',
                    mesh.name,
                    mesh.users,
                )
            else:
                self.context.blend_data.meshes.remove(mesh)

        for material in list(self.context.blend_data.materials):
            if not self.is_temp_object_name(material.name):
                continue
            if material.users:
                logger.warning(
                    'Failed to remove "%s" with %d users while removing temp materials',
                    material.name,
                    material.users,
                )
            else:
                self.context.blend_data.materials.remove(material)

        if self.armature is None:
            logger.warning("Failed to read VRM Humanoid")

    def cleanup_gltf2_with_indices(self) -> None:
        with save_workspace(self.context):
            meshes_key = self.import_id + "Meshes"
            nodes_key = self.import_id + "Nodes"
            remove_objs: list[Object] = []
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
                for obj in self.context.blend_data.objects:
                    if obj in remove_objs and not obj.users:
                        retry = True
                        self.context.blend_data.objects.remove(obj, do_unlink=True)

    def temp_object_name(self) -> str:
        self.temp_object_name_count += 1
        return f"{self.import_id}Temp_{self.temp_object_name_count}_"

    def is_temp_object_name(self, name: str) -> bool:
        return name.startswith(f"{self.import_id}Temp_")

    def setup_viewport(self) -> None:
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
                    'scene.view_settings.view_transform doesn\'t support "Standard".'
                )

        if self.preferences.set_shading_type_to_material_on_import:
            screen = self.context.screen
            for area in screen.areas:
                for space in area.spaces:
                    if space.type == "VIEW_3D" and isinstance(space, SpaceView3D):
                        space.shading.type = "MATERIAL"

    def save_t_pose_action(self) -> None:
        if self.armature is None:
            return

        t_pose_action = self.context.blend_data.actions.new(name="T-Pose")
        t_pose_action.use_fake_user = True
        animation_data_created = False
        if not self.armature.animation_data:
            self.armature.animation_data_create()
            animation_data_created = True
        if not self.armature.animation_data:
            message = "armature.animation_data is None"
            raise ValueError(message)
        original_action = self.armature.animation_data.action
        self.armature.animation_data.action = t_pose_action

        for bone in self.armature.pose.bones:
            for data_path in [
                "location",
                "rotation_quaternion",
                "rotation_axis_angle",
                "rotation_euler",
                "scale",
            ]:
                bone.keyframe_insert(data_path=data_path, frame=1)

        ext = get_armature_extension(self.armature_data)
        ext.vrm0.humanoid.pose = ext.vrm0.humanoid.POSE_CUSTOM_POSE.identifier
        ext.vrm1.humanoid.pose = ext.vrm1.humanoid.POSE_CUSTOM_POSE.identifier
        ext.vrm0.humanoid.pose_library = t_pose_action
        ext.vrm1.humanoid.pose_library = t_pose_action
        if animation_data_created:
            self.armature.animation_data_clear()
        else:
            self.armature.animation_data.action = original_action

    def setup_object_selection_and_activation(self) -> None:
        active_object = self.context.view_layer.objects.active
        if active_object and active_object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        if self.imported_object_names is not None:
            bpy.ops.object.select_all(action="DESELECT")
            for obj in self.context.selectable_objects:
                if obj.name in self.imported_object_names:
                    obj.select_set(True)
        if self.armature is not None:
            self.context.view_layer.objects.active = self.armature


def parse_vrm_json(filepath: Path, *, license_validation: bool) -> ParseResult:
    json_dict, _ = parse_glb(filepath.read_bytes())

    extensions_dict = json_dict.get("extensions")
    if isinstance(extensions_dict, dict):
        vrm1_extension_dict = extensions_dict.get("VRMC_vrm")
        vrm0_extension_dict = extensions_dict.get("VRM")
    else:
        vrm1_extension_dict = None
        vrm0_extension_dict = None

    if isinstance(vrm1_extension_dict, dict):
        (
            spec_version_number,
            spec_version_str,
            spec_version_is_stable,
            hips_node_index,
        ) = read_vrm1_extension(vrm1_extension_dict)
        vrm0_extension_dict = {}
    elif isinstance(vrm0_extension_dict, dict):
        (
            spec_version_number,
            spec_version_str,
            spec_version_is_stable,
            hips_node_index,
        ) = read_vrm0_extension(vrm0_extension_dict)
        vrm1_extension_dict = {}
    else:
        spec_version_number = (0, 0)
        spec_version_str = "0.0"
        spec_version_is_stable = True
        hips_node_index = None
        vrm0_extension_dict = {}
        vrm1_extension_dict = {}

    if license_validation:
        validate_license(json_dict, spec_version_number)

    return ParseResult(
        filepath=filepath,
        json_dict=json_dict,
        spec_version_number=spec_version_number,
        spec_version_str=spec_version_str,
        spec_version_is_stable=spec_version_is_stable,
        vrm0_extension_dict=vrm0_extension_dict,
        vrm1_extension_dict=vrm1_extension_dict,
        hips_node_index=hips_node_index,
    )


def read_vrm0_extension(
    vrm0_dict: dict[str, Json],
) -> tuple[tuple[int, int], str, bool, Optional[int]]:
    spec_version_number = (0, 0)
    spec_version_str = "0.0"
    spec_version_is_stable = True
    hips_node_index = None

    spec_version = vrm0_dict.get("specVersion")
    if isinstance(spec_version, str):
        spec_version_str = spec_version

    humanoid_dict = vrm0_dict.get("humanoid")
    if isinstance(humanoid_dict, dict):
        human_bone_dicts = humanoid_dict.get("humanBones")
        if isinstance(human_bone_dicts, list):
            for human_bone_dict in human_bone_dicts:
                if not isinstance(human_bone_dict, dict):
                    continue
                if human_bone_dict.get("bone") != "hips":
                    continue
                node_index = human_bone_dict.get("node")
                if isinstance(node_index, int):
                    hips_node_index = node_index

    return (
        spec_version_number,
        spec_version_str,
        spec_version_is_stable,
        hips_node_index,
    )


def read_vrm1_extension(
    vrm1_dict: dict[str, Json],
) -> tuple[tuple[int, int], str, bool, Optional[int]]:
    spec_version_number = (1, 0)
    spec_version_str = "1.0"
    spec_version_is_stable = True
    hips_node_index = None

    humanoid_dict = vrm1_dict.get("humanoid")
    if isinstance(humanoid_dict, dict):
        human_bones_dict = humanoid_dict.get("humanBones")
        if isinstance(human_bones_dict, dict):
            hips_dict = human_bones_dict.get("hips")
            if isinstance(hips_dict, dict):
                node_index = hips_dict.get("node")
                if isinstance(node_index, int):
                    hips_node_index = node_index

    return (
        spec_version_number,
        spec_version_str,
        spec_version_is_stable,
        hips_node_index,
    )
