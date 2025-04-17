
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
    @contextlib.contextmanager
    def save_bone_child_object_transforms(
        context: Context, armature: Object
    ) -> Iterator[Armature]:
        if not isinstance(armature.data, Armature):
            message = f"{type(armature.data)} is not an Armature"
            raise TypeError(message)

        context.view_layer.update()
        bone_child_object_world_matrices: dict[str, Matrix] = {}
        for obj in context.blend_data.objects:
            if (
                obj.parent_type == "BONE"
                and obj.parent == armature
                and obj.parent_bone in armature.data.bones
            ):
                bone_child_object_world_matrices[obj.name] = obj.matrix_world.copy()

        try:
            with save_workspace(context, armature, mode="EDIT"):
                yield armature.data
        finally:
            context.view_layer.update()
            for name, matrix_world in bone_child_object_world_matrices.items():
                restore_obj = context.blend_data.objects.get(name)
                if (
                    restore_obj
                    and restore_obj.parent_type == "BONE"
                    and restore_obj.parent == armature
                    and restore_obj.parent_bone in armature.data.bones
                ):
                    restore_obj.matrix_world = matrix_world.copy()
            context.view_layer.update()

    def use_fake_user_for_thumbnail(self) -> None:
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
