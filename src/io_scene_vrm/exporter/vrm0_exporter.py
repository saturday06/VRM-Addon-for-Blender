# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
# SPDX-FileCopyrightText: 2018 iCyP

import importlib
import itertools
import re
import statistics
import struct
from collections.abc import Iterator, Mapping, MutableSequence, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from os import environ
from sys import float_info
from typing import Final, Optional, Union

import bpy
from bpy.types import (
    Armature,
    Context,
    Curve,
    Image,
    Key,
    Material,
    Mesh,
    MeshUVLoopLayer,
    Node,
    Object,
    PoseBone,
    ShaderNodeGroup,
    ShaderNodeTexImage,
    ShapeKey,
)
from mathutils import Matrix, Vector

from ..common import convert, gltf, shader
from ..common.convert import Json
from ..common.deep import make_json
from ..common.gl import (
    GL_FLOAT,
    GL_LINEAR,
    GL_REPEAT,
    GL_UNSIGNED_INT,
    GL_UNSIGNED_SHORT,
)
from ..common.gltf import (
    FLOAT_NEGATIVE_MAX,
    FLOAT_POSITIVE_MAX,
)
from ..common.legacy_gltf import TEXTURE_INPUT_NAMES
from ..common.logging import get_logger
from ..common.mtoon_unversioned import MtoonUnversioned
from ..common.progress import Progress, create_progress
from ..common.version import get_addon_version
from ..common.vrm0.human_bone import HumanBoneSpecifications
from ..common.workspace import save_workspace
from ..editor import search
from ..editor.extension import get_armature_extension, get_material_extension
from ..editor.mtoon1.property_group import (
    Mtoon0TexturePropertyGroup,
    Mtoon1KhrTextureTransformPropertyGroup,
    Mtoon1SamplerPropertyGroup,
    Mtoon1TextureInfoPropertyGroup,
    Mtoon1TexturePropertyGroup,
)
from ..editor.search import MESH_CONVERTIBLE_OBJECT_TYPES
from ..editor.t_pose import setup_humanoid_t_pose
from ..editor.vrm0.property_group import Vrm0BlendShapeGroupPropertyGroup
from ..external.io_scene_gltf2_support import (
    image_to_image_bytes,
    init_extras_export,
)
from .abstract_base_vrm_exporter import (
    AbstractBaseVrmExporter,
    assign_dict,
    force_apply_modifiers,
)

logger = get_logger(__name__)


class Vrm0Exporter(AbstractBaseVrmExporter):
    @dataclass(frozen=True)
    class Gltf2IoTextureImage:
        name: str
        mime_type: str
        image_bytes: bytes
        export_image_index: int

    @dataclass
    class PrimitiveTarget:
        name: str

        position: bytearray = field(default_factory=bytearray)
        position_max_x = FLOAT_NEGATIVE_MAX
        position_min_x = FLOAT_POSITIVE_MAX
        position_max_y = FLOAT_NEGATIVE_MAX
        position_min_y = FLOAT_POSITIVE_MAX
        position_max_z = FLOAT_NEGATIVE_MAX
        position_min_z = FLOAT_POSITIVE_MAX

        normal: bytearray = field(default_factory=bytearray)

    class VertexAttributeAndTargets:
        POSITION_STRUCT: Final = struct.Struct("<fff")
        NORMAL_STRUCT: Final = struct.Struct("<fff")
        TEXCOORD_STRUCT: Final = struct.Struct("<ff")
        WEIGHTS_STRUCT: Final = struct.Struct("<ffff")
        JOINTS_STRUCT: Final = struct.Struct("<HHHH")

        IndexSearchKey = tuple[
            int, tuple[float, float, float], Optional[tuple[float, float]]
        ]

        def __init__(self, target_names: Sequence[str]) -> None:
            self.targets = [
                Vrm0Exporter.PrimitiveTarget(name=target_name)
                for target_name in target_names
            ]

            self.count = 0

            self.position = bytearray()
            self.position_max_x = FLOAT_NEGATIVE_MAX
            self.position_min_x = FLOAT_POSITIVE_MAX
            self.position_max_y = FLOAT_NEGATIVE_MAX
            self.position_min_y = FLOAT_POSITIVE_MAX
            self.position_max_z = FLOAT_NEGATIVE_MAX
            self.position_min_z = FLOAT_POSITIVE_MAX

            self.normal = bytearray()
            self.texcoord = bytearray()
            self.weights = bytearray()
            self.joints = bytearray()

            self.index_search_dict: dict[
                tuple[int, tuple[float, float, float], Optional[tuple[float, float]]],
                int,
            ] = {}

        @staticmethod
        def create_index_search_key(
            *,
            blender_vertex_index: int,
            normal: tuple[float, float, float],
            texcoord: Optional[tuple[float, float]],
        ) -> IndexSearchKey:
            return (
                # TODO: 旧エクスポーターと互換性のある形式
                blender_vertex_index,
                normal,
                texcoord,
            )

        def find_added_vertex_index(
            self,
            blender_vertex_index: int,
            normal: tuple[float, float, float],
            texcoord: Optional[tuple[float, float]],
        ) -> Optional[int]:
            index_search_key = self.create_index_search_key(
                blender_vertex_index=blender_vertex_index,
                normal=normal,
                texcoord=texcoord,
            )
            return self.index_search_dict.get(index_search_key)

        def add_vertex(
            self,
            *,
            blender_vertex_index: int,
            position: tuple[float, float, float],
            normal: tuple[float, float, float],
            texcoord: Optional[tuple[float, float]],
            weights: Optional[tuple[float, float, float, float]],
            joints: Optional[tuple[int, int, int, int]],
            targets_position: Sequence[tuple[float, float, float]],
            targets_normal: Sequence[tuple[float, float, float]],
        ) -> int:
            index = self.count
            self.count += 1

            index_search_key = self.create_index_search_key(
                blender_vertex_index=blender_vertex_index,
                normal=normal,
                texcoord=texcoord,
            )
            self.index_search_dict[index_search_key] = index

            self.position.extend(self.POSITION_STRUCT.pack(*position))
            position_x, position_y, position_z = position
            self.position_max_x = max(self.position_max_x, position_x)
            self.position_min_x = min(self.position_min_x, position_x)
            self.position_max_y = max(self.position_max_y, position_y)
            self.position_min_y = min(self.position_min_y, position_y)
            self.position_max_z = max(self.position_max_z, position_z)
            self.position_min_z = min(self.position_min_z, position_z)

            self.normal.extend(self.NORMAL_STRUCT.pack(*normal))
            if texcoord is not None:
                self.texcoord.extend(self.TEXCOORD_STRUCT.pack(*texcoord))
            if weights is not None:
                self.weights.extend(self.WEIGHTS_STRUCT.pack(*weights))
            if joints is not None:
                self.joints.extend(self.JOINTS_STRUCT.pack(*joints))

            for i, target in enumerate(self.targets):
                target_position_x, target_position_y, target_position_z = (
                    targets_position[i]
                )
                target.position.extend(
                    self.POSITION_STRUCT.pack(
                        target_position_x, target_position_y, target_position_z
                    )
                )
                target.position_max_x = max(target.position_max_x, target_position_x)
                target.position_min_x = min(target.position_min_x, target_position_x)
                target.position_max_y = max(target.position_max_y, target_position_y)
                target.position_min_y = min(target.position_min_y, target_position_y)
                target.position_max_z = max(target.position_max_z, target_position_z)
                target.position_min_z = min(target.position_min_z, target_position_z)

                target.normal.extend(self.NORMAL_STRUCT.pack(*targets_normal[i]))

            return index

    def export_vrm(self) -> Optional[bytes]:
        init_extras_export()

        with (
            save_workspace(self.context),
            self.clear_blend_shape_proxy_previews(self.armature_data),
            setup_humanoid_t_pose(self.context, self.armature),
            self.hide_mtoon1_outline_geometry_nodes(self.context),
            create_progress(self.context) as progress,
        ):
            json_dict: dict[str, Json] = {}
            buffer0 = bytearray()
            self.write_glb_structure(progress, json_dict, buffer0)
            return gltf.pack_glb(json_dict, buffer0)

    def write_glb_structure(
        self, progress: Progress, json_dict: dict[str, Json], buffer0: bytearray
    ) -> None:
        json_dict["asset"] = {"generator": self.get_asset_generator(), "version": "2.0"}

        scene_dicts: list[dict[str, Json]] = []
        node_dicts: list[dict[str, Json]] = []
        mesh_dicts: list[dict[str, Json]] = []
        skin_dicts: list[dict[str, Json]] = []
        material_dicts: list[dict[str, Json]] = []
        texture_dicts: list[dict[str, Json]] = []
        sampler_dicts: list[dict[str, Json]] = []
        image_dicts: list[dict[str, Json]] = []
        accessor_dicts: list[dict[str, Json]] = []
        buffer_view_dicts: list[dict[str, Json]] = []
        extensions_vrm_material_property_dicts: list[Json] = []
        extensions_vrm_dict: dict[str, Json] = {
            "materialProperties": extensions_vrm_material_property_dicts,
        }
        extensions_used: list[str] = []
        material_name_to_material_index: dict[str, int] = {}
        image_name_to_image_index: dict[str, int] = {}

        self.write_materials(
            progress,
            material_dicts,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            extensions_vrm_material_property_dicts,
            extensions_used,
            buffer0,
            material_name_to_material_index,
            image_name_to_image_index,
        )

        bone_name_to_node_index: dict[str, int] = {}
        mesh_object_name_to_mesh_index: dict[str, int] = {}
        self.write_scene(
            progress,
            scene_dicts,
            node_dicts,
            mesh_dicts,
            skin_dicts,
            material_dicts,
            accessor_dicts,
            buffer_view_dicts,
            extensions_vrm_material_property_dicts,
            buffer0,
            bone_name_to_node_index,
            mesh_object_name_to_mesh_index,
            material_name_to_material_index,
        )
        self.write_extensions_vrm(
            progress,
            mesh_dicts,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            extensions_vrm_dict,
            extensions_used,
            buffer0,
            image_name_to_image_index,
            bone_name_to_node_index,
            mesh_object_name_to_mesh_index,
        )

        if scene_dicts:
            json_dict["scenes"] = make_json(scene_dicts)
            json_dict["scene"] = 0
        if node_dicts:
            json_dict["nodes"] = make_json(node_dicts)
        if mesh_dicts:
            json_dict["meshes"] = make_json(mesh_dicts)
        if material_dicts:
            json_dict["materials"] = make_json(material_dicts)
        if skin_dicts:
            json_dict["skins"] = make_json(skin_dicts)
        if accessor_dicts:
            json_dict["accessors"] = make_json(accessor_dicts)
        if texture_dicts:
            json_dict["textures"] = make_json(texture_dicts)
        if image_dicts:
            json_dict["images"] = make_json(image_dicts)
        if sampler_dicts:
            json_dict["samplers"] = make_json(sampler_dicts)
        if buffer_view_dicts:
            json_dict["bufferViews"] = make_json(buffer_view_dicts)
        if extensions_used:
            json_dict["extensionsUsed"] = list(dict.fromkeys(extensions_used).keys())
        json_dict["extensions"] = make_json({"VRM": extensions_vrm_dict})
        json_dict["buffers"] = [
            {
                "byteLength": len(buffer0),
            }
        ]

    def write_extensions_vrm(
        self,
        progress: Progress,
        mesh_dicts: list[dict[str, Json]],
        texture_dicts: list[dict[str, Json]],
        sampler_dicts: list[dict[str, Json]],
        image_dicts: list[dict[str, Json]],
        buffer_view_dicts: list[dict[str, Json]],
        vrm_dict: dict[str, Json],
        extensions_used: list[str],
        buffer0: bytearray,
        image_name_to_image_index: dict[str, int],
        bone_name_to_node_index: Mapping[str, int],
        mesh_object_name_to_mesh_index: Mapping[str, int],
    ) -> None:
        vrm_dict["specVersion"] = "0.0"
        vrm_dict["exporterVersion"] = self.get_asset_generator()

        self.write_extensions_vrm_first_person(
            progress, vrm_dict, bone_name_to_node_index, mesh_object_name_to_mesh_index
        )
        self.write_extensions_vrm_meta(
            progress,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            vrm_dict,
            buffer0,
            image_name_to_image_index,
        )
        self.write_extensions_vrm_blend_shape_master(
            progress, mesh_dicts, mesh_object_name_to_mesh_index, vrm_dict
        )
        self.write_extensions_vrm_secondary_animation(
            progress, vrm_dict, bone_name_to_node_index
        )
        self.write_extensions_vrm_humanoid(progress, vrm_dict, bone_name_to_node_index)
        extensions_used.append("VRM")

    def write_extensions_vrm_humanoid(
        self,
        _progress: Progress,
        vrm_dict: dict[str, Json],
        bone_name_to_node_index: Mapping[str, int],
    ) -> None:
        human_bone_dicts: list[Json] = []
        humanoid_dict: dict[str, Json] = {"humanBones": human_bone_dicts}
        vrm_dict["humanoid"] = humanoid_dict
        humanoid = get_armature_extension(self.armature_data).vrm0.humanoid
        for human_bone_name in HumanBoneSpecifications.all_names:
            for human_bone in humanoid.human_bones:
                if not (
                    human_bone.bone == human_bone_name
                    and (
                        node_index := bone_name_to_node_index.get(
                            human_bone.node.bone_name
                        )
                    )
                    is not None
                ):
                    continue
                human_bone_dict: dict[str, Json] = {
                    "bone": human_bone_name,
                    "node": node_index,
                    "useDefaultValues": human_bone.use_default_values,
                }
                human_bone_dicts.append(human_bone_dict)
                if not human_bone.use_default_values:
                    human_bone_dict.update(
                        {
                            "min": {
                                "x": human_bone.min[0],
                                "y": human_bone.min[1],
                                "z": human_bone.min[2],
                            },
                            "max": {
                                "x": human_bone.max[0],
                                "y": human_bone.max[1],
                                "z": human_bone.max[2],
                            },
                            "center": {
                                "x": human_bone.center[0],
                                "y": human_bone.center[1],
                                "z": human_bone.center[2],
                            },
                            "axisLength": human_bone.axis_length,
                        }
                    )
                break
        humanoid_dict["armStretch"] = humanoid.arm_stretch
        humanoid_dict["legStretch"] = humanoid.leg_stretch
        humanoid_dict["upperArmTwist"] = humanoid.upper_arm_twist
        humanoid_dict["lowerArmTwist"] = humanoid.lower_arm_twist
        humanoid_dict["upperLegTwist"] = humanoid.upper_leg_twist
        humanoid_dict["lowerLegTwist"] = humanoid.lower_leg_twist
        humanoid_dict["feetSpacing"] = humanoid.feet_spacing
        humanoid_dict["hasTranslationDoF"] = humanoid.has_translation_dof

    def write_extensions_vrm_blend_shape_master(
        self,
        _progress: Progress,
        mesh_dicts: list[dict[str, Json]],
        mesh_object_name_to_mesh_index: Mapping[str, int],
        vrm_dict: dict[str, Json],
    ) -> None:
        blend_shape_master = get_armature_extension(
            self.armature_data
        ).vrm0.blend_shape_master
        first_person = get_armature_extension(self.armature_data).vrm0.first_person
        blend_shape_group_dicts: list[Json] = []
        blend_shape_master_dict: dict[str, Json] = {
            "blendShapeGroups": blend_shape_group_dicts
        }
        vrm_dict["blendShapeMaster"] = blend_shape_master_dict

        remaining_preset_names = [
            preset_name.identifier
            for preset_name in Vrm0BlendShapeGroupPropertyGroup.preset_name_enum
            if preset_name != Vrm0BlendShapeGroupPropertyGroup.PRESET_NAME_UNKNOWN
        ]

        for blend_shape_group in blend_shape_master.blend_shape_groups:
            blend_shape_group_dict: dict[str, Json] = {}

            if not blend_shape_group.name:
                continue
            blend_shape_group_dict["name"] = blend_shape_group.name

            if not blend_shape_group.preset_name:
                continue

            if blend_shape_group.preset_name != "unknown":
                if blend_shape_group.preset_name not in remaining_preset_names:
                    continue
                remaining_preset_names.remove(blend_shape_group.preset_name)

            blend_shape_group_dict["presetName"] = blend_shape_group.preset_name

            bind_dicts: list[Json] = []
            blend_shape_group_dict["binds"] = bind_dicts
            for bind in blend_shape_group.binds:
                bind_dict: dict[str, Json] = {}
                mesh_index = mesh_object_name_to_mesh_index.get(
                    bind.mesh.mesh_object_name
                )
                if mesh_index is None:
                    # logger.warning("%s => None", bind.mesh.mesh_object_name)
                    continue
                bind_dict["mesh"] = mesh_index

                if not (
                    0 <= mesh_index < len(mesh_dicts)
                    and (mesh_dict := mesh_dicts[mesh_index])
                    and isinstance(
                        mesh_primitive_dicts := mesh_dict.get("primitives"), list
                    )
                    and mesh_primitive_dicts
                    and isinstance(mesh_primitive_dict := mesh_primitive_dicts[0], dict)
                    and isinstance(
                        mesh_primitive_extras_dict := mesh_primitive_dict.get("extras"),
                        dict,
                    )
                    and isinstance(
                        target_names := mesh_primitive_extras_dict.get("targetNames"),
                        list,
                    )
                ):
                    continue

                if bind.index not in target_names:
                    continue

                bind_dict["index"] = target_names.index(bind.index)
                bind_dict["weight"] = min(max(bind.weight * 100, 0), 100)

                bind_dicts.append(bind_dict)

            material_value_dicts: list[Json] = []
            blend_shape_group_dict["materialValues"] = material_value_dicts
            for material_value in blend_shape_group.material_values:
                if not material_value.material or not material_value.material.name:
                    continue

                material_value_dicts.append(
                    {
                        "materialName": material_value.material.name,
                        "propertyName": material_value.property_name,
                        "targetValue": [v.value for v in material_value.target_value],
                    }
                )

            blend_shape_group_dict["isBinary"] = blend_shape_group.is_binary
            blend_shape_group_dicts.append(blend_shape_group_dict)

        # VirtualMotionCapture requires some blend shape presets
        # https://twitter.com/sh_akira/status/1674237253231714305
        # Note: the VRM specification does not require them. UniVRM 0.112.0
        # can be configured not to output them.
        for preset_name in remaining_preset_names:
            if first_person.look_at_type_name == "Bone" and preset_name.startswith(
                "look"
            ):
                continue
            name = next(
                (
                    enum.name.replace(" ", "")
                    for enum in Vrm0BlendShapeGroupPropertyGroup.preset_name_enum
                    if enum.identifier == preset_name
                ),
                preset_name.capitalize(),
            )
            blend_shape_group_dicts.append(
                {
                    "name": name,
                    "presetName": preset_name,
                    "binds": [],
                    "materialValues": [],
                    "isBinary": False,
                }
            )

    def write_extensions_vrm_secondary_animation(
        self,
        _progress: Progress,
        vrm_dict: dict[str, Json],
        bone_name_to_node_index: Mapping[str, int],
    ) -> None:
        secondary_animation = get_armature_extension(
            self.armature_data
        ).vrm0.secondary_animation
        secondary_animation_dict: dict[str, Json] = {}
        vrm_dict["secondaryAnimation"] = secondary_animation_dict

        collider_group_dicts: list[Json] = []
        secondary_animation_dict["colliderGroups"] = collider_group_dicts
        secondary_animation = get_armature_extension(
            self.armature_data
        ).vrm0.secondary_animation

        collider_group_name_to_index: dict[str, int] = {}

        for collider_group in secondary_animation.collider_groups:
            node_index = bone_name_to_node_index.get(collider_group.node.bone_name)
            if node_index is None:
                continue

            collider_group_dict: dict[str, Json] = {}
            collider_dicts: list[Json] = []
            collider_group_dict["colliders"] = collider_dicts

            collider_group_name_to_index[collider_group.name] = len(
                collider_group_dicts
            )
            collider_group_dicts.append(collider_group_dict)

            collider_group_dict["node"] = node_index

            for collider in collider_group.colliders:
                collider_object = collider.bpy_object
                if (
                    not collider_object
                    or collider_object.parent_bone not in self.armature.pose.bones
                ):
                    continue

                collider_dict: dict[str, Json] = {}
                offset = [
                    collider_object.matrix_world.to_translation()[i]
                    - (
                        self.armature.matrix_world
                        @ Matrix.Translation(
                            self.armature.pose.bones[collider_object.parent_bone].head
                        )
                    ).to_translation()[i]
                    for i in range(3)
                ]

                object_mean_scale = statistics.mean(
                    abs(s) for s in collider_object.matrix_world.to_scale()
                )
                collider_dict["radius"] = (
                    collider_object.empty_display_size * object_mean_scale
                )

                collider_dict["offset"] = {
                    # https://github.com/vrm-c/UniVRM/issues/65
                    "x": -offset[0],
                    "y": offset[2],
                    "z": -offset[1],
                }
                collider_dicts.append(collider_dict)

        bone_group_dicts: list[Json] = []
        secondary_animation_dict["boneGroups"] = bone_group_dicts
        for bone_group in secondary_animation.bone_groups:
            bone_group_dict: dict[str, Json] = {
                "comment": bone_group.comment,
                "stiffiness": bone_group.stiffiness,
                "gravityPower": bone_group.gravity_power,
                "gravityDir": {
                    # TODO: firstPerson.firstPersonBoneOffsetとBoneGroup.gravityDirの
                    # 軸変換はオリジナルになっている。これについてコメントを記載する。
                    "x": bone_group.gravity_dir[0],
                    "y": bone_group.gravity_dir[2],
                    "z": bone_group.gravity_dir[1],
                },
                "dragForce": bone_group.drag_force,
                "center": bone_name_to_node_index.get(bone_group.center.bone_name, -1),
                "hitRadius": bone_group.hit_radius,
                "bones": [
                    node_index
                    for bone in bone_group.bones
                    if (node_index := bone_name_to_node_index.get(bone.bone_name))
                    is not None
                ],
            }
            collider_group_indices: list[Json] = []
            for collider_group_name in bone_group.collider_groups:
                collider_group_index = collider_group_name_to_index.get(
                    collider_group_name.value
                )
                if collider_group_index is None:
                    continue
                collider_group_indices.append(collider_group_index)

            bone_group_dict["colliderGroups"] = collider_group_indices
            bone_group_dicts.append(bone_group_dict)

    def write_extensions_vrm_meta(
        self,
        _progress: Progress,
        texture_dicts: list[dict[str, Json]],
        sampler_dicts: list[dict[str, Json]],
        image_dicts: list[dict[str, Json]],
        buffer_view_dicts: list[dict[str, Json]],
        vrm_dict: dict[str, Json],
        buffer0: bytearray,
        image_name_to_index_dict: dict[str, int],
    ) -> None:
        meta = get_armature_extension(self.armature_data).vrm0.meta
        meta_dict: dict[str, Json] = {
            "title": meta.title,
            "version": meta.version,
            "author": meta.author,
            "contactInformation": meta.contact_information,
            "reference": meta.reference,
            "allowedUserName": meta.allowed_user_name,
            "violentUssageName": meta.violent_ussage_name,
            "sexualUssageName": meta.sexual_ussage_name,
            "commercialUssageName": meta.commercial_ussage_name,
            "otherPermissionUrl": meta.other_permission_url,
            "licenseName": meta.license_name,
            "otherLicenseUrl": meta.other_license_url,
        }

        if meta.texture:
            image_index = self.find_or_create_image(
                image_dicts,
                buffer_view_dicts,
                buffer0,
                image_name_to_index_dict,
                meta.texture,
            )
            sampler_dict: dict[str, Json] = {
                "magFilter": GL_LINEAR,
                "minFilter": GL_LINEAR,
                "wrapS": GL_REPEAT,
                "wrapT": GL_REPEAT,
            }
            if sampler_dict in sampler_dicts:
                sampler_index = sampler_dicts.index(sampler_dict)
            else:
                sampler_index = len(sampler_dicts)
                sampler_dicts.append(sampler_dict)
            texture_index = len(texture_dicts)
            texture_dicts.append(
                {
                    "sampler": sampler_index,
                    "source": image_index,
                },
            )
            meta_dict["texture"] = texture_index

        vrm_dict["meta"] = meta_dict

    def write_extensions_vrm_first_person(
        self,
        _progress: Progress,
        vrm_dict: dict[str, Json],
        bone_name_to_node_index: Mapping[str, int],
        mesh_object_name_to_mesh_index: Mapping[str, int],
    ) -> None:
        first_person_dict: dict[str, Json] = {}
        vrm_dict["firstPerson"] = first_person_dict

        first_person = get_armature_extension(self.armature_data).vrm0.first_person

        if first_person.first_person_bone.bone_name:
            first_person_bone_name: Optional[str] = (
                first_person.first_person_bone.bone_name
            )
        else:
            first_person_bone_name = next(
                human_bone.node.bone_name
                for human_bone in (
                    get_armature_extension(self.armature_data).vrm0.humanoid.human_bones
                )
                if human_bone.bone == "head"
            )

        if first_person_bone_name:
            first_person_bone_index = bone_name_to_node_index.get(
                first_person_bone_name
            )
            if isinstance(first_person_bone_index, int):
                first_person_dict["firstPersonBone"] = first_person_bone_index

        first_person_dict["firstPersonBoneOffset"] = {
            # TODO: firstPerson.firstPersonBoneOffsetとBoneGroup.gravityDirの
            # 軸変換はオリジナルになっている。これについてコメントを記載する。
            "x": first_person.first_person_bone_offset[0],
            "y": first_person.first_person_bone_offset[2],
            "z": first_person.first_person_bone_offset[1],
        }

        mesh_annotation_dicts: list[Json] = []
        first_person_dict["meshAnnotations"] = mesh_annotation_dicts
        for mesh_annotation in first_person.mesh_annotations:
            mesh_index = mesh_object_name_to_mesh_index.get(
                mesh_annotation.mesh.mesh_object_name
            )
            if mesh_index is None:
                mesh_index = -1
            mesh_annotation_dicts.append(
                {
                    "mesh": mesh_index,
                    "firstPersonFlag": mesh_annotation.first_person_flag,
                }
            )
        first_person_dict["lookAtTypeName"] = first_person.look_at_type_name
        for look_at, look_at_dict_key in [
            (
                first_person.look_at_horizontal_inner,
                "lookAtHorizontalInner",
            ),
            (
                first_person.look_at_horizontal_outer,
                "lookAtHorizontalOuter",
            ),
            (
                first_person.look_at_vertical_down,
                "lookAtVerticalDown",
            ),
            (
                first_person.look_at_vertical_up,
                "lookAtVerticalUp",
            ),
        ]:
            first_person_dict[look_at_dict_key] = {
                "curve": list(look_at.curve),
                "xRange": look_at.x_range,
                "yRange": look_at.y_range,
            }

    def write_scene(
        self,
        progress: Progress,
        scene_dicts: list[dict[str, Json]],
        node_dicts: list[dict[str, Json]],
        mesh_dicts: list[dict[str, Json]],
        skin_dicts: list[dict[str, Json]],
        material_dicts: list[dict[str, Json]],
        accessor_dicts: list[dict[str, Json]],
        buffer_view_dicts: list[dict[str, Json]],
        extensions_vrm_material_property_dicts: list[Json],
        buffer0: bytearray,
        bone_name_to_node_index: dict[str, int],
        mesh_object_name_to_mesh_index: dict[str, int],
        material_name_to_material_index: Mapping[str, int],
    ) -> None:
        scene0_nodes: list[Json] = []

        armature_root_node_indices, skin_dict, skin_joints = self.write_armature(
            progress,
            node_dicts,
            accessor_dicts,
            buffer_view_dicts,
            buffer0,
            bone_name_to_node_index,
        )
        scene0_nodes.extend(armature_root_node_indices)
        scene0_nodes.extend(
            self.write_mesh_nodes(
                progress,
                node_dicts,
                mesh_dicts,
                skin_dicts,
                material_dicts,
                accessor_dicts,
                buffer_view_dicts,
                extensions_vrm_material_property_dicts,
                buffer0,
                bone_name_to_node_index,
                mesh_object_name_to_mesh_index,
                material_name_to_material_index,
                skin_dict,
                skin_joints,
            )
        )

        scene_dicts.append({"nodes": scene0_nodes})

    def write_mtoon1_downgraded_material(
        self,
        _progress: Progress,
        texture_dicts: list[dict[str, Json]],
        sampler_dicts: list[dict[str, Json]],
        image_dicts: list[dict[str, Json]],
        buffer_view_dicts: list[dict[str, Json]],
        extensions_used: list[str],
        buffer0: bytearray,
        image_name_to_image_index: dict[str, int],
        material: Material,
        material_dict: dict[str, Json],
        vrm_material_property_dict: dict[str, Json],
    ) -> None:
        gltf = get_material_extension(material).mtoon1
        mtoon = gltf.extensions.vrmc_materials_mtoon

        material_dict.update(
            {
                "alphaMode": gltf.alpha_mode,
                "doubleSided": gltf.double_sided,
                "extensions": {"KHR_materials_unlit": {}},
            }
        )

        extensions_used.append("KHR_materials_unlit")
        pbr_metallic_roughness_dict: dict[str, Json] = {
            "metallicFactor": 0,
            "roughnessFactor": 0.9,
        }
        keyword_map: dict[str, bool] = {}
        tag_map: dict[str, str] = {}
        float_properties: dict[str, float] = {}
        vector_properties: dict[str, Sequence[float]] = {}
        texture_properties: dict[str, int] = {}
        pbr_metallic_roughness_dict["baseColorFactor"] = list(
            gltf.pbr_metallic_roughness.base_color_factor
        )
        extensions = gltf.pbr_metallic_roughness.base_color_texture.extensions
        khr_texture_transform = extensions.khr_texture_transform

        vector_properties["_Color"] = convert.linear_to_srgb(
            gltf.pbr_metallic_roughness.base_color_factor
        )

        if assign_dict(
            pbr_metallic_roughness_dict,
            "baseColorTexture",
            self.create_mtoon1_downgraded_texture_info(
                gltf.pbr_metallic_roughness.base_color_texture,
                texture_properties,
                "_MainTex",
                vector_properties,
                texture_dicts,
                sampler_dicts,
                image_dicts,
                buffer_view_dicts,
                buffer0,
                image_name_to_image_index,
                khr_texture_transform,
            ),
        ):
            vector_properties["_MainTex"] = [
                khr_texture_transform.offset[0],
                khr_texture_transform.offset[1],
                khr_texture_transform.scale[0],
                khr_texture_transform.scale[1],
            ]
            extensions_used.append("KHR_texture_transform")

        vector_properties["_ShadeColor"] = convert.linear_to_srgb(
            [*mtoon.shade_color_factor, 1]
        )
        self.create_mtoon1_downgraded_texture(
            mtoon.shade_multiply_texture.index,
            texture_properties,
            "_ShadeTexture",
            vector_properties,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            buffer0,
            image_name_to_image_index,
        )

        float_properties["_BumpScale"] = gltf.normal_texture.scale
        if assign_dict(
            material_dict,
            "normalTexture",
            self.create_mtoon1_downgraded_texture_info(
                gltf.normal_texture,
                texture_properties,
                "_BumpMap",
                vector_properties,
                texture_dicts,
                sampler_dicts,
                image_dicts,
                buffer_view_dicts,
                buffer0,
                image_name_to_image_index,
                khr_texture_transform,
            ),
        ):
            normal_texture_to_index_dict = material_dict.get("normalTexture")
            if isinstance(normal_texture_to_index_dict, dict):
                normal_texture_to_index_dict["scale"] = gltf.normal_texture.scale
            keyword_map["_NORMALMAP"] = True

        self.create_mtoon1_downgraded_texture(
            gltf.mtoon0_shading_grade_texture,
            texture_properties,
            "_ShadingGradeTexture",
            vector_properties,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            buffer0,
            image_name_to_image_index,
        )
        float_properties["_ShadingGradeRate"] = gltf.mtoon0_shading_grade_rate

        float_properties["_ShadeShift"] = convert.mtoon_shading_shift_1_to_0(
            mtoon.shading_toony_factor, mtoon.shading_shift_factor
        )
        float_properties["_ShadeToony"] = convert.mtoon_shading_toony_1_to_0(
            mtoon.shading_toony_factor, mtoon.shading_shift_factor
        )
        float_properties["_IndirectLightIntensity"] = (
            convert.mtoon_gi_equalization_to_intensity(mtoon.gi_equalization_factor)
        )
        float_properties["_RimLightingMix"] = gltf.mtoon0_rim_lighting_mix
        float_properties["_RimFresnelPower"] = mtoon.parametric_rim_fresnel_power_factor
        float_properties["_RimLift"] = mtoon.parametric_rim_lift_factor

        emissive_strength = (
            gltf.extensions.khr_materials_emissive_strength.emissive_strength
        )
        emissive_factor = Vector(gltf.emissive_factor)
        hdr_emissive_factor = (
            Vector(convert.linear_to_srgb(emissive_factor)) * emissive_strength
        )
        vector_properties["_EmissionColor"] = [*hdr_emissive_factor, 1]
        if emissive_factor.length_squared > 0:
            material_dict["emissiveFactor"] = list(emissive_factor)

        assign_dict(
            material_dict,
            "emissiveTexture",
            self.create_mtoon1_downgraded_texture_info(
                gltf.emissive_texture,
                texture_properties,
                "_EmissionMap",
                vector_properties,
                texture_dicts,
                sampler_dicts,
                image_dicts,
                buffer_view_dicts,
                buffer0,
                image_name_to_image_index,
                khr_texture_transform,
            ),
        )
        if pbr_metallic_roughness_dict:
            material_dict["pbrMetallicRoughness"] = pbr_metallic_roughness_dict

        self.create_mtoon1_downgraded_texture(
            mtoon.matcap_texture.index,
            texture_properties,
            "_SphereAdd",
            vector_properties,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            buffer0,
            image_name_to_image_index,
        )

        vector_properties["_RimColor"] = convert.linear_to_srgb(
            [*mtoon.parametric_rim_color_factor, 1]
        )
        self.create_mtoon1_downgraded_texture(
            mtoon.rim_multiply_texture.index,
            texture_properties,
            "_RimTexture",
            vector_properties,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            buffer0,
            image_name_to_image_index,
        )

        vector_properties["_OutlineColor"] = convert.linear_to_srgb(
            [*mtoon.outline_color_factor, 1]
        )
        self.create_mtoon1_downgraded_texture(
            mtoon.outline_width_multiply_texture.index,
            texture_properties,
            "_OutlineWidthTexture",
            vector_properties,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            buffer0,
            image_name_to_image_index,
        )

        float_properties["_UvAnimScrollX"] = mtoon.uv_animation_scroll_x_speed_factor
        float_properties["_UvAnimScrollY"] = -mtoon.uv_animation_scroll_y_speed_factor
        float_properties["_UvAnimRotation"] = mtoon.uv_animation_rotation_speed_factor
        self.create_mtoon1_downgraded_texture(
            mtoon.uv_animation_mask_texture.index,
            texture_properties,
            "_UvAnimMaskTexture",
            vector_properties,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            buffer0,
            image_name_to_image_index,
        )

        float_properties["_OutlineLightingMix"] = mtoon.outline_lighting_mix_factor
        outline_color_mode = 1 if mtoon.outline_lighting_mix_factor > 0 else 0
        float_properties["_OutlineColorMode"] = outline_color_mode

        float_properties["_OutlineWidth"] = 0.0
        outline_width_world = False
        outline_width_screen = False
        outline_color_fixed = False
        outline_color_mixed = False
        if mtoon.outline_width_mode == mtoon.OUTLINE_WIDTH_MODE_NONE.identifier:
            float_properties["_OutlineWidthMode"] = 0
            float_properties["_OutlineLightingMix"] = 0
            float_properties["_OutlineColorMode"] = 0
        elif (
            mtoon.outline_width_mode
            == mtoon.OUTLINE_WIDTH_MODE_WORLD_COORDINATES.identifier
        ):
            float_properties["_OutlineWidth"] = mtoon.outline_width_factor * 100
            float_properties["_OutlineWidthMode"] = 1
            outline_width_world = True
            if outline_color_mode == 0:
                outline_color_fixed = True
            else:
                outline_color_mixed = True
        elif (
            mtoon.outline_width_mode
            == mtoon.OUTLINE_WIDTH_MODE_SCREEN_COORDINATES.identifier
        ):
            float_properties["_OutlineWidth"] = mtoon.outline_width_factor * 200
            float_properties["_OutlineWidthMode"] = 2
            outline_width_screen = True
            if outline_color_mode == 0:
                outline_color_fixed = True
            else:
                outline_color_mixed = True

        if outline_width_world:
            keyword_map["MTOON_OUTLINE_WIDTH_WORLD"] = True
        elif outline_width_screen:
            keyword_map["MTOON_OUTLINE_WIDTH_SCREEN"] = True

        if outline_color_fixed:
            keyword_map["MTOON_OUTLINE_COLOR_FIXED"] = outline_color_fixed
        elif outline_color_mixed:
            keyword_map["MTOON_OUTLINE_COLOR_MIXED"] = outline_color_mixed

        float_properties["_Cutoff"] = 0.5
        if gltf.alpha_mode == gltf.ALPHA_MODE_OPAQUE.identifier:
            blend_mode = 0
            src_blend = 1
            dst_blend = 0
            z_write = 1
            alphatest_on = False
            render_queue = -1
            render_type = "Opaque"
        elif gltf.alpha_mode == gltf.ALPHA_MODE_MASK.identifier:
            blend_mode = 1
            src_blend = 1
            dst_blend = 0
            z_write = 1
            alphatest_on = True
            render_queue = gltf.mtoon0_render_queue
            render_type = "TransparentCutout"
            float_properties["_Cutoff"] = gltf.alpha_cutoff
            material_dict["alphaCutoff"] = gltf.alpha_cutoff
        elif not mtoon.transparent_with_z_write:
            blend_mode = 2
            src_blend = 5
            dst_blend = 10
            z_write = 0
            alphatest_on = False
            render_queue = gltf.mtoon0_render_queue
            render_type = "Transparent"
        else:
            blend_mode = 3
            src_blend = 5
            dst_blend = 10
            z_write = 1
            alphatest_on = False
            render_queue = gltf.mtoon0_render_queue
            render_type = "Transparent"
            float_properties["_Cutoff"] = gltf.alpha_cutoff  # for compatibility

        self.create_mtoon1_downgraded_texture(
            gltf.mtoon0_receive_shadow_texture,
            texture_properties,
            "_ReceiveShadowTexture",
            vector_properties,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            buffer0,
            image_name_to_image_index,
        )
        float_properties["_ReceiveShadowRate"] = gltf.mtoon0_receive_shadow_rate

        keyword_map["_ALPHABLEND_ON"] = material.blend_method not in ("OPAQUE", "CLIP")
        keyword_map["_ALPHAPREMULTIPLY_ON"] = False

        float_properties["_BlendMode"] = blend_mode
        float_properties["_SrcBlend"] = src_blend
        float_properties["_DstBlend"] = dst_blend
        float_properties["_ZWrite"] = z_write
        if alphatest_on:
            keyword_map["_ALPHATEST_ON"] = alphatest_on
        tag_map["RenderType"] = render_type

        float_properties["_MToonVersion"] = MtoonUnversioned.version
        if gltf.mtoon0_front_cull_mode:
            float_properties["_CullMode"] = 1
        elif material.use_backface_culling:
            float_properties["_CullMode"] = 2
        else:
            float_properties["_CullMode"] = 0
        float_properties["_OutlineCullMode"] = 1
        float_properties["_DebugMode"] = 0
        float_properties["_LightColorAttenuation"] = gltf.mtoon0_light_color_attenuation
        float_properties["_OutlineScaledMaxDistance"] = (
            gltf.mtoon0_outline_scaled_max_distance
        )

        keyword_map["MTOON_DEBUG_NORMAL"] = False
        keyword_map["MTOON_DEBUG_LITSHADERATE"] = False

        vrm_material_property_dict.update(
            {
                "name": material.name,
                "shader": "VRM/MToon",
                "keywordMap": make_json(keyword_map),
                "tagMap": make_json(tag_map),
                "floatProperties": make_json(float_properties),
                "vectorProperties": make_json(vector_properties),
                "textureProperties": make_json(texture_properties),
                "renderQueue": render_queue,
            }
        )

    def find_or_create_image(
        self,
        image_dicts: list[dict[str, Json]],
        buffer_view_dicts: list[dict[str, Json]],
        buffer0: bytearray,
        image_name_to_index_dict: dict[str, int],
        image: Image,
    ) -> int:
        image_index = image_name_to_index_dict.get(image.name)
        if isinstance(image_index, int):
            return image_index

        image_bytes, mime = image_to_image_bytes(
            image, self.gltf2_addon_export_settings
        )

        image_buffer_view_index = len(buffer_view_dicts)
        buffer_view_dicts.append(
            {
                "buffer": 0,
                "byteOffset": len(buffer0),
                "byteLength": len(image_bytes),
            }
        )
        buffer0.extend(image_bytes)

        image_index = len(image_dicts)
        image_dicts.append(
            {
                "name": image.name,
                "mimeType": mime,
                "bufferView": image_buffer_view_index,
            }
        )

        image_name_to_index_dict[image.name] = image_index

        return image_index

    def create_mtoon0_khr_texture_transform(
        self, node: Node, texture_input_name: str
    ) -> tuple[dict[str, Json], tuple[float, float, float, float]]:
        default: tuple[dict[str, Json], tuple[float, float, float, float]] = (
            {
                "offset": [0, 0],
                "scale": [1, 1],
            },
            (0, 0, 1, 1),
        )

        texture_input = node.inputs.get(texture_input_name)
        if not texture_input:
            return default

        texture_input_links = texture_input.links
        if not texture_input_links:
            return default

        x_from_node = texture_input_links[0].from_node
        if not x_from_node:
            return default

        x_inputs = x_from_node.inputs
        if not x_inputs:
            return default

        x_links = x_inputs[0].links
        if not x_links:
            return default

        uv_offset_scaling_node = x_links[0].from_node
        if not uv_offset_scaling_node or uv_offset_scaling_node.type != "MAPPING'":
            return default

        location_input = uv_offset_scaling_node.inputs.get("Location")
        offset = (0.0, 0.0)
        if isinstance(location_input, shader.VECTOR_SOCKET_CLASSES):
            offset = (
                location_input.default_value[0],
                location_input.default_value[1],
            )

        scale_input = uv_offset_scaling_node.inputs.get("Scale")
        scale = (1.0, 1.0)
        if isinstance(scale_input, shader.VECTOR_SOCKET_CLASSES):
            scale = (
                scale_input.default_value[0],
                scale_input.default_value[1],
            )

        return (
            {
                "offset": list(offset),
                "scale": list(scale),
            },
            (*offset, *scale),
        )

    def create_mtoon0_texture_info_dict(
        self,
        context: Context,
        texture_dicts: list[dict[str, Json]],
        sampler_dicts: list[dict[str, Json]],
        image_dicts: list[dict[str, Json]],
        buffer_view_dicts: list[dict[str, Json]],
        extensions_used: list[str],
        buffer0: bytearray,
        node: Node,
        texture_input_name: str,
        image_name_to_index_dict: dict[str, int],
        *,
        use_khr_texture_transform: bool = False,
    ) -> Optional[tuple[dict[str, Json], int, tuple[float, float, float, float]]]:
        image_name_and_sampler_type = shader.get_image_name_and_sampler_type(
            node, texture_input_name
        )
        if image_name_and_sampler_type is None:
            return None

        image_name, wrap_type, filter_type = image_name_and_sampler_type
        image_index = self.find_or_create_image(
            image_dicts,
            buffer_view_dicts,
            buffer0,
            image_name_to_index_dict,
            context.blend_data.images[image_name],
        )

        sampler_dict: dict[str, Json] = {
            "magFilter": filter_type,
            "minFilter": filter_type,
            "wrapS": wrap_type,
            "wrapT": wrap_type,
        }
        if sampler_dict in sampler_dicts:
            sampler_index = sampler_dicts.index(sampler_dict)
        else:
            sampler_index = len(sampler_dicts)
            sampler_dicts.append(sampler_dict)

        texture_dict: dict[str, Json] = {
            "sampler": sampler_index,
            "source": image_index,
        }

        if texture_dict in texture_dicts:
            texture_index = texture_dicts.index(texture_dict)
        else:
            texture_index = len(texture_dicts)
            texture_dicts.append(texture_dict)

        khr_texture_transform_dict, vector_property = (
            self.create_mtoon0_khr_texture_transform(node, texture_input_name)
        )

        texture_info: dict[str, Json] = {"index": texture_index}

        if use_khr_texture_transform:
            texture_info["extensions"] = {
                "KHR_texture_transform": khr_texture_transform_dict
            }
            extensions_used.append("KHR_texture_transform")

        return (
            texture_info,
            texture_index,
            vector_property,
        )

    def write_legacy_mtoon_unversioned_material(
        self,
        _progress: Progress,
        texture_dicts: list[dict[str, Json]],
        sampler_dicts: list[dict[str, Json]],
        image_dicts: list[dict[str, Json]],
        buffer_view_dicts: list[dict[str, Json]],
        extensions_used: list[str],
        buffer0: bytearray,
        image_name_to_image_index: dict[str, int],
        material: Material,
        material_dict: dict[str, Json],
        vrm_material_property_dict: dict[str, Json],
        node: ShaderNodeGroup,
    ) -> None:
        keyword_map: dict[str, bool] = {}
        tag_map: dict[str, str] = {}
        texture_properties: dict[str, int] = {}
        material_dict.update(
            {
                "name": material.name,
                "extensions": {"KHR_materials_unlit": {}},
                "doubleSided": not material.use_backface_culling,
            }
        )
        extensions_used.append("KHR_materials_unlit")
        pbr_metallic_roughness_dict: dict[str, Json] = {
            "metallicFactor": 0,
            "roughnessFactor": 0.9,
        }

        color = shader.get_rgba_value_or(
            node,
            "DiffuseColor",
            0.0,
            1.0,
            (
                1.0,
                1.0,
                1.0,
                1.0,
            ),
        )
        emission_color = shader.get_rgba_value(node, "EmissionColor", 0.0, 1.0)
        if emission_color is None:
            emission_color = (0.0, 0.0, 0.0, 1.0)
        else:
            material_dict["emissiveFactor"] = make_json(emission_color[:3])

        pbr_metallic_roughness_dict["baseColorFactor"] = make_json(color)

        vector_properties: dict[str, Sequence[float]] = {
            "_Color": color,
            "_EmissionColor": emission_color,
            "_ShadeColor": shader.get_rgba_value_or(node, "ShadeColor", 0.0, 1.0),
            "_OutlineColor": shader.get_rgba_value_or(node, "OutlineColor", 0.0, 1.0),
            "_RimColor": shader.get_rgba_value_or(node, "RimColor", 0.0, 1.0),
        }

        float_properties: dict[str, Union[float, int]] = {
            "_MToonVersion": MtoonUnversioned.version,
            "_DebugMode": 0,
            "_ShadeShift": shader.get_float_value_or(node, "ShadeShift"),
            "_ShadeToony": shader.get_float_value_or(
                node, "ShadeToony", default_value=0.5
            ),
            "_ShadingGradeRate": shader.get_float_value_or(
                node, "ShadingGradeRate", default_value=0.5
            ),
            "_ReceiveShadowRate": shader.get_float_value_or(
                node, "ReceiveShadowRate", default_value=0.5
            ),
            "_LightColorAttenuation": shader.get_float_value_or(
                node, "LightColorAttenuation", default_value=0.5
            ),
            "_IndirectLightIntensity": shader.get_float_value_or(
                node, "IndirectLightIntensity", default_value=0.5
            ),
            "_RimFresnelPower": shader.get_float_value_or(
                node, "RimFresnelPower", 0.0, float_info.max, default_value=1.0
            ),
            "_RimLift": shader.get_float_value_or(node, "RimLift"),
            "_RimLightingMix": shader.get_float_value_or(node, "RimLightingMix"),
            "_OutlineLightingMix": shader.get_float_value_or(
                node, "OutlineLightingMix"
            ),
            "_OutlineScaledMaxDistance": shader.get_float_value_or(
                node, "OutlineScaleMaxDistance"
            ),
            "_OutlineWidth": shader.get_float_value_or(node, "OutlineWidth"),
            "_UvAnimRotation": shader.get_float_value_or(node, "UV_Scroll_Rotation"),
            "_UvAnimScrollX": shader.get_float_value_or(node, "UV_Scroll_X"),
            "_UvAnimScrollY": shader.get_float_value_or(node, "UV_Scroll_Y"),
        }

        alpha_cutoff = shader.get_float_value(node, "CutoffRate", 0, float_info.max)
        if alpha_cutoff is not None:
            float_properties["_Cutoff"] = alpha_cutoff

        outline_width_mode = max(
            0, min(2, int(round(shader.get_float_value_or(node, "OutlineWidthMode"))))
        )
        float_properties["_OutlineWidthMode"] = outline_width_mode
        if outline_width_mode == 1:
            keyword_map["MTOON_OUTLINE_WIDTH_WORLD"] = True
        elif outline_width_mode == 2:
            keyword_map["MTOON_OUTLINE_WIDTH_SCREEN"] = True

        outline_color_mode = max(
            0, min(2, int(round(shader.get_float_value_or(node, "OutlineColorMode"))))
        )
        float_properties["_OutlineColorMode"] = outline_color_mode
        if outline_width_mode > 0:
            if outline_color_mode == 1:
                keyword_map["MTOON_OUTLINE_COLOR_MIXED"] = True
            elif outline_color_mode == 2:
                keyword_map["MTOON_OUTLINE_COLOR_FIXED"] = True

        if material.blend_method == "OPAQUE":
            tag_map["RenderType"] = "Opaque"
            material_dict["alphaMode"] = "OPAQUE"
            float_properties["_BlendMode"] = 0
            float_properties["_SrcBlend"] = 1
            float_properties["_DstBlend"] = 0
            float_properties["_ZWrite"] = 1
            float_properties["_OutlineCullMode"] = 1
            keyword_map["MTOON_DEBUG_LITSHADERATE"] = False
            keyword_map["MTOON_DEBUG_NORMAL"] = False
            keyword_map["_ALPHABLEND_ON"] = False
            keyword_map["_ALPHAPREMULTIPLY_ON"] = False
            render_queue = -1
        elif material.blend_method == "CLIP":
            tag_map["RenderType"] = "TransparentCutout"
            material_dict["alphaMode"] = "MASK"
            float_properties["_BlendMode"] = 1
            float_properties["_SrcBlend"] = 1
            float_properties["_DstBlend"] = 0
            float_properties["_ZWrite"] = 1
            float_properties["_OutlineCullMode"] = 1
            keyword_map["MTOON_DEBUG_LITSHADERATE"] = False
            keyword_map["MTOON_DEBUG_NORMAL"] = False
            keyword_map["_ALPHABLEND_ON"] = False
            keyword_map["_ALPHAPREMULTIPLY_ON"] = False
            keyword_map["_ALPHATEST_ON"] = True
            if alpha_cutoff is not None:
                material_dict["alphaCutoff"] = alpha_cutoff
            render_queue = 2450
        else:
            tag_map["RenderType"] = "Transparent"
            material_dict["alphaMode"] = "BLEND"
            float_properties["_SrcBlend"] = 5
            float_properties["_DstBlend"] = 10
            float_properties["_OutlineCullMode"] = 1
            keyword_map["MTOON_DEBUG_LITSHADERATE"] = False
            keyword_map["MTOON_DEBUG_NORMAL"] = False
            keyword_map["_ALPHABLEND_ON"] = True
            keyword_map["_ALPHAPREMULTIPLY_ON"] = False
            transparent_with_z_write = shader.get_float_value_or(
                node, "TransparentWithZWrite", 0
            )
            if transparent_with_z_write < float_info.epsilon:
                float_properties["_BlendMode"] = 2
                float_properties["_ZWrite"] = 0
                render_queue = 3000
            else:
                float_properties["_BlendMode"] = 3
                float_properties["_ZWrite"] = 1
                render_queue = 2501

        float_properties["_CullMode"] = 2 if material.use_backface_culling else 0

        # 旧エクスポーターとの互換性のため、テクスチャ追加順を制御している

        main_tex = self.create_mtoon0_texture_info_dict(
            self.context,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            extensions_used,
            buffer0,
            node,
            "MainTexture",
            image_name_to_image_index,
            use_khr_texture_transform=True,
        )
        if main_tex:
            (
                base_color_texture_dict,
                main_tex_texture_property,
                main_tex_vector_property,
            ) = main_tex
            pbr_metallic_roughness_dict["baseColorTexture"] = base_color_texture_dict
            texture_properties["_MainTex"] = main_tex_texture_property
            vector_properties["_MainTex"] = main_tex_vector_property

        # TODO: 互換性のためのもの。たぶん正しい設定値がある気がする
        default_texture_vector_property = [0, 0, 1, 1]

        shade_texture = self.create_mtoon0_texture_info_dict(
            self.context,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            extensions_used,
            buffer0,
            node,
            "ShadeTexture",
            image_name_to_image_index,
        )
        if shade_texture:
            _, shade_texture_texture_property, _ = shade_texture
            texture_properties["_ShadeTexture"] = shade_texture_texture_property
            vector_properties["_ShadeTexture"] = default_texture_vector_property

        bump_scale = shader.get_float_value_or(node, "BumpScale", default_value=0.5)
        float_properties["_BumpScale"] = bump_scale

        bump_map = self.create_mtoon0_texture_info_dict(
            self.context,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            extensions_used,
            buffer0,
            node,
            "NormalmapTexture",
            image_name_to_image_index,
            use_khr_texture_transform=True,
        )
        if not bump_map:
            bump_map = self.create_mtoon0_texture_info_dict(
                self.context,
                texture_dicts,
                sampler_dicts,
                image_dicts,
                buffer_view_dicts,
                extensions_used,
                buffer0,
                node,
                "NomalmapTexture",
                image_name_to_image_index,
                use_khr_texture_transform=True,
            )
        if bump_map:
            normal_texture_info, bump_map_texture_property, _ = bump_map
            material_dict["normalTexture"] = normal_texture_info
            texture_properties["_BumpMap"] = bump_map_texture_property
            vector_properties["_BumpMap"] = default_texture_vector_property
            keyword_map["_NORMALMAP"] = True
            normal_texture_info["scale"] = bump_scale

        for socket_name, texture_property_key in {
            "ReceiveShadow_Texture": "_ReceiveShadowTexture",
            "ShadingGradeTexture": "_ShadingGradeTexture",
        }.items():
            texture = self.create_mtoon0_texture_info_dict(
                self.context,
                texture_dicts,
                sampler_dicts,
                image_dicts,
                buffer_view_dicts,
                extensions_used,
                buffer0,
                node,
                socket_name,
                image_name_to_image_index,
            )
            if not texture:
                continue
            _, texture_property, _ = texture
            texture_properties[texture_property_key] = texture_property
            vector_properties[texture_property_key] = default_texture_vector_property

        emission_map = self.create_mtoon0_texture_info_dict(
            self.context,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            extensions_used,
            buffer0,
            node,
            "Emission_Texture",
            image_name_to_image_index,
            use_khr_texture_transform=True,
        )
        if emission_map:
            emissive_texture_info, emission_map_texture_property, _ = emission_map
            material_dict["emissiveTexture"] = emissive_texture_info
            texture_properties["_EmissionMap"] = emission_map_texture_property
            vector_properties["_EmissionMap"] = default_texture_vector_property

        for socket_name, texture_property_key in {
            "SphereAddTexture": "_SphereAdd",
            "RimTexture": "_RimTexture",
            "OutlineWidthTexture": "_OutlineWidthTexture",
            "UV_Animation_Mask_Texture": "_UvAnimMaskTexture",
        }.items():
            texture = self.create_mtoon0_texture_info_dict(
                self.context,
                texture_dicts,
                sampler_dicts,
                image_dicts,
                buffer_view_dicts,
                extensions_used,
                buffer0,
                node,
                socket_name,
                image_name_to_image_index,
            )
            if not texture:
                continue
            _, texture_property, _ = texture
            texture_properties[texture_property_key] = texture_property
            vector_properties[texture_property_key] = default_texture_vector_property

        if pbr_metallic_roughness_dict:
            material_dict["pbrMetallicRoughness"] = pbr_metallic_roughness_dict

        vrm_material_property_dict.update(
            {
                "name": material.name,
                "shader": "VRM/MToon",
                "renderQueue": render_queue,
                "keywordMap": make_json(keyword_map),
                "tagMap": make_json(tag_map),
                "floatProperties": make_json(float_properties),
                "vectorProperties": make_json(vector_properties),
                "textureProperties": make_json(texture_properties),
            }
        )

    def write_legacy_gltf_material(
        self,
        _progress: Progress,
        texture_dicts: list[dict[str, Json]],
        sampler_dicts: list[dict[str, Json]],
        image_dicts: list[dict[str, Json]],
        buffer_view_dicts: list[dict[str, Json]],
        extensions_used: list[str],
        buffer0: bytearray,
        image_name_to_image_index: dict[str, int],
        material: Material,
        material_dict: dict[str, Json],
        vrm_material_property_dict: dict[str, Json],
        node: ShaderNodeGroup,
    ) -> None:
        vrm_material_property_dict.update(
            {
                "name": material.name,
                "shader": "VRM_USE_GLTFSHADER",
                "keywordMap": {},
                "tagMap": {},
                "floatProperties": {},
                "vectorProperties": {},
                "textureProperties": {},
                "extras": {"VRM_Addon_for_Blender_legacy_gltf_material": {}},
            }
        )

        pbr_metallic_roughness_dict: dict[str, Json] = {
            "baseColorFactor": list(
                shader.get_rgba_value_or(
                    node, "base_Color", 0.0, 1.0, default_value=(1, 1, 1, 1)
                )
            ),
            "metallicFactor": shader.get_float_value_or(node, "metallic", 0.0, 1.0),
            "roughnessFactor": shader.get_float_value_or(node, "roughness", 0.0, 1.0),
        }

        material_dict.update(
            {
                "name": material.name,
                "emissiveFactor": list(
                    shader.get_rgb_value_or(node, "emissive_color", 0.0, 1.0)
                ),
                "doubleSided": not material.use_backface_culling,
            }
        )

        if material.blend_method == "OPAQUE":
            material_dict["alphaMode"] = "OPAQUE"
        elif material.blend_method == "CLIP":
            material_dict["alphaMode"] = "MASK"
            material_dict["alphaCutoff"] = material.alpha_threshold
        else:
            material_dict["alphaMode"] = "BLEND"

        normal_texture = self.create_mtoon0_texture_info_dict(
            self.context,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            extensions_used,
            buffer0,
            node,
            "normal",
            image_name_to_image_index,
        )
        if normal_texture:
            (normal_texture_dict, _, _) = normal_texture
            material_dict["normalTexture"] = normal_texture_dict

        emissive_texture = self.create_mtoon0_texture_info_dict(
            self.context,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            extensions_used,
            buffer0,
            node,
            "emissive_texture",
            image_name_to_image_index,
        )
        if emissive_texture:
            (emissive_texture_dict, _, _) = emissive_texture
            material_dict["emissiveTexture"] = emissive_texture_dict

        base_color_texture = self.create_mtoon0_texture_info_dict(
            self.context,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            extensions_used,
            buffer0,
            node,
            "color_texture",
            image_name_to_image_index,
        )
        if base_color_texture:
            (base_color_texture_dict, _, _) = base_color_texture
            pbr_metallic_roughness_dict["baseColorTexture"] = base_color_texture_dict

        metallic_roughness_texture = self.create_mtoon0_texture_info_dict(
            self.context,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            extensions_used,
            buffer0,
            node,
            "metallic_roughness_texture",
            image_name_to_image_index,
        )
        if metallic_roughness_texture:
            (metallic_roughness_texture_dict, _, _) = metallic_roughness_texture
            pbr_metallic_roughness_dict["metallicRoughnessTexture"] = (
                metallic_roughness_texture_dict
            )

        occlusion_texture = self.create_mtoon0_texture_info_dict(
            self.context,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            extensions_used,
            buffer0,
            node,
            "occlusion_texture",
            image_name_to_image_index,
        )
        if occlusion_texture:
            (occlusion_texture_dict, _, _) = occlusion_texture
            pbr_metallic_roughness_dict["occlusionTexture"] = occlusion_texture_dict

        if pbr_metallic_roughness_dict:
            material_dict["pbrMetallicRoughness"] = pbr_metallic_roughness_dict

        if shader.get_float_value_or(node, "unlit") > 0.5:
            material_dict["extensions"] = {"KHR_materials_unlit": {}}
            extensions_used.append("KHR_materials_unlit")

    def write_legacy_transparent_zwrite_material(
        self,
        _progress: Progress,
        texture_dicts: list[dict[str, Json]],
        sampler_dicts: list[dict[str, Json]],
        image_dicts: list[dict[str, Json]],
        buffer_view_dicts: list[dict[str, Json]],
        extensions_used: list[str],
        buffer0: bytearray,
        image_name_to_image_index: dict[str, int],
        material: Material,
        material_dict: dict[str, Json],
        vrm_material_property_dict: dict[str, Json],
        node: ShaderNodeGroup,
    ) -> None:
        vector_properties: dict[str, Sequence[float]] = {}
        texture_properties: dict[str, int] = {}

        vrm_material_property_dict.update(
            {
                "name": material.name,
                "shader": "VRM/UnlitTransparentZWrite",
                "renderQueue": 2600,
                "keywordMap": {},
                "tagMap": {"RenderType": "Transparent"},
                "floatProperties": {},
            }
        )

        pbr_metallic_roughness_dict: dict[str, Json] = {
            "baseColorFactor": [1, 1, 1, 1],
            "metallicFactor": 0,
            "roughnessFactor": 0.9,
        }

        material_dict.update(
            {
                "name": material.name,
                "alphaMode": "BLEND",
                "doubleSided": False,
                "extensions": {"KHR_materials_unlit": {}},
            }
        )

        if pbr_metallic_roughness_dict:
            material_dict["pbrMetallicRoughness"] = pbr_metallic_roughness_dict

        main_tex = self.create_mtoon0_texture_info_dict(
            self.context,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            extensions_used,
            buffer0,
            node,
            "Main_Texture",
            image_name_to_image_index,
        )
        if main_tex:
            (
                base_color_texture_dict,
                main_tex_texture_property,
                main_tex_vector_property,
            ) = main_tex
            pbr_metallic_roughness_dict["baseColorTexture"] = base_color_texture_dict
            texture_properties["_MainTex"] = main_tex_texture_property
            vector_properties["_MainTex"] = main_tex_vector_property

        vrm_material_property_dict["vectorProperties"] = make_json(vector_properties)
        vrm_material_property_dict["textureProperties"] = make_json(texture_properties)

    def write_gltf_material(
        self,
        _progress: Progress,
        texture_dicts: list[dict[str, Json]],
        sampler_dicts: list[dict[str, Json]],
        image_dicts: list[dict[str, Json]],
        buffer_view_dicts: list[dict[str, Json]],
        extensions_used: list[str],
        buffer0: bytearray,
        gltf2_io_texture_images: list[Gltf2IoTextureImage],
        material: Material,
        material_dict: dict[str, Json],
        vrm_material_property_dict: dict[str, Json],
    ) -> None:
        vrm_material_property_dict.update(
            {
                "name": material.name,
                "shader": "VRM_USE_GLTFSHADER",
                "keywordMap": {},
                "tagMap": {},
                "floatProperties": {},
                "vectorProperties": {},
                "textureProperties": {},
            }
        )

        if bpy.app.version < (3, 6):
            module_name = "io_scene_gltf2.blender.exp.gltf2_blender_gather_materials"
        elif bpy.app.version < (4, 3):
            module_name = (
                "io_scene_gltf2.blender.exp.material.gltf2_blender_gather_materials"
            )
        else:
            module_name = "io_scene_gltf2.blender.exp.material.materials"
        try:
            gltf2_blender_gather_materials = importlib.import_module(module_name)
        except ModuleNotFoundError:
            logger.exception("Failed to import glTF 2.0 Add-on")
            return

        gather_material = gltf2_blender_gather_materials.gather_material

        gltf2_io_material: Optional[object] = None
        try:
            if bpy.app.version < (3, 2):
                # https://github.com/KhronosGroup/glTF-Blender-IO/blob/abd8380e19dbe5e5fb9042513ad6b744032bc9bc/addons/io_scene_gltf2/blender/exp/gltf2_blender_gather_materials.py#L32
                gltf2_io_material = gather_material(
                    material, self.gltf2_addon_export_settings
                )
            elif bpy.app.version < (4, 0):
                # https://github.com/KhronosGroup/glTF-Blender-IO/blob/9e08d423a803da52eb08fbc93d9aa99f3f681a27/addons/io_scene_gltf2/blender/exp/gltf2_blender_gather_primitives.py#L71-L96
                # https://github.com/KhronosGroup/glTF-Blender-IO/blob/9e08d423a803da52eb08fbc93d9aa99f3f681a27/addons/io_scene_gltf2/blender/exp/gltf2_blender_gather_materials.py#L42
                gltf2_io_material = gather_material(
                    material, 0, self.gltf2_addon_export_settings
                )
            else:
                # https://github.com/KhronosGroup/glTF-Blender-IO/blob/765c1bd8f59ce34d6e346147f379af191969777f/addons/io_scene_gltf2/blender/exp/material/gltf2_blender_gather_materials.py#L47
                gltf2_io_material, _ = gather_material(
                    material, self.gltf2_addon_export_settings
                )

            alpha_cutoff = getattr(gltf2_io_material, "alpha_cutoff", None)
            if isinstance(alpha_cutoff, (int, float)):
                material_dict["alphaCutoff"] = alpha_cutoff

            alpha_mode = getattr(gltf2_io_material, "alpha_mode", None)
            if isinstance(alpha_mode, str):
                material_dict["alphaMode"] = alpha_mode

            double_sided = getattr(gltf2_io_material, "double_sided", None)
            if isinstance(double_sided, bool):
                material_dict["doubleSided"] = double_sided

            emissive_factor = convert.sequence_or_none(
                getattr(gltf2_io_material, "emissive_factor", None)
            )
            if emissive_factor is not None:
                material_dict["emissiveFactor"] = make_json(emissive_factor)

            assign_dict(
                material_dict,
                "emissiveTexture",
                self.create_gltf2_io_texture(
                    getattr(gltf2_io_material, "emissive_texture", None),
                    texture_dicts,
                    sampler_dicts,
                    image_dicts,
                    buffer_view_dicts,
                    buffer0,
                    gltf2_io_texture_images,
                ),
            )

            extensions = convert.mapping_or_none(
                getattr(gltf2_io_material, "extensions", None)
            )
            if extensions is not None:
                extensions_dict: dict[str, Json] = {}

                # https://github.com/KhronosGroup/glTF/tree/19a1d820040239bca1327fc26220ae8cae9f948c/extensions/2.0/Khronos/KHR_materials_unlit
                if extensions.get("KHR_materials_unlit") is not None:
                    extensions_dict["KHR_materials_unlit"] = {}
                    extensions_used.append("KHR_materials_unlit")

                # https://github.com/KhronosGroup/glTF/blob/9c4a3567384b4d9f2706cdd9623bbb5ca7b341ad/extensions/2.0/Khronos/KHR_materials_emissive_strength
                khr_materials_emissive_strength = convert.mapping_or_none(
                    getattr(
                        extensions.get("KHR_materials_emissive_strength"),
                        "extension",
                        None,
                    )
                )
                if isinstance(khr_materials_emissive_strength, dict):
                    emissive_strength = khr_materials_emissive_strength.get(
                        "emissiveStrength"
                    )
                    if (
                        isinstance(emissive_strength, (int, float))
                        and emissive_strength >= 0
                        and emissive_strength != 1.0
                    ):
                        extensions_dict["KHR_materials_emissive_strength"] = {
                            "emissiveStrength": emissive_strength,
                        }
                        extensions_used.append("KHR_materials_emissive_strength")

                if extensions_dict:
                    material_dict["extensions"] = extensions_dict

            assign_dict(
                material_dict,
                "normalTexture",
                self.create_gltf2_io_texture(
                    getattr(gltf2_io_material, "normal_texture", None),
                    texture_dicts,
                    sampler_dicts,
                    image_dicts,
                    buffer_view_dicts,
                    buffer0,
                    gltf2_io_texture_images,
                ),
            )

            assign_dict(
                material_dict,
                "occlusionTexture",
                self.create_gltf2_io_texture(
                    getattr(gltf2_io_material, "occlusion_texture", None),
                    texture_dicts,
                    sampler_dicts,
                    image_dicts,
                    buffer_view_dicts,
                    buffer0,
                    gltf2_io_texture_images,
                ),
            )

            pbr_metallic_roughness = getattr(
                gltf2_io_material, "pbr_metallic_roughness", None
            )
            if pbr_metallic_roughness is not None:
                pbr_metallic_roughness_dict: dict[str, Json] = {}

                base_color_factor = convert.sequence_or_none(
                    getattr(pbr_metallic_roughness, "base_color_factor", None)
                )
                if base_color_factor is not None:
                    pbr_metallic_roughness_dict["baseColorFactor"] = make_json(
                        base_color_factor
                    )

                assign_dict(
                    pbr_metallic_roughness_dict,
                    "baseColorTexture",
                    self.create_gltf2_io_texture(
                        getattr(pbr_metallic_roughness, "base_color_texture", None),
                        texture_dicts,
                        sampler_dicts,
                        image_dicts,
                        buffer_view_dicts,
                        buffer0,
                        gltf2_io_texture_images,
                    ),
                )

                metallic_factor = getattr(
                    pbr_metallic_roughness, "metallic_factor", None
                )
                if isinstance(metallic_factor, (int, float)):
                    pbr_metallic_roughness_dict["metallicFactor"] = metallic_factor

                assign_dict(
                    pbr_metallic_roughness_dict,
                    "metallicRoughnessTexture",
                    self.create_gltf2_io_texture(
                        getattr(
                            pbr_metallic_roughness, "metallic_roughness_texture", None
                        ),
                        texture_dicts,
                        sampler_dicts,
                        image_dicts,
                        buffer_view_dicts,
                        buffer0,
                        gltf2_io_texture_images,
                    ),
                )

                roughness_factor = getattr(
                    pbr_metallic_roughness, "roughness_factor", None
                )
                if isinstance(roughness_factor, (int, float)):
                    pbr_metallic_roughness_dict["roughnessFactor"] = roughness_factor

                if pbr_metallic_roughness_dict:
                    material_dict["pbrMetallicRoughness"] = pbr_metallic_roughness_dict
        except Exception:
            logger.exception("Failed to generate glTF Material using glTF 2.0 add-on")

    def write_material(
        self,
        progress: Progress,
        material_dicts: list[dict[str, Json]],
        texture_dicts: list[dict[str, Json]],
        sampler_dicts: list[dict[str, Json]],
        image_dicts: list[dict[str, Json]],
        buffer_view_dicts: list[dict[str, Json]],
        extensions_vrm_material_property_dicts: list[Json],
        extensions_used: list[str],
        buffer0: bytearray,
        material_name_to_material_index: dict[str, int],
        image_name_to_image_index: dict[str, int],
        gltf2_io_texture_images: list[Gltf2IoTextureImage],
        material: Material,
    ) -> None:
        material_dict: dict[str, Json] = {
            "name": material.name,
        }
        vrm_material_property_dict: dict[str, Json] = {
            "name": material.name,
            "shader": "VRM_USE_GLTFSHADER",
        }
        material_index = len(material_dicts)
        material_name_to_material_index[material.name] = material_index
        material_dicts.append(material_dict)
        extensions_vrm_material_property_dicts.append(vrm_material_property_dict)

        mtoon1 = get_material_extension(material).mtoon1
        if mtoon1.enabled:
            self.write_mtoon1_downgraded_material(
                progress,
                texture_dicts,
                sampler_dicts,
                image_dicts,
                buffer_view_dicts,
                extensions_used,
                buffer0,
                image_name_to_image_index,
                material,
                material_dict,
                vrm_material_property_dict,
            )
            return

        legacy_shader_node_group, legacy_shader_name = search.legacy_shader_node(
            material
        )
        if not legacy_shader_node_group:
            pass
        elif legacy_shader_name == "MToon_unversioned":
            self.write_legacy_mtoon_unversioned_material(
                progress,
                texture_dicts,
                sampler_dicts,
                image_dicts,
                buffer_view_dicts,
                extensions_used,
                buffer0,
                image_name_to_image_index,
                material,
                material_dict,
                vrm_material_property_dict,
                legacy_shader_node_group,
            )
            return
        elif legacy_shader_name == "GLTF":
            self.write_legacy_gltf_material(
                progress,
                texture_dicts,
                sampler_dicts,
                image_dicts,
                buffer_view_dicts,
                extensions_used,
                buffer0,
                image_name_to_image_index,
                material,
                material_dict,
                vrm_material_property_dict,
                legacy_shader_node_group,
            )
            return
        elif legacy_shader_name == "TRANSPARENT_ZWRITE":
            self.write_legacy_transparent_zwrite_material(
                progress,
                texture_dicts,
                sampler_dicts,
                image_dicts,
                buffer_view_dicts,
                extensions_used,
                buffer0,
                image_name_to_image_index,
                material,
                material_dict,
                vrm_material_property_dict,
                legacy_shader_node_group,
            )
            return

        self.write_gltf_material(
            progress,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            extensions_used,
            buffer0,
            gltf2_io_texture_images,
            material,
            material_dict,
            vrm_material_property_dict,
        )

    def write_materials(
        self,
        _progress: Progress,
        material_dicts: list[dict[str, Json]],
        texture_dicts: list[dict[str, Json]],
        sampler_dicts: list[dict[str, Json]],
        image_dicts: list[dict[str, Json]],
        buffer_view_dicts: list[dict[str, Json]],
        extensions_vrm_material_property_dicts: list[Json],
        extensions_used: list[str],
        buffer0: bytearray,
        material_name_to_material_index: dict[str, int],
        image_name_to_image_index: dict[str, int],
    ) -> None:
        gltf2_io_texture_images: list[Vrm0Exporter.Gltf2IoTextureImage] = []
        for material in search.export_materials(self.context, self.export_objects):
            self.write_material(
                _progress,
                material_dicts,
                texture_dicts,
                sampler_dicts,
                image_dicts,
                buffer_view_dicts,
                extensions_vrm_material_property_dicts,
                extensions_used,
                buffer0,
                material_name_to_material_index,
                image_name_to_image_index,
                gltf2_io_texture_images,
                material,
            )

    def write_armature(
        self,
        progress: Progress,
        node_dicts: list[dict[str, Json]],
        accessor_dicts: list[dict[str, Json]],
        buffer_view_dicts: list[dict[str, Json]],
        buffer0: bytearray,
        bone_name_to_node_index: dict[str, int],
    ) -> tuple[Sequence[int], Mapping[str, Json], Sequence[int]]:
        bones = [bone for bone in self.armature.pose.bones if not bone.parent]
        root_node_index = len(node_dicts)
        if not bones:
            logger.error("No bones")
            node_dicts.append(
                {
                    "name": self.armature.name,
                }
            )
            return [root_node_index], {}, []

        bone_name_to_inverse_bind_matrix: dict[str, Matrix] = {}
        humanoid_root_bone_index: Optional[int] = None
        humanoid_root_bone: Optional[PoseBone] = None

        if len(bones) == 1:
            humanoid_root_bone = bones[0]
            humanoid_root_bone_index = self.write_armature_bone_nodes(
                progress,
                node_dicts,
                buffer0,
                bones[0],
                bone_name_to_node_index,
                bone_name_to_inverse_bind_matrix,
            )
            scene_node_indices: list[int] = [humanoid_root_bone_index]
        else:
            # ルートボーンか複数ある場合、それぞれをシーンに展開する
            # これは旧エクスポーターの仕様そのままだが、本当に正しいかは自信がない
            # 親となるボーンを作り、それにskinをつけるのが本当は良いかもしれない
            scene_node_indices = []
            for bone in bones:
                root_node_index = self.write_armature_bone_nodes(
                    progress,
                    node_dicts,
                    buffer0,
                    bone,
                    bone_name_to_node_index,
                    bone_name_to_inverse_bind_matrix,
                )
                scene_node_indices.append(root_node_index)

                # Humanoidに属しているボーンがあるかを調べ、
                # それをhumanoid_root_bone_indexとして設定
                humanoid = get_armature_extension(self.armature_data).vrm0.humanoid
                traversing_bones = [bone]
                while traversing_bones:
                    traversing_bone = traversing_bones.pop()
                    if any(
                        human_bone.node.bone_name == traversing_bone.name
                        for human_bone in humanoid.human_bones
                    ):
                        humanoid_root_bone = bone
                        humanoid_root_bone_index = root_node_index
                        break
                    traversing_bones.extend(traversing_bone.children)

        if humanoid_root_bone is None or humanoid_root_bone_index is None:
            logger.error("No human bone")
            return [root_node_index], {}, []

        while len(buffer0) % 4:
            buffer0.append(0)
        inverse_bind_matrices_offset = len(buffer0)

        skin_joint_node_indices: list[int] = []
        inverse_bind_matrix_struct = struct.Struct("<16f")
        for bone_name, node_index in bone_name_to_node_index.items():
            skin_joint_node_indices.append(node_index)
            inverse_bind_matrix = bone_name_to_inverse_bind_matrix.get(bone_name)
            if inverse_bind_matrix is None:
                message = f"No inverse bind matrix for {bone_name}"
                raise AssertionError(message)
            buffer0.extend(
                inverse_bind_matrix_struct.pack(*itertools.chain(*inverse_bind_matrix))
            )

        buffer_view_index = len(buffer_view_dicts)
        buffer_view_dicts.append(
            {
                "buffer": 0,
                "byteOffset": inverse_bind_matrices_offset,
                "byteLength": len(buffer0) - inverse_bind_matrices_offset,
            }
        )

        accessor_index = len(accessor_dicts)
        accessor_dicts.append(
            {
                "bufferView": buffer_view_index,
                "byteOffset": 0,
                "type": "MAT4",
                "componentType": GL_FLOAT,
                "count": len(skin_joint_node_indices),
            }
        )

        # Hitogata 0.6.0.1はskinを共有するとエラーになるようなので
        # メッシュに対してそれぞれ内容の同じskinを持たせる
        skin_dict: dict[str, Json] = {
            "joints": make_json(skin_joint_node_indices),
            "inverseBindMatrices": accessor_index,
            "skeleton": humanoid_root_bone_index,
        }

        return scene_node_indices, skin_dict, skin_joint_node_indices

    def write_armature_bone_nodes(
        self,
        progress: Progress,
        node_dicts: list[dict[str, Json]],
        buffer0: bytearray,
        bone: PoseBone,
        bone_name_to_node_index: dict[str, int],
        bone_name_to_inverse_bind_matrices: dict[str, Matrix],
    ) -> int:
        node_index = len(node_dicts)
        bone_name_to_node_index[bone.name] = node_index

        parent_bone = bone.parent
        if parent_bone is None:
            parent_world_translation = Vector((0, 0, 0))
        else:
            parent_world_translation = self.armature.matrix_world @ parent_bone.head

        world_translation = self.armature.matrix_world @ bone.head

        bone_name_to_inverse_bind_matrices[bone.name] = Matrix(
            (
                (1, 0, 0, 0),
                (0, 1, 0, 0),
                (0, 0, 1, 0),
                (world_translation.x, -world_translation.z, -world_translation.y, 1),
            )
        )

        node_dict: dict[str, Json] = {
            "name": bone.name,
            "translation": make_json(
                convert.axis_blender_to_gltf(
                    world_translation - parent_world_translation
                )
            ),
        }
        node_dicts.append(node_dict)
        if bone.children:
            node_dict["children"] = [
                self.write_armature_bone_nodes(
                    progress,
                    node_dicts,
                    buffer0,
                    child,
                    bone_name_to_node_index,
                    bone_name_to_inverse_bind_matrices,
                )
                for child in bone.children
            ]
        return node_index

    def get_or_write_cluster_empty_material(
        self,
        material_dicts: list[dict[str, Json]],
        extensions_vrm_material_property_dicts: list[Json],
    ) -> int:
        # clusterではマテリアル無しのプリミティブが許可されないため、
        # 空のマテリアルを付与する。
        missing_material_name = "glTF_2_0_default_material"
        for i, material_dict in enumerate(material_dicts):
            if material_dict.get("name") == missing_material_name:
                return i

        new_missing_material_index = len(material_dicts)
        material_dicts.append({"name": missing_material_name})
        extensions_vrm_material_property_dicts.append(
            {
                "name": missing_material_name,
                "shader": "VRM_USE_GLTFSHADER",
                "keywordMap": {},
                "tagMap": {},
                "floatProperties": {},
                "vectorProperties": {},
                "textureProperties": {},
            }
        )
        return new_missing_material_index

    def collect_vertex(
        self,
        obj: Object,
        main_mesh_data: Mesh,
        vertex_index: int,
        uv_layer: Optional[MeshUVLoopLayer],
        loop_index: int,
        vertex_group_index_to_joint: Mapping[int, int],
        bone_name_to_node_index: Mapping[str, int],
        skin_joints: Sequence[int],
        shape_key_name_to_mesh_data: Mapping[str, Mesh],
        shape_key_name_to_vertex_index_to_morph_normal_diffs: Optional[
            Mapping[str, tuple[tuple[float, float, float], ...]]
        ],
        vertex_attributes_and_targets: VertexAttributeAndTargets,
        *,
        have_skin: bool,
        no_morph_normal_export: bool,
    ) -> int:
        texcoord = None
        if uv_layer:
            texcoord_u, texcoord_v = uv_layer.data[loop_index].uv
            texcoord = (texcoord_u, 1 - texcoord_v)

        # 頂点のノーマルではなくloopのノーマルを使う。これで失うものはあると
        # 思うが、glTF 2.0アドオンと同一にしておくのが無難だろうと判断。
        # https://github.com/KhronosGroup/glTF-Blender-IO/pull/1127
        # TODO: この実装は本来はループを回った3つの法線を平均にするべき
        normal = main_mesh_data.loops[loop_index].normal

        already_added_vertex_index = (
            vertex_attributes_and_targets.find_added_vertex_index(
                blender_vertex_index=vertex_index,
                normal=convert.axis_blender_to_gltf(normal),
                texcoord=texcoord,
            )
        )
        if isinstance(already_added_vertex_index, int):
            return already_added_vertex_index

        vertex = main_mesh_data.vertices[vertex_index]
        position_x, position_y, position_z = vertex.co

        joints: Optional[tuple[int, int, int, int]] = None
        weights: Optional[tuple[float, float, float, float]] = None
        if have_skin:
            weight_and_joint_list: list[tuple[float, int]] = [
                (weight, joint)
                for vertex_group_element in vertex.groups
                if (
                    (
                        joint := vertex_group_index_to_joint.get(
                            vertex_group_element.group
                        )
                    )
                    is not None
                )
                # ウエイトがゼロの場合ジョイントもゼロにする
                # https://github.com/KhronosGroup/glTF/tree/f33f90ad9439a228bf90cde8319d851a52a3f470/specification/2.0#skinned-mesh-attributes
                and not ((weight := vertex_group_element.weight) < float_info.epsilon)
            ]
            weight_and_joint_list.sort(reverse=True)
            while len(weight_and_joint_list) < 4:
                weight_and_joint_list.append((0.0, 0))

            weights = (
                weight_and_joint_list[0][0],
                weight_and_joint_list[1][0],
                weight_and_joint_list[2][0],
                weight_and_joint_list[3][0],
            )
            joints = (
                weight_and_joint_list[0][1],
                weight_and_joint_list[1][1],
                weight_and_joint_list[2][1],
                weight_and_joint_list[3][1],
            )

            total_weight = sum(weights)
            if total_weight < float_info.epsilon:
                logger.debug(
                    "No weight on vertex index=%d mesh=%s",
                    vertex_index,
                    main_mesh_data.name,
                )

                # Attach near bone
                joint = None
                mesh_parent: Optional[Object] = obj
                while mesh_parent:
                    if mesh_parent.parent_type == "BONE":
                        if (
                            mesh_parent.parent == self.armature
                            and (
                                bone_index := bone_name_to_node_index.get(
                                    mesh_parent.parent_bone
                                )
                            )
                            is not None
                            and bone_index in skin_joints
                        ):
                            joint = skin_joints.index(bone_index)
                        break
                    if mesh_parent.parent_type == "OBJECT":
                        mesh_parent = mesh_parent.parent
                    else:
                        break

                if joint is None:
                    # TODO: たぶんhipsよりはhipsから辿ったルートボーンの方が良い
                    ext = get_armature_extension(self.armature_data)
                    for human_bone in ext.vrm0.humanoid.human_bones:
                        if human_bone.bone != "hips":
                            continue
                        if (
                            bone_index := bone_name_to_node_index.get(
                                human_bone.node.bone_name
                            )
                        ) is not None and bone_index in skin_joints:
                            joint = skin_joints.index(bone_index)

                if joint is None:
                    message = "No fallback bone index found"
                    raise ValueError(message)
                weights = (1.0, 0, 0, 0)
                joints = (joint, 0, 0, 0)
            else:
                weights = (
                    weights[0] / total_weight,
                    weights[1] / total_weight,
                    weights[2] / total_weight,
                    weights[3] / total_weight,
                )

        targets_position: list[tuple[float, float, float]] = []
        targets_normal: list[tuple[float, float, float]] = []
        for (
            shape_key_name,
            shape_key_mesh_data,
        ) in shape_key_name_to_mesh_data.items():
            (
                shape_key_position_x,
                shape_key_position_y,
                shape_key_position_z,
            ) = shape_key_mesh_data.vertices[vertex_index].co
            targets_position.append(
                convert.axis_blender_to_gltf(
                    (
                        shape_key_position_x - position_x,
                        shape_key_position_y - position_y,
                        shape_key_position_z - position_z,
                    )
                )
            )
            if no_morph_normal_export:
                targets_normal.append((0, 0, 0))
                continue

            if not shape_key_name_to_vertex_index_to_morph_normal_diffs:
                targets_normal.append((0, 0, 0))
                logger.error(
                    "BUG: shape key name to vertex index to morph normal diffs"
                    " are not created"
                )
                continue

            morph_normal_diff = shape_key_name_to_vertex_index_to_morph_normal_diffs[
                shape_key_name
            ][vertex_index]
            # logger.error(
            #     "MORPH_NORMAL_DIFF: %s %s", vertex_index, morph_normal_diff
            # )
            targets_normal.append(convert.axis_blender_to_gltf(morph_normal_diff))

        return vertex_attributes_and_targets.add_vertex(
            blender_vertex_index=vertex_index,
            position=convert.axis_blender_to_gltf(
                (
                    position_x,
                    position_y,
                    position_z,
                )
            ),
            normal=convert.axis_blender_to_gltf(normal),
            texcoord=texcoord,
            joints=joints,
            weights=weights,
            targets_position=targets_position,
            targets_normal=targets_normal,
        )

    def write_mesh_node(
        self,
        _progress: Progress,
        node_dicts: list[dict[str, Json]],
        mesh_dicts: list[dict[str, Json]],
        skin_dicts: list[dict[str, Json]],
        material_dicts: list[dict[str, Json]],
        accessor_dicts: list[dict[str, Json]],
        buffer_view_dicts: list[dict[str, Json]],
        extensions_vrm_material_property_dicts: list[Json],
        buffer0: bytearray,
        object_name_to_node_index: dict[str, int],
        bone_name_to_node_index: Mapping[str, int],
        obj: Object,
        mesh_convertible_objects: Sequence[Object],
        mesh_object_name_to_mesh_index: dict[str, int],
        material_name_to_material_index: Mapping[str, int],
        skin_dict: Mapping[str, Json],
        skin_joints: Sequence[int],
    ) -> Optional[int]:
        if obj.type not in MESH_CONVERTIBLE_OBJECT_TYPES:
            return None

        have_skin = self.have_skin(obj)

        node_index = len(node_dicts)
        node_dict: dict[str, Json] = {
            "name": obj.name,
            "rotation": [0, 0, 0, 1],  # TODO: デフォルト値と同一のため削除予定
            "scale": [1, 1, 1],  # TODO: デフォルト値と同一のため削除予定
        }

        parent_node_index = None
        parent_translation = None
        if have_skin:
            # スキンがある場合はシーンのルートノードになる
            pass
        else:
            if (
                obj.parent_type in ["ARMATURE", "OBJECT"]
                and (
                    parent := self.get_export_parent_object(
                        obj, mesh_convertible_objects
                    )
                )
                and parent in self.export_objects
            ):
                # TODO: 互換性のためネストしたメッシュを復元しないが、将来的には復元する
                # parent_translation = parent.matrix_world.to_translation()
                # parent_node_index = object_name_to_node_index.get(parent.name)
                pass

            if obj.parent_type == "BONE" and (
                bone := self.armature.pose.bones.get(obj.parent_bone)
            ):
                parent_translation = (
                    self.armature.matrix_world @ bone.matrix
                ).to_translation()
                parent_node_index = bone_name_to_node_index.get(obj.parent_bone)

        if parent_node_index is not None and 0 <= parent_node_index < len(node_dicts):
            parent_node_dict = node_dicts[parent_node_index]
            parent_children = parent_node_dict.get("children")
            if parent_children is None or not isinstance(
                parent_children, MutableSequence
            ):
                parent_children = []
                parent_node_dict["children"] = parent_children
            parent_children.append(node_index)

        if not parent_translation:
            parent_translation = Vector((0, 0, 0))

        if not have_skin:
            node_dict["translation"] = make_json(
                convert.axis_blender_to_gltf(
                    obj.matrix_world.to_translation() - parent_translation
                )
            )

        node_dicts.append(node_dict)
        object_name_to_node_index[obj.name] = node_index

        scene_node_index = None
        if parent_node_index is None:
            scene_node_index = node_index

        original_mesh_convertible = obj.data
        if not isinstance(original_mesh_convertible, (Curve, Mesh)):
            logger.error(
                "Unexpected mesh convertible object type: %s",
                type(original_mesh_convertible),
            )
            return scene_node_index

        mesh_index = len(mesh_dicts)

        original_shape_keys: Optional[Key] = None
        if isinstance(original_mesh_convertible, Mesh):
            original_mesh_convertible.calc_loop_triangles()
            original_shape_keys = original_mesh_convertible.shape_keys

        with save_workspace(self.context):
            main_mesh_data = force_apply_modifiers(self.context, obj, persistent=False)
            if not main_mesh_data:
                return scene_node_index

            shape_key_name_to_mesh_data: dict[str, Mesh] = {}
            if original_shape_keys:
                # シェイプキーごとにモディファイアを適用したメッシュを作成する。
                # これは、VRM 0.x用にglTF Nodeの回転やスケールを正規化するが、
                # ポーズモードで回転やスケールをつけた場合、その正規化のウエイト
                # 計算がシェイプキーに適用されないため、シェイプキーごとの変化量を
                # 自前で計算しなおす必要があるため。
                # 頂点のインデックスなどが変わる可能性があるためダメなパターンも
                # あると思うので、改善の余地あり。
                for shape_key in original_shape_keys.key_blocks:
                    if original_shape_keys.reference_key.name == shape_key.name:
                        continue

                    shape_key.value = 1.0
                    self.context.view_layer.update()
                    shape_mesh = force_apply_modifiers(
                        self.context, obj, persistent=False
                    )
                    shape_key.value = 0.0
                    self.context.view_layer.update()

                    if not shape_mesh:
                        continue
                    shape_key_name_to_mesh_data[shape_key.name] = shape_mesh

        obj.hide_viewport = False
        obj.hide_select = False

        # TODO: 古いアドオンとの互換性のために移動を実行しているが、不要な気がする
        mesh_data_transform = Matrix.Identity(4)
        if not have_skin:
            mesh_data_transform @= Matrix.Translation(
                -obj.matrix_world.to_translation()
            )
        mesh_data_transform @= obj.matrix_world

        for mesh_data in [main_mesh_data, *shape_key_name_to_mesh_data.values()]:
            if not mesh_data:
                continue
            mesh_data.transform(mesh_data_transform)
            if bpy.app.version < (4, 1):
                mesh_data.calc_normals_split()

        material_slot_index_to_material_name: Mapping[int, str] = {
            material_index: material_ref.name
            for material_index, material_slot in enumerate(obj.material_slots)
            if (material_ref := material_slot.material) and material_ref.name
        }

        no_morph_normal_export_material_indices: set[int] = set()
        material_name: Optional[str] = None
        material_index: Optional[int] = None
        for material_name, material_index in material_name_to_material_index.items():
            material = bpy.data.materials.get(material_name)
            if not material:
                continue

            mtoon1 = get_material_extension(material).mtoon1
            if mtoon1.export_shape_key_normals:
                continue

            if mtoon1.enabled:
                no_morph_normal_export_material_indices.add(material_index)
                continue

            _, legacy_shader_name = search.legacy_shader_node(material)
            if legacy_shader_name == "MToon_unversioned":
                no_morph_normal_export_material_indices.add(material_index)

        shape_key_name_to_vertex_index_to_morph_normal_diffs = None
        if original_shape_keys and shape_key_name_to_mesh_data:
            shape_key_name_to_vertex_index_to_morph_normal_diffs = (
                self.create_shape_key_name_to_vertex_index_to_morph_normal_diffs(
                    self.context,
                    main_mesh_data,
                    shape_key_name_to_mesh_data,
                    original_shape_keys.reference_key.name,
                )
            )

        vertex_attributes_and_targets = Vrm0Exporter.VertexAttributeAndTargets(
            list(shape_key_name_to_mesh_data.keys())
        )
        material_index_to_vertex_indices: dict[int, bytearray] = {}
        vertex_indices_struct = struct.Struct("<I")

        vertex_group_index_to_joint: Mapping[int, int] = {
            vertex_group_index: skin_joints.index(vertex_group_node_index)
            for vertex_group_index, vertex_group in enumerate(obj.vertex_groups)
            if (
                vertex_group_node_index := bone_name_to_node_index.get(
                    vertex_group.name
                )
            )
            is not None
            and vertex_group_node_index in skin_joints
        }

        uv_layers = main_mesh_data.uv_layers
        uv_layer = uv_layers.active
        main_mesh_data.calc_loop_triangles()
        for loop_triangle in main_mesh_data.loop_triangles:
            material_slot_index = loop_triangle.material_index
            material_name = material_slot_index_to_material_name.get(
                material_slot_index
            )
            material_index = None
            if material_name:
                material_index = material_name_to_material_index.get(material_name)
            if material_index is None:
                material_index = self.get_or_write_cluster_empty_material(
                    material_dicts, extensions_vrm_material_property_dicts
                )

            no_morph_normal_export = (
                material_index in no_morph_normal_export_material_indices
            )
            vertex_indices = material_index_to_vertex_indices.get(material_index)
            if vertex_indices is None:
                vertex_indices = bytearray()
                material_index_to_vertex_indices[material_index] = vertex_indices

            for loop_index in loop_triangle.loops:
                loop = main_mesh_data.loops[loop_index]
                original_vertex_index = loop.vertex_index
                vertex_index = self.collect_vertex(
                    obj,
                    main_mesh_data,
                    original_vertex_index,
                    uv_layer,
                    loop_index,
                    vertex_group_index_to_joint,
                    bone_name_to_node_index,
                    skin_joints,
                    shape_key_name_to_mesh_data,
                    shape_key_name_to_vertex_index_to_morph_normal_diffs,
                    vertex_attributes_and_targets,
                    have_skin=have_skin,
                    no_morph_normal_export=no_morph_normal_export,
                )

                vertex_indices.extend(vertex_indices_struct.pack(vertex_index))

        if not material_index_to_vertex_indices:
            return scene_node_index

        node_dict["mesh"] = mesh_index

        primitive_dicts: list[dict[str, Json]] = []

        while len(buffer0) % 4:
            buffer0.append(0)

        # TODO: buffer書き込み用のクラスを独立

        # indicesの書き込み
        for (
            primitive_material_index,
            vertex_indices,
        ) in material_index_to_vertex_indices.items():
            indices_buffer_offset = len(buffer0)
            buffer0.extend(vertex_indices)
            indices_buffer_view_index = len(buffer_view_dicts)
            buffer_view_dicts.append(
                {
                    "buffer": 0,
                    "byteOffset": indices_buffer_offset,
                    "byteLength": len(vertex_indices),
                }
            )
            indices_accessor_index = len(accessor_dicts)
            accessor_dicts.append(
                {
                    "bufferView": indices_buffer_view_index,
                    "byteOffset": 0,
                    "type": "SCALAR",
                    "componentType": GL_UNSIGNED_INT,
                    # TODO: 割り算はミスを誘うので避ける
                    "count": int(len(vertex_indices) / 4),
                }
            )
            primitive_dicts.append(
                {
                    "material": primitive_material_index,
                    "indices": indices_accessor_index,
                }
            )

        # attributesは共有する仕様にした
        primitive_attribute_dict: dict[str, Json] = {}
        for primitive_dict in primitive_dicts:
            primitive_dict["attributes"] = primitive_attribute_dict

        position_buffer_offset = len(buffer0)
        buffer0.extend(vertex_attributes_and_targets.position)
        position_buffer_view_index = len(buffer_view_dicts)
        buffer_view_dicts.append(
            {
                "buffer": 0,
                "byteOffset": position_buffer_offset,
                "byteLength": len(vertex_attributes_and_targets.position),
            }
        )
        position_accessor_index = len(accessor_dicts)

        accessor_dicts.append(
            {
                "bufferView": position_buffer_view_index,
                "byteOffset": 0,
                "type": "VEC3",
                "componentType": GL_FLOAT,
                "count": vertex_attributes_and_targets.count,
                "min": [
                    vertex_attributes_and_targets.position_min_x,
                    vertex_attributes_and_targets.position_min_y,
                    vertex_attributes_and_targets.position_min_z,
                ],
                "max": [
                    vertex_attributes_and_targets.position_max_x,
                    vertex_attributes_and_targets.position_max_y,
                    vertex_attributes_and_targets.position_max_z,
                ],
            }
        )
        primitive_attribute_dict["POSITION"] = position_accessor_index

        normal_buffer_offset = len(buffer0)
        buffer0.extend(vertex_attributes_and_targets.normal)
        normal_buffer_view_index = len(buffer_view_dicts)
        buffer_view_dicts.append(
            {
                "buffer": 0,
                "byteOffset": normal_buffer_offset,
                "byteLength": len(vertex_attributes_and_targets.normal),
            }
        )
        normal_accessor_index = len(accessor_dicts)
        accessor_dicts.append(
            {
                "bufferView": normal_buffer_view_index,
                "byteOffset": 0,
                "type": "VEC3",
                "componentType": GL_FLOAT,
                "count": vertex_attributes_and_targets.count,
                # "normalized": True, # TODO: 要調査
            }
        )
        primitive_attribute_dict["NORMAL"] = normal_accessor_index

        primitive_texcoord = vertex_attributes_and_targets.texcoord
        if primitive_texcoord:
            texcoord_buffer_offset = len(buffer0)
            buffer0.extend(primitive_texcoord)
            texcoord_buffer_view_index = len(buffer_view_dicts)
            buffer_view_dicts.append(
                {
                    "buffer": 0,
                    "byteOffset": texcoord_buffer_offset,
                    "byteLength": len(primitive_texcoord),
                }
            )
            texcoord_accessor_index = len(accessor_dicts)
            accessor_dicts.append(
                {
                    "bufferView": texcoord_buffer_view_index,
                    "byteOffset": 0,
                    "type": "VEC2",
                    "componentType": GL_FLOAT,
                    "count": vertex_attributes_and_targets.count,
                }
            )
            primitive_attribute_dict["TEXCOORD_0"] = texcoord_accessor_index

        primitive_joints = vertex_attributes_and_targets.joints
        if primitive_joints:
            joints_buffer_offset = len(buffer0)
            buffer0.extend(primitive_joints)
            joints_buffer_view_index = len(buffer_view_dicts)
            buffer_view_dicts.append(
                {
                    "buffer": 0,
                    "byteOffset": joints_buffer_offset,
                    "byteLength": len(primitive_joints),
                }
            )
            joints_accessor_index = len(accessor_dicts)
            accessor_dicts.append(
                {
                    "bufferView": joints_buffer_view_index,
                    "byteOffset": 0,
                    "type": "VEC4",
                    "componentType": GL_UNSIGNED_SHORT,
                    "count": vertex_attributes_and_targets.count,
                }
            )
            primitive_attribute_dict["JOINTS_0"] = joints_accessor_index

        primitive_weights = vertex_attributes_and_targets.weights
        if primitive_weights:
            while len(buffer0) % 4:
                buffer0.append(0)

            weights_buffer_offset = len(buffer0)
            buffer0.extend(primitive_weights)
            weights_buffer_view_index = len(buffer_view_dicts)
            buffer_view_dicts.append(
                {
                    "buffer": 0,
                    "byteOffset": weights_buffer_offset,
                    "byteLength": len(primitive_weights),
                }
            )
            weights_accessor_index = len(accessor_dicts)
            accessor_dicts.append(
                {
                    "bufferView": weights_buffer_view_index,
                    "byteOffset": 0,
                    "type": "VEC4",
                    "componentType": GL_FLOAT,
                    "count": vertex_attributes_and_targets.count,
                }
            )
            primitive_attribute_dict["WEIGHTS_0"] = weights_accessor_index

        # targetsは共有する仕様にした
        primitive_targets = vertex_attributes_and_targets.targets
        if primitive_targets:
            while len(buffer0) % 4:
                buffer0.append(0)

            primitive_target_dicts: list[dict[str, Json]] = []
            for target in primitive_targets:
                target_position_buffer_offset = len(buffer0)
                buffer0.extend(target.position)
                target_position_buffer_view_index = len(buffer_view_dicts)
                buffer_view_dicts.append(
                    {
                        "buffer": 0,
                        "byteOffset": target_position_buffer_offset,
                        "byteLength": len(target.position),
                    }
                )
                target_position_accessor_index = len(accessor_dicts)

                accessor_dicts.append(
                    {
                        "bufferView": target_position_buffer_view_index,
                        "byteOffset": 0,
                        "type": "VEC3",
                        "componentType": GL_FLOAT,
                        "count": vertex_attributes_and_targets.count,
                        "min": [
                            target.position_min_x,
                            target.position_min_y,
                            target.position_min_z,
                        ],
                        "max": [
                            target.position_max_x,
                            target.position_max_y,
                            target.position_max_z,
                        ],
                    }
                )

                target_normal_buffer_offset = len(buffer0)
                buffer0.extend(target.normal)
                target_normal_buffer_view_index = len(buffer_view_dicts)
                buffer_view_dicts.append(
                    {
                        "buffer": 0,
                        "byteOffset": target_normal_buffer_offset,
                        "byteLength": len(target.normal),
                    }
                )
                target_normal_accessor_index = len(accessor_dicts)
                accessor_dicts.append(
                    {
                        "bufferView": target_normal_buffer_view_index,
                        "byteOffset": 0,
                        "type": "VEC3",
                        "componentType": GL_FLOAT,
                        "count": vertex_attributes_and_targets.count,
                    }
                )

                primitive_target_dicts.append(
                    {
                        "POSITION": target_position_accessor_index,
                        "NORMAL": target_normal_accessor_index,
                    }
                )

            for primitive_dict in primitive_dicts:
                primitive_dict["targets"] = make_json(primitive_target_dicts)
                primitive_dict["extras"] = {
                    # targetNamesはglTFの仕様には含まれないが、多くの実装で使われている
                    # https://github.com/KhronosGroup/glTF/blob/0251c5c0cce8daec69bd54f29f891e3d0cdb52c8/specification/2.0/Specification.adoc?plain=1#L1500-L1504
                    "targetNames": [target.name for target in primitive_targets]
                }

        mesh_dicts.append(
            {
                "name": original_mesh_convertible.name,
                "primitives": make_json(primitive_dicts),
            }
        )
        mesh_object_name_to_mesh_index[obj.name] = mesh_index
        if skin_dict and have_skin:
            # TODO: メッシュごとに別々のskinを作る
            node_dict["skin"] = len(skin_dicts)
            skin_dicts.append(dict(skin_dict))

        return scene_node_index

    def get_export_parent_object(
        self, obj: Object, mesh_convertible_objects: Sequence[Object]
    ) -> Optional[Object]:
        if obj.parent_type != "OBJECT":
            return None

        parent = obj.parent
        while parent:
            if parent in mesh_convertible_objects:
                return parent
            parent = parent.parent

        return None

    def write_mesh_nodes(
        self,
        progress: Progress,
        node_dicts: list[dict[str, Json]],
        mesh_dicts: list[dict[str, Json]],
        skin_dicts: list[dict[str, Json]],
        material_dicts: list[dict[str, Json]],
        accessor_dicts: list[dict[str, Json]],
        buffer_view_dicts: list[dict[str, Json]],
        extensions_vrm_material_property_dicts: list[Json],
        buffer0: bytearray,
        bone_name_to_node_index: Mapping[str, int],
        mesh_object_name_to_mesh_index: dict[str, int],
        material_name_to_material_index: Mapping[str, int],
        skin_dict: Mapping[str, Json],
        skin_joints: Sequence[int],
    ) -> list[int]:
        object_name_to_node_index: dict[str, int] = {}
        node_indices: list[int] = []

        mesh_convertible_objects = [
            meshe_object
            for meshe_object in self.export_objects
            if meshe_object.type in search.MESH_CONVERTIBLE_OBJECT_TYPES
        ]

        # メッシュを親子関係に従ってソート
        while True:
            swapped = False
            for mesh_object in list(mesh_convertible_objects):
                parent_mesh_object = self.get_export_parent_object(
                    mesh_object, mesh_convertible_objects
                )
                if not parent_mesh_object:
                    continue

                if mesh_convertible_objects.index(
                    mesh_object
                ) < mesh_convertible_objects.index(parent_mesh_object):
                    mesh_convertible_objects.remove(mesh_object)
                    mesh_convertible_objects.append(mesh_object)
                    swapped = True

            if not swapped:
                break

        for obj in self.export_objects:
            node_index = None
            with save_workspace(self.context, obj):
                node_index = self.write_mesh_node(
                    progress,
                    node_dicts,
                    mesh_dicts,
                    skin_dicts,
                    material_dicts,
                    accessor_dicts,
                    buffer_view_dicts,
                    extensions_vrm_material_property_dicts,
                    buffer0,
                    object_name_to_node_index,
                    bone_name_to_node_index,
                    obj,
                    mesh_convertible_objects,
                    mesh_object_name_to_mesh_index,
                    material_name_to_material_index,
                    skin_dict,
                    skin_joints,
                )
            if node_index is None:
                continue
            node_indices.append(node_index)

        return node_indices

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

    @contextmanager
    def clear_shape_key_values(self) -> Iterator[dict[tuple[str, str], float]]:
        mesh_name_and_shape_key_name_to_value: dict[tuple[str, str], float] = {}
        mesh_objs = [obj for obj in self.export_objects if obj.type == "MESH"]
        for mesh_obj in mesh_objs:
            mesh = mesh_obj.data
            if not isinstance(mesh, Mesh):
                continue
            shape_keys = mesh.shape_keys
            if not shape_keys:
                continue
            key_block: Optional[ShapeKey] = None
            for key_block in shape_keys.key_blocks:
                mesh_name_and_shape_key_name_to_value[(mesh.name, key_block.name)] = (
                    key_block.value
                )
                key_block.value = 0
        self.context.view_layer.update()
        try:
            yield mesh_name_and_shape_key_name_to_value
        finally:
            for (
                mesh_name,
                shape_key_name,
            ), value in mesh_name_and_shape_key_name_to_value.items():
                mesh = self.context.blend_data.meshes.get(mesh_name)
                if not mesh:
                    continue
                shape_keys = mesh.shape_keys
                if not shape_keys:
                    continue
                key_block = shape_keys.key_blocks.get(shape_key_name)
                if not key_block:
                    continue
                key_block.value = value

    def get_legacy_shader_images(self, material: Material) -> Sequence[Image]:
        node, legacy_shader_name = search.legacy_shader_node(material)
        if not node or not legacy_shader_name:
            return []

        images: list[Image] = []
        if legacy_shader_name == "MToon_unversioned":
            for (
                raw_input_socket_name
            ) in MtoonUnversioned.texture_kind_exchange_dict.values():
                # Support models that were loaded by earlier versions
                # (1.3.5 or earlier), which had this typo
                #
                # Those models have node.inputs["NomalmapTexture"] instead of
                # "NormalmapTexture". But 'shader_vals' which comes from
                # MaterialMtoon.texture_kind_exchange_dict is "NormalmapTexture".
                # if script reference node.inputs["NormalmapTexture"] in that
                # situation, it will occur error. So change it to "NomalmapTexture"
                # which is typo but points to the same thing in those models.
                if (
                    raw_input_socket_name == "NormalmapTexture"
                    and "NormalmapTexture" not in node.inputs
                    and "NomalmapTexture" in node.inputs
                ):
                    input_socket_name = "NomalmapTexture"
                elif raw_input_socket_name == "ReceiveShadow_Texture":
                    input_socket_name = "ReceiveShadow_Texture_alpha"
                else:
                    input_socket_name = raw_input_socket_name

                input_socket = node.inputs.get(input_socket_name)
                if not input_socket:
                    continue

                image_node = shader.search_input_node(input_socket, ShaderNodeTexImage)
                if not image_node:
                    continue

                image = image_node.image
                if not image:
                    continue

                images.append(image)
        elif legacy_shader_name == "GLTF":
            for input_socket_name in TEXTURE_INPUT_NAMES:
                input_socket = node.inputs.get(input_socket_name)
                if not input_socket:
                    continue

                image_node = shader.search_input_node(input_socket, ShaderNodeTexImage)
                if not image_node:
                    continue

                image = image_node.image
                if not image:
                    continue

                images.append(image)

        elif legacy_shader_name == "TRANSPARENT_ZWRITE":
            input_socket = node.inputs.get("Main_Texture")
            if not input_socket:
                return []

            image_node = shader.search_input_node(input_socket, ShaderNodeTexImage)
            if not image_node:
                return []

            image = image_node.image
            if not image:
                return []

            return [image]

        return list(dict.fromkeys(images).keys())  # 重複削除

    def create_gltf2_io_texture(
        self,
        gltf2_io_texture_info: object,
        texture_dicts: list[dict[str, Json]],
        sampler_dicts: list[dict[str, Json]],
        image_dicts: list[dict[str, Json]],
        buffer_view_dicts: list[dict[str, Json]],
        buffer0: bytearray,
        gltf2_io_texture_images: list[Gltf2IoTextureImage],
    ) -> Json:
        source = getattr(getattr(gltf2_io_texture_info, "index", None), "source", None)
        if not source:
            return None

        source_name = getattr(source, "name", None)
        if not isinstance(source_name, str):
            source_name = ""

        source_mime_type = getattr(source, "mime_type", None)
        if not isinstance(source_mime_type, str):
            source_mime_type = "image/png"

        source_buffer_view_data = getattr(
            getattr(source, "buffer_view", None), "data", None
        )
        if not isinstance(source_buffer_view_data, bytes):
            return None

        export_image_index = None
        for gltf2_io_texture_image in gltf2_io_texture_images:
            if gltf2_io_texture_image.name != source_name:
                continue
            if gltf2_io_texture_image.mime_type != source_mime_type:
                continue
            if gltf2_io_texture_image.image_bytes != source_buffer_view_data:
                continue
            export_image_index = gltf2_io_texture_image.export_image_index
            break

        if export_image_index is None:
            image_base_name = re.sub(
                r"^BlenderVrmAddonImport[0-9]+Image[0-9]+_", "", source_name
            )

            # 旧エクスポーターとの互換性のため、重複した命名を避ける
            image_name = image_base_name
            for count in range(100000):
                if count:
                    image_name = image_base_name + "." + str(count)
                if not any(
                    image_name == image_dict.get("name") for image_dict in image_dicts
                ):
                    break

            image_buffer_view_index = len(buffer_view_dicts)
            buffer_view_dicts.append(
                {
                    "buffer": 0,
                    "byteOffset": len(buffer0),
                    "byteLength": len(source_buffer_view_data),
                }
            )
            buffer0.extend(source_buffer_view_data)

            export_image_index = len(image_dicts)
            image_dict: dict[str, Json] = {
                "name": image_name,
                "mimeType": source_mime_type,
                "bufferView": image_buffer_view_index,
            }
            image_dicts.append(image_dict)

            gltf2_io_texture_images.append(
                Vrm0Exporter.Gltf2IoTextureImage(
                    name=source_name,
                    mime_type=source_mime_type,
                    image_bytes=source_buffer_view_data,
                    export_image_index=export_image_index,
                )
            )

        sampler = getattr(
            getattr(gltf2_io_texture_info, "index", None), "sampler", None
        )
        wrap_s = getattr(sampler, "wrap_s", None)
        wrap_t = getattr(sampler, "wrap_t", None)
        mag_filter = getattr(sampler, "mag_filter", None)
        min_filter = getattr(sampler, "min_filter", None)

        if not isinstance(wrap_s, int):
            wrap_s = GL_REPEAT
        if not isinstance(wrap_t, int):
            wrap_t = GL_REPEAT
        if not isinstance(mag_filter, int):
            mag_filter = GL_LINEAR
        if not isinstance(min_filter, int):
            min_filter = GL_LINEAR

        sampler_dict: dict[str, Json] = {
            "magFilter": mag_filter,
            "minFilter": min_filter,
            "wrapS": wrap_s,
            "wrapT": wrap_t,
        }
        if sampler_dict in sampler_dicts:
            sampler_index = sampler_dicts.index(sampler_dict)
        else:
            sampler_index = len(sampler_dicts)
            sampler_dicts.append(sampler_dict)

        texture_dict: dict[str, Json] = {
            "sampler": sampler_index,
            "source": export_image_index,
        }

        if texture_dict in texture_dicts:
            texture_index = texture_dicts.index(texture_dict)
        else:
            texture_index = len(texture_dicts)
            texture_dicts.append(texture_dict)

        texture_info: dict[str, Json] = {"index": texture_index}

        texture_info_scale = getattr(gltf2_io_texture_info, "scale", None)
        if isinstance(texture_info_scale, (int, float)):
            texture_info["scale"] = texture_info_scale

        texture_info_strength = getattr(gltf2_io_texture_info, "strength", None)
        if isinstance(texture_info_strength, (int, float)):
            texture_info["strength"] = texture_info_strength

        return make_json(texture_info)

    def create_mtoon1_downgraded_texture(
        self,
        texture: Union[Mtoon0TexturePropertyGroup, Mtoon1TexturePropertyGroup],
        texture_properties: dict[str, int],
        texture_properties_key: str,
        vector_properties: dict[str, Sequence[float]],
        texture_dicts: list[dict[str, Json]],
        sampler_dicts: list[dict[str, Json]],
        image_dicts: list[dict[str, Json]],
        buffer_view_dicts: list[dict[str, Json]],
        buffer0: bytearray,
        image_name_to_image_index: dict[str, int],
    ) -> Optional[dict[str, Json]]:
        source = texture.get_connected_node_image()
        if not source:
            return None

        wrap_s = Mtoon1SamplerPropertyGroup.wrap_enum.identifier_to_value(
            texture.sampler.wrap_s,
            Mtoon1SamplerPropertyGroup.WRAP_DEFAULT.value,
        )

        wrap_t = Mtoon1SamplerPropertyGroup.wrap_enum.identifier_to_value(
            texture.sampler.wrap_t,
            Mtoon1SamplerPropertyGroup.WRAP_DEFAULT.value,
        )

        mag_filter = Mtoon1SamplerPropertyGroup.mag_filter_enum.identifier_to_value(
            texture.sampler.mag_filter,
            Mtoon1SamplerPropertyGroup.MAG_FILTER_DEFAULT.value,
        )

        min_filter = Mtoon1SamplerPropertyGroup.min_filter_enum.identifier_to_value(
            texture.sampler.min_filter,
            Mtoon1SamplerPropertyGroup.MIN_FILTER_DEFAULT.value,
        )

        sampler_dict: dict[str, Json] = {
            "magFilter": mag_filter,
            "minFilter": min_filter,
            "wrapS": wrap_s,
            "wrapT": wrap_t,
        }
        if sampler_dict in sampler_dicts:
            sampler_index = sampler_dicts.index(sampler_dict)
        else:
            sampler_index = len(sampler_dicts)
            sampler_dicts.append(sampler_dict)

        image_index = self.find_or_create_image(
            image_dicts,
            buffer_view_dicts,
            buffer0,
            image_name_to_image_index,
            source,
        )

        texture_dict: dict[str, Json] = {
            "sampler": sampler_index,
            "source": image_index,
        }
        if texture_dict in texture_dicts:
            texture_index = texture_dicts.index(texture_dict)
        else:
            texture_index = len(texture_dicts)
            texture_dicts.append(texture_dict)

        texture_properties[texture_properties_key] = texture_index
        vector_properties[texture_properties_key] = [0, 0, 1, 1]

        texture_info: dict[str, Json] = {"index": texture_index}
        return texture_info

    def create_mtoon1_downgraded_texture_info(
        self,
        texture_info: Mtoon1TextureInfoPropertyGroup,
        texture_properties: dict[str, int],
        texture_properties_key: str,
        vector_properties: dict[str, Sequence[float]],
        texture_dicts: list[dict[str, Json]],
        sampler_dicts: list[dict[str, Json]],
        image_dicts: list[dict[str, Json]],
        buffer_view_dicts: list[dict[str, Json]],
        buffer0: bytearray,
        image_name_to_image_index: dict[str, int],
        khr_texture_transform: Optional[Mtoon1KhrTextureTransformPropertyGroup],
    ) -> Optional[dict[str, Json]]:
        texture_info_dict = self.create_mtoon1_downgraded_texture(
            texture_info.index,
            texture_properties,
            texture_properties_key,
            vector_properties,
            texture_dicts,
            sampler_dicts,
            image_dicts,
            buffer_view_dicts,
            buffer0,
            image_name_to_image_index,
        )
        if texture_info_dict is None:
            return None

        if khr_texture_transform is not None:
            texture_info_dict["extensions"] = {
                "KHR_texture_transform": {
                    "offset": list(khr_texture_transform.offset),
                    "scale": list(khr_texture_transform.scale),
                }
            }
        return texture_info_dict

    @staticmethod
    def create_shape_key_name_to_vertex_index_to_morph_normal_diffs(
        context: Context,
        mesh_data: Mesh,
        shape_key_name_to_mesh_data: Mapping[str, Mesh],
        reference_key_name: str,
    ) -> Mapping[str, tuple[tuple[float, float, float], ...]]:
        # logger.error("CREATE UNIQ:")
        # 法線の差分を強制的にゼロにする設定が有効な頂点インデックスを集める
        exclusion_vertex_indices: set[int] = set()
        for polygon in mesh_data.polygons:
            if not (0 <= polygon.material_index < len(mesh_data.materials)):
                continue
            material_ref = mesh_data.materials[polygon.material_index]
            if material_ref is None:
                continue
            # Use non-evaluated material
            material = context.blend_data.materials.get(material_ref.name)
            if material is None:
                continue
            material_extension = get_material_extension(material)
            if material_extension.mtoon1.export_shape_key_normals:
                continue
            if material_extension.mtoon1.enabled:
                exclusion_vertex_indices.update(polygon.vertices)
                continue
            node, legacy_shader_name = search.legacy_shader_node(material)
            if not node:
                continue
            if legacy_shader_name == "MToon_unversioned":
                exclusion_vertex_indices.update(polygon.vertices)

        # logger.error("  exc=%s", exclusion_vertex_indices)

        # logger.error("KEY DIFF:")

        # シェイプキーごとの法線の値を集める
        shape_key_name_to_vertex_normal_vectors: dict[str, list[Vector]] = {}
        for shape_key_name, shape_key_mesh_data in [
            (reference_key_name, mesh_data),
            *shape_key_name_to_mesh_data.items(),
        ]:
            # logger.error("  refkey=%s key=%s", reference_key_name, shape_key_name)
            # 頂点のノーマルではなくsplit(loop)のノーマルを使う
            # https://github.com/KhronosGroup/glTF-Blender-IO/pull/1129
            vertex_normal_sum_vectors = [Vector([0.0, 0.0, 0.0])] * len(
                mesh_data.vertices
            )
            for loop_triangle in shape_key_mesh_data.loop_triangles:
                # logger.error("    loop_triangle mat=%s", loop_triangle.material_index)
                for vertex_index, normal in zip(
                    loop_triangle.vertices, loop_triangle.split_normals
                ):
                    # logger.error(
                    #     "      vindex=%s normal=%s",
                    #     vertex_index,
                    #     normal,
                    # )
                    if vertex_index in exclusion_vertex_indices:
                        # logger.error("      EXCLUDE")
                        continue
                    if not (0 <= vertex_index < len(vertex_normal_sum_vectors)):
                        # logger.error("      OUT OF RANGE")
                        continue
                    vertex_normal_sum_vectors[vertex_index] = (
                        # 普通は += 演算子を使うが、なぜか結果が変わるので使わない
                        vertex_normal_sum_vectors[vertex_index] + Vector(normal)
                    )
                    # logger.error(
                    #     "      => %s:%s",
                    #     vertex_normal_sum_vectors[vertex_index],
                    #     list(vertex_normal_sum_vectors[vertex_index]),
                    # )
            shape_key_name_to_vertex_normal_vectors[shape_key_name] = [
                Vector((0, 0, 0))
                if vector.length_squared < float_info.epsilon
                else vector.normalized()
                for vector in vertex_normal_sum_vectors
            ]

        reference_vertex_normal_vectors = shape_key_name_to_vertex_normal_vectors[
            reference_key_name
        ]

        # シェイプキーごとに、リファレンスキーとの法線の差分を集める
        shape_key_name_to_vertex_index_to_morph_normal_diffs: dict[
            str, tuple[tuple[float, float, float], ...]
        ] = {}

        # logger.error("REFERENCE_KEY: %s", mesh_data.shape_keys.reference_key.name)
        # for v in reference_vertex_normal_vectors:
        #     logger.error("  %s", v)

        # for n, vv in shape_key_name_to_vertex_normal_vectors.items():
        #     logger.error("KEY: %s", n)
        #     for v in vv:
        #         logger.error("  %s", v)

        # logger.error("RESULT:")
        for (
            shape_key_name,
            vertex_normal_vectors,
        ) in shape_key_name_to_vertex_normal_vectors.items():
            if shape_key_name == reference_key_name:
                continue
            vertex_index_to_morph_normal_diffs: tuple[
                tuple[float, float, float], ...
            ] = tuple(
                (
                    vertex_normal_vector.x - reference_vertex_normal_vector.x,
                    vertex_normal_vector.y - reference_vertex_normal_vector.y,
                    vertex_normal_vector.z - reference_vertex_normal_vector.z,
                )
                for vertex_normal_vector, reference_vertex_normal_vector in zip(
                    vertex_normal_vectors,
                    reference_vertex_normal_vectors,
                )
            )
            # logger.error(
            #     "  %s:%s",
            #     shape_key_name,
            #     vertex_index_to_morph_normal_diffs,
            # )
            shape_key_name_to_vertex_index_to_morph_normal_diffs[shape_key_name] = (
                vertex_index_to_morph_normal_diffs
            )
        return shape_key_name_to_vertex_index_to_morph_normal_diffs

    def have_skin(self, mesh: Object) -> bool:
        # TODO: このメソッドは誤判定があるが互換性のためにそのままになっている。
        # 将来的には正しい実装に置き換わる
        while mesh:
            if any(
                modifier.show_viewport and modifier.type == "ARMATURE"
                for modifier in mesh.modifiers
            ):
                return True
            parent_mesh = mesh.parent
            if not parent_mesh:
                return True
            if (
                mesh.parent_type == "BONE"
                and parent_mesh.type == "ARMATURE"
                and mesh.parent_bone
            ):
                return False
            if (
                mesh.parent_type != "OBJECT"
                or parent_mesh.type not in search.MESH_CONVERTIBLE_OBJECT_TYPES
            ):
                return True
            mesh = parent_mesh
        return True

    def get_asset_generator(self) -> str:
        addon_version = get_addon_version()
        if environ.get("BLENDER_VRM_USE_TEST_EXPORTER_VERSION") == "true":
            addon_version = (999, 999, 999)
        return "saturday06_blender_vrm_exporter_experimental_" + ".".join(
            map(str, addon_version)
        )
