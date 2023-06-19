"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import importlib
import math
import re
import statistics
import struct
from collections import abc
from os import environ
from sys import float_info
from typing import Dict, List, Optional, Sequence, Tuple, Union

import bmesh
import bpy
from mathutils import Matrix, Vector

from ..common import convert, deep, shader
from ..common.deep import Json, make_json
from ..common.gl import (
    GL_FLOAT,
    GL_LINEAR,
    GL_LINEAR_MIPMAP_LINEAR,
    GL_LINEAR_MIPMAP_NEAREST,
    GL_NEAREST,
    GL_NEAREST_MIPMAP_LINEAR,
    GL_NEAREST_MIPMAP_NEAREST,
    GL_REPEAT,
    GL_UNSIGNED_INT,
    GL_UNSIGNED_SHORT,
)
from ..common.gltf import (
    FLOAT_NEGATIVE_MAX,
    FLOAT_POSITIVE_MAX,
    TEXTURE_INPUT_NAMES,
    pack_glb,
)
from ..common.logging import get_logger
from ..common.mtoon_unversioned import MtoonUnversioned
from ..common.version import addon_version
from ..common.vrm0.human_bone import HumanBoneSpecifications
from ..editor import migration, search
from ..editor.mtoon1.property_group import (
    Mtoon0TexturePropertyGroup,
    Mtoon1KhrTextureTransformPropertyGroup,
    Mtoon1SamplerPropertyGroup,
    Mtoon1TextureInfoPropertyGroup,
    Mtoon1TexturePropertyGroup,
)
from ..external import io_scene_gltf2_support
from .abstract_base_vrm_exporter import AbstractBaseVrmExporter, assign_dict
from .glb_bin_collection import GlbBin, GlbBinCollection, ImageBin

logger = get_logger(__name__)


class LegacyVrmExporter(AbstractBaseVrmExporter):
    class KhrTextureTransform:
        def __init__(self, offset: Tuple[float, float], scale: Tuple[float, float]):
            self.offset = offset
            self.scale = scale

        def add_to(self, texture_info: Dict[str, Json]) -> None:
            texture_info.update(
                {
                    "extensions": {
                        "KHR_texture_transform": {
                            "scale": list(self.scale),
                            "offset": list(self.offset),
                        }
                    }
                }
            )

    def __init__(
        self,
        context: bpy.types.Context,
        export_objects: List[bpy.types.Object],
        export_fb_ngon_encoding: bool,
    ) -> None:
        super().__init__(context)
        self.export_objects = export_objects
        self.export_fb_ngon_encoding = export_fb_ngon_encoding
        self.json_dict: Dict[str, Json] = {}
        self.glb_bin_collector = GlbBinCollection()
        self.use_dummy_armature = False
        self.mesh_name_to_index: Dict[str, int] = {}
        self.outline_modifier_visibilities: Dict[str, Dict[str, Tuple[bool, bool]]] = {}
        armatures = [obj for obj in self.export_objects if obj.type == "ARMATURE"]
        if armatures:
            self.armature = armatures[0]
        else:
            dummy_armature_key = self.export_id + "DummyArmatureKey"
            bpy.ops.icyp.make_basic_armature(
                "EXEC_DEFAULT", custom_property_name=dummy_armature_key
            )
            for obj in self.context.selectable_objects:
                if obj.type == "ARMATURE" and dummy_armature_key in obj:
                    self.export_objects.append(obj)
                    self.armature = obj
            if not self.armature:
                raise RuntimeError("Failed to generate default armature")
            self.use_dummy_armature = True
        migration.migrate(self.armature.name, defer=False)

        self.result: Optional[bytes] = None

    def export_vrm(self) -> Optional[bytes]:
        wm = self.context.window_manager
        wm.progress_begin(0, 11)
        object_name_and_modifier_names = self.hide_mtoon1_outline_geometry_nodes()
        try:
            self.setup_pose(
                self.armature,
                self.armature.data.vrm_addon_extension.vrm0.humanoid.pose_library,
                self.armature.data.vrm_addon_extension.vrm0.humanoid.pose_marker_name,
            )
            wm.progress_update(1)
            self.image_to_bin()
            wm.progress_update(2)
            self.armature_to_node_and_scenes_dict()
            wm.progress_update(3)
            self.material_to_dict()
            wm.progress_update(4)
            self.hide_outline_modifiers()
            wm.progress_update(5)
            self.mesh_to_bin_and_dict()
            wm.progress_update(6)
            self.restore_outline_modifiers()
            wm.progress_update(7)
            self.json_dict["scene"] = 0
            self.gltf_meta_to_dict()
            wm.progress_update(8)
            self.vrm_meta_to_dict()  # colliderとかmetaとか....
            wm.progress_update(9)
            self.fill_empty_material()
            wm.progress_update(10)
            self.pack()
        finally:
            try:
                self.restore_pose(self.armature)
                self.restore_mtoon1_outline_geometry_nodes(
                    object_name_and_modifier_names
                )
                self.cleanup()
            finally:
                wm.progress_end()
        return self.result

    @staticmethod
    def axis_blender_to_glb(vec3: Sequence[float]) -> List[float]:
        return [vec3[i] * t for i, t in zip([0, 2, 1], [-1, 1, 1])]

    def hide_outline_modifiers(self) -> None:
        for obj in self.export_objects:
            if obj.type not in search.MESH_CONVERTIBLE_OBJECT_TYPES:
                continue

            modifier_dict: Dict[str, Tuple[bool, bool]] = {}
            for modifier in obj.modifiers:
                if (
                    not modifier
                    or modifier.type != "NODES"
                    or not modifier.node_group
                    or modifier.node_group.name != shader.OUTLINE_GEOMETRY_GROUP_NAME
                ):
                    continue
                modifier_dict[modifier.name] = (
                    modifier.show_render,
                    modifier.show_viewport,
                )
                modifier.show_render = False
                modifier.show_viewport = False
            self.outline_modifier_visibilities[obj.name] = modifier_dict

    def restore_outline_modifiers(self) -> None:
        for object_name, modifier_dict in self.outline_modifier_visibilities.items():
            obj = bpy.data.objects.get(object_name)
            if (
                not obj
                or obj not in self.export_objects
                or obj.type not in search.MESH_CONVERTIBLE_OBJECT_TYPES
            ):
                continue

            for modifier_name, (show_render, show_viewport) in modifier_dict.items():
                modifier = obj.modifiers.get(modifier_name)
                if (
                    not modifier
                    or modifier.type != "NODES"
                    or not modifier.node_group
                    or modifier.node_group.name != shader.OUTLINE_GEOMETRY_GROUP_NAME
                ):
                    continue
                modifier.show_render = show_render
                modifier.show_viewport = show_viewport

    def image_to_bin(self) -> None:
        # collect used image
        used_images = []
        used_materials = search.export_materials(self.export_objects)
        for mat in used_materials:
            if "vrm_shader" in mat:
                del mat["vrm_shader"]

        # image fetching
        for node, mat in search.shader_nodes_and_materials(used_materials):
            if node.node_tree["SHADER"] == "MToon_unversioned":
                mat["vrm_shader"] = "MToon_unversioned"
                for shader_vals in MtoonUnversioned.texture_kind_exchange_dict.values():
                    # Support models that were loaded by earlier versions (1.3.5 or earlier), which had this typo
                    #
                    # Those models have node.inputs["NomalmapTexture"] instead of "NormalmapTexture".  # noqa: SC100
                    # But 'shader_vals' which comes from MaterialMtoon.texture_kind_exchange_dict is "NormalmapTexture".
                    # if script reference node.inputs["NormalmapTexture"] in that situation, it will occur error.
                    # So change it to "NomalmapTexture" which is typo but points to the same thing  # noqa: SC100
                    # in those models.
                    if (
                        shader_vals == "NormalmapTexture"
                        and "NormalmapTexture" not in node.inputs
                        and "NomalmapTexture" in node.inputs
                    ):
                        shader_vals = "NomalmapTexture"

                    if shader_vals == "ReceiveShadow_Texture":
                        if node.inputs[shader_vals + "_alpha"].links:
                            n = node.inputs[shader_vals + "_alpha"].links[0].from_node
                            if n.image not in used_images:
                                used_images.append(n.image)
                    elif node.inputs[shader_vals].links:
                        n = node.inputs[shader_vals].links[0].from_node
                        if n.image not in used_images:
                            used_images.append(n.image)
            elif node.node_tree["SHADER"] == "GLTF":
                mat["vrm_shader"] = "GLTF"
                for k in TEXTURE_INPUT_NAMES:
                    if node.inputs[k].links:
                        n = node.inputs[k].links[0].from_node
                        if n.image not in used_images:
                            used_images.append(n.image)

            elif node.node_tree["SHADER"] == "TRANSPARENT_ZWRITE":
                mat["vrm_shader"] = "TRANSPARENT_ZWRITE"
                if node.inputs["Main_Texture"].links:
                    n = node.inputs["Main_Texture"].links[0].from_node
                    if n.image not in used_images:
                        used_images.append(n.image)
            else:
                # ?
                pass

        # MToon 1.0 downgraded
        for mat in used_materials:
            if not mat.vrm_addon_extension.mtoon1.enabled:
                continue
            for texture in mat.vrm_addon_extension.mtoon1.all_textures(
                downgrade_to_mtoon0=True
            ):
                source = texture.source
                if source and source not in used_images:
                    used_images.append(source)

        # thumbnail
        ext = self.armature.data.vrm_addon_extension
        if (
            ext.vrm0.meta.texture
            and ext.vrm0.meta.texture.name
            and ext.vrm0.meta.texture not in used_images
        ):
            used_images.append(ext.vrm0.meta.texture)

        for image in used_images:
            image_bin, filetype = io_scene_gltf2_support.image_to_image_bytes(
                image, self.gltf2_addon_export_settings
            )
            ImageBin(image_bin, image.name, filetype, self.glb_bin_collector)

    def armature_to_node_and_scenes_dict(self) -> None:
        node_dicts: List[Json] = []
        scene_nodes: List[Json] = []
        skin_dicts: List[Json] = []

        bone_id_dict = {
            b.name: bone_id for bone_id, b in enumerate(self.armature.pose.bones)
        }

        def bone_to_node(b_bone: bpy.types.PoseBone) -> Dict[str, Json]:
            if b_bone.parent is not None:
                world_head = (
                    self.armature.matrix_world @ Matrix.Translation(b_bone.head)
                ).to_translation()
                parent_world_head = (
                    self.armature.matrix_world @ Matrix.Translation(b_bone.parent.head)
                ).to_translation()
                translation = [world_head[i] - parent_world_head[i] for i in range(3)]
            else:
                translation = (
                    self.armature.matrix_world @ b_bone.matrix
                ).to_translation()
            node = {
                "name": b_bone.name,
                "translation": self.axis_blender_to_glb(translation),
                # "rotation":[0,0,0,1],
                # "scale":[1,1,1],
                "children": [bone_id_dict[ch.name] for ch in b_bone.children],
            }
            if not node["children"]:
                del node["children"]
            return node

        human_bone_node_names = [
            human_bone.node.bone_name
            for human_bone in self.armature.data.vrm_addon_extension.vrm0.humanoid.human_bones
        ]

        for bone in self.armature.pose.bones:
            if bone.parent is not None:
                continue

            has_human_bone = False
            if bone.name in human_bone_node_names:
                has_human_bone = True
            joints: Json = None
            joints = []
            skin_dict: Json = None
            skin_dict = {"joints": joints}
            root_bone_id = bone_id_dict[bone.name]
            joints.append(root_bone_id)
            skin_dict["skeleton"] = root_bone_id
            scene_nodes.append(root_bone_id)
            node_dicts.append(bone_to_node(bone))
            bone_children = list(bone.children)
            while bone_children:
                child = bone_children.pop()
                if child.name in human_bone_node_names:
                    has_human_bone = True
                node_dicts.append(bone_to_node(child))
                joints.append(bone_id_dict[child.name])
                bone_children.extend(list(child.children))
            node_dicts = sorted(
                node_dicts,
                key=lambda node_dict: bone_id_dict.get(
                    node_dict.get("name"), pow(2, 31)
                )
                if isinstance(node_dict, dict)
                else pow(2, 31),
            )
            if has_human_bone:
                skin_dicts.append(skin_dict)

        for skin_dict in skin_dicts:
            if not isinstance(skin_dict, dict):
                continue
            skin_invert_matrix_bin = bytearray()
            f_4x4_packer = struct.Struct("<16f").pack
            joints = skin_dict.get("joints")
            if not isinstance(joints, list):
                joints = []
                skin_dict["joints"] = joints
            for node_id in joints:
                if not isinstance(node_id, int) or not 0 <= node_id < len(node_dicts):
                    continue
                node = node_dicts[node_id]
                if not isinstance(node, dict):
                    continue
                bone_name = node.get("name")
                if not bone_name:
                    continue
                bone_glb_world_pos = self.axis_blender_to_glb(
                    (
                        self.armature.matrix_world
                        @ Matrix.Translation(self.armature.pose.bones[bone_name].head)
                    ).to_translation()
                )
                inv_matrix = [
                    1,
                    0,
                    0,
                    0,
                    0,
                    1,
                    0,
                    0,
                    0,
                    0,
                    1,
                    0,
                    -bone_glb_world_pos[0],
                    -bone_glb_world_pos[1],
                    -bone_glb_world_pos[2],
                    1,
                ]
                skin_invert_matrix_bin.extend(f_4x4_packer(*inv_matrix))

            im_bin = GlbBin(
                skin_invert_matrix_bin,
                "MAT4",
                GL_FLOAT,
                len(joints),
                None,
                self.glb_bin_collector,
            )
            skin_dict["inverseBindMatrices"] = im_bin.accessor_id

        self.json_dict.update({"scenes": [{"nodes": scene_nodes}]})
        self.json_dict.update({"nodes": node_dicts})
        self.json_dict.update({"skins": skin_dicts})

    def material_to_dict(self) -> None:
        glb_material_list: List[Json] = []
        vrm_material_props_list: List[Json] = []
        gltf2_io_texture_images: List[Tuple[str, bytes, int]] = []

        image_id_dict = {
            image.name: image.image_id for image in self.glb_bin_collector.image_bins
        }
        sampler_dict: Dict[Tuple[int, int, int, int], int] = {}
        texture_dict: Dict[Tuple[int, int], int] = {}

        # texture func
        def add_texture(
            image_name: str,
            wrap_s_type: int,
            mag_filter_type: int,
            wrap_t_type: Optional[int] = None,
            min_filter_type: Optional[int] = None,
        ) -> int:
            if wrap_t_type is None:
                wrap_t_type = wrap_s_type
            if min_filter_type is None:
                min_filter_type = mag_filter_type
            sampler_dict_key = (
                wrap_s_type,
                wrap_t_type,
                mag_filter_type,
                min_filter_type,
            )
            if sampler_dict_key not in sampler_dict:
                sampler_dict.update({sampler_dict_key: len(sampler_dict)})
            if (
                image_id_dict[image_name],
                sampler_dict[sampler_dict_key],
            ) not in texture_dict:
                texture_dict.update(
                    {
                        (
                            image_id_dict[image_name],
                            sampler_dict[sampler_dict_key],
                        ): len(texture_dict)
                    }
                )
            return texture_dict[
                (image_id_dict[image_name], sampler_dict[sampler_dict_key])
            ]

        def apply_texture_and_sampler_to_dict() -> None:
            if sampler_dict:
                self.json_dict["samplers"] = [
                    {
                        "wrapS": sampler[0],
                        "wrapT": sampler[1],
                        "magFilter": sampler[2],
                        "minFilter": sampler[3],
                    }
                    for sampler in sampler_dict
                ]
            if texture_dict:
                self.json_dict["textures"] = [
                    {
                        "sampler": tex[1],
                        "source": tex[0],
                    }
                    for tex in texture_dict
                ]

        # function separate by shader
        def pbr_fallback(
            b_mat: bpy.types.Material,
            base_color: Optional[Sequence[float]] = None,
            metalness: Optional[float] = None,
            roughness: Optional[float] = None,
            base_color_texture: Optional[Tuple[str, int, int]] = None,
            metallic_roughness_texture: Optional[Tuple[str, int, int]] = None,
            normal_texture: Optional[Tuple[str, int, int]] = None,
            normal_texture_scale: Optional[float] = None,
            occlusion_texture: Optional[Tuple[str, int, int]] = None,
            emissive_texture: Optional[Tuple[str, int, int]] = None,
            transparent_method: str = "OPAQUE",
            transparency_cutoff: Optional[float] = 0.5,
            unlit: Optional[bool] = None,
            double_sided: bool = False,
            texture_transform: Optional[LegacyVrmExporter.KhrTextureTransform] = None,
        ) -> Dict[str, Json]:
            """transparent_method = {"OPAQUE","MASK","BLEND"}"""
            if base_color is None:
                base_color = (1, 1, 1, 1)
            base_color = tuple(map(lambda v: max(0, min(1, v)), base_color))
            if metalness is None:
                metalness = 0
            metalness = max(0, min(1, metalness))
            if roughness is None:
                roughness = 0.9
            roughness = max(0, min(1, roughness))
            if unlit is None:
                unlit = True
            fallback_dict = {
                "name": b_mat.name,
                "pbrMetallicRoughness": {
                    "baseColorFactor": base_color,
                    "metallicFactor": metalness,
                    "roughnessFactor": roughness,
                },
            }
            for k, v in fallback_dict["pbrMetallicRoughness"].items():
                if v is None:
                    del fallback_dict["pbrMetallicRoughness"][k]

            if base_color_texture is not None:
                texture_info: Dict[str, Json] = {
                    "index": add_texture(*base_color_texture),
                    "texCoord": 0,
                }
                if texture_transform is not None:
                    texture_transform.add_to(texture_info)
                fallback_dict["pbrMetallicRoughness"].update(
                    {"baseColorTexture": texture_info}  # TODO:
                )
            if metallic_roughness_texture is not None:
                texture_info = {
                    "index": add_texture(*metallic_roughness_texture),
                    "texCoord": 0,  # TODO:
                }
                if texture_transform is not None:
                    texture_transform.add_to(texture_info)
                fallback_dict["pbrMetallicRoughness"].update(
                    {"metallicRoughnessTexture": texture_info}
                )
            if normal_texture is not None:
                normal_texture_info: Dict[str, Json] = {
                    "index": add_texture(*normal_texture),
                    "texCoord": 0,  # TODO:
                }
                if normal_texture_scale is not None:
                    normal_texture_info["scale"] = normal_texture_scale
                if texture_transform is not None:
                    texture_transform.add_to(normal_texture_info)
                fallback_dict["normalTexture"] = normal_texture_info
            if occlusion_texture is not None:
                occlusion_texture_info: Dict[str, Json] = {
                    "index": add_texture(*occlusion_texture),
                    "texCoord": 0,  # TODO:
                }
                if texture_transform is not None:
                    texture_transform.add_to(occlusion_texture_info)
                fallback_dict["occlusionTexture"] = occlusion_texture_info
            if emissive_texture is not None:
                emissive_texture_info: Dict[str, Json] = {
                    "index": add_texture(*emissive_texture),
                    "texCoord": 0,  # TODO:
                }
                if texture_transform is not None:
                    texture_transform.add_to(emissive_texture_info)
                fallback_dict["emissiveTexture"] = emissive_texture_info

            fallback_dict["alphaMode"] = transparent_method
            if transparent_method == "MASK":
                fallback_dict["alphaCutoff"] = (
                    0.5 if transparency_cutoff is None else transparency_cutoff
                )
            if unlit:
                fallback_dict["extensions"] = {"KHR_materials_unlit": {}}
            fallback_dict["doubleSided"] = double_sided
            return fallback_dict

        def set_mtoon_outline_keywords(
            keyword_map: Dict[str, bool],
            width_world: bool,
            width_screen: bool,
            color_fixed: bool,
            color_mixed: bool,
        ) -> None:
            if width_world:
                keyword_map["MTOON_OUTLINE_WIDTH_WORLD"] = width_world
            elif width_screen:
                keyword_map["MTOON_OUTLINE_WIDTH_SCREEN"] = width_screen
            if color_fixed:
                keyword_map["MTOON_OUTLINE_COLOR_FIXED"] = color_fixed
            elif color_mixed:
                keyword_map["MTOON_OUTLINE_COLOR_MIXED"] = color_mixed

        def make_mtoon_unversioned_extension_dict(
            b_mat: bpy.types.Material, mtoon_shader_node: bpy.types.Node
        ) -> Tuple[Dict[str, Json], Dict[str, Json]]:
            mtoon_dict: Dict[str, Json] = {}
            mtoon_dict["name"] = b_mat.name
            mtoon_dict["shader"] = "VRM/MToon"

            keyword_map: Dict[str, bool] = {}
            tag_map: Dict[str, str] = {}
            mtoon_float_dict: Dict[str, float] = {}
            mtoon_vector_dict: Dict[str, Sequence[float]] = {}
            mtoon_texture_dict: Dict[str, int] = {}

            outline_width_mode = 0
            outline_color_mode = 0
            for float_key, float_prop in [
                (k, val)
                for k, val in MtoonUnversioned.float_props_exchange_dict.items()
                if val is not None
            ]:
                float_val = shader.get_float_value(mtoon_shader_node, float_prop)
                if float_val is not None:
                    mtoon_float_dict[float_key] = float_val
                    if float_key == "_OutlineWidthMode":
                        outline_width_mode = min(max(round(float_val), 0), 2)
                        mtoon_float_dict[float_key] = int(outline_width_mode)
                    if float_key == "_OutlineColorMode":
                        outline_color_mode = min(max(round(float_val), 0), 1)
                        mtoon_float_dict[float_key] = int(outline_color_mode)

            if outline_width_mode < 1:
                set_mtoon_outline_keywords(keyword_map, False, False, False, False)
            elif outline_width_mode < 2:
                if outline_color_mode < 1:
                    set_mtoon_outline_keywords(keyword_map, True, False, True, False)
                else:
                    set_mtoon_outline_keywords(keyword_map, True, False, False, True)

            elif outline_width_mode >= 2:
                if outline_color_mode < 1:
                    set_mtoon_outline_keywords(keyword_map, False, True, True, False)
                else:
                    set_mtoon_outline_keywords(keyword_map, False, True, False, True)

            vec_props = list(
                dict.fromkeys(MtoonUnversioned.vector_props_exchange_dict.values())
            )
            for remove_vec_prop in MtoonUnversioned.texture_kind_exchange_dict.values():
                if remove_vec_prop in vec_props:
                    vec_props.remove(remove_vec_prop)

            for vector_key, vector_prop in [
                (k, v)
                for k, v in MtoonUnversioned.vector_props_exchange_dict.items()
                if v in vec_props
            ]:
                vector_val = shader.get_rgba_value(mtoon_shader_node, vector_prop)
                if vector_val is not None:
                    mtoon_vector_dict[vector_key] = vector_val

            use_normalmap = False
            main_texture: Optional[Tuple[str, int, int]] = None
            main_texture_transform: Optional[
                LegacyVrmExporter.KhrTextureTransform
            ] = None
            normal_texture: Optional[Tuple[str, int, int]] = None
            emissive_texture: Optional[Tuple[str, int, int]] = None

            for (
                texture_key,
                texture_prop,
            ) in MtoonUnversioned.texture_kind_exchange_dict.items():
                tex = shader.get_image_name_and_sampler_type(
                    mtoon_shader_node, texture_prop
                )
                if tex is None:
                    continue

                mtoon_texture_dict[texture_key] = add_texture(*tex)
                mtoon_vector_dict[texture_key] = [0, 0, 1, 1]
                if texture_prop == "MainTexture":
                    main_texture = tex
                    uv_offset_scaling_node = None
                    try:
                        uv_offset_scaling_node = (
                            mtoon_shader_node.inputs[texture_prop]
                            .links[0]
                            .from_node.inputs[0]
                            .links[0]
                            .from_node
                        )
                    except IndexError:
                        uv_offset_scaling_node = None
                    if (
                        uv_offset_scaling_node is not None
                        and uv_offset_scaling_node.type == "MAPPING'"
                    ):
                        mtoon_vector_dict[texture_key] = [
                            uv_offset_scaling_node.inputs["Location"].default_value[0],
                            uv_offset_scaling_node.inputs["Location"].default_value[1],
                            uv_offset_scaling_node.inputs["Scale"].default_value[0],
                            uv_offset_scaling_node.inputs["Scale"].default_value[1],
                        ]
                    else:
                        mtoon_vector_dict[texture_key] = [0, 0, 1, 1]
                    main_texture_transform = LegacyVrmExporter.KhrTextureTransform(
                        offset=(
                            mtoon_vector_dict[texture_key][0],
                            mtoon_vector_dict[texture_key][1],
                        ),
                        scale=(
                            mtoon_vector_dict[texture_key][2],
                            mtoon_vector_dict[texture_key][3],
                        ),
                    )
                elif (
                    # Support older version that had typo
                    texture_prop
                    in ["NormalmapTexture", "NomalmapTexture"]
                ):
                    use_normalmap = True
                    normal_texture = tex
                elif texture_prop == "Emission_Texture":
                    emissive_texture = tex

            def material_prop_setter(
                blend_mode: int,
                src_blend: int,
                dst_blend: int,
                z_write: int,
                alphatest: bool,
                render_queue: int,
                render_type: str,
            ) -> None:
                mtoon_float_dict["_BlendMode"] = blend_mode
                mtoon_float_dict["_SrcBlend"] = src_blend
                mtoon_float_dict["_DstBlend"] = dst_blend
                mtoon_float_dict["_ZWrite"] = z_write
                if alphatest:
                    keyword_map.update({"_ALPHATEST_ON": alphatest})
                mtoon_dict["renderQueue"] = render_queue
                tag_map["RenderType"] = render_type

            if b_mat.blend_method == "OPAQUE":
                material_prop_setter(0, 1, 0, 1, False, -1, "Opaque")
            elif b_mat.blend_method == "CLIP":
                material_prop_setter(1, 1, 0, 1, True, 2450, "TransparentCutout")
                mtoon_float_dict["_Cutoff"] = b_mat.alpha_threshold
            else:  # transparent and Z_TRANSPARENCY or Raytrace
                transparent_with_z_write = shader.get_float_value(
                    mtoon_shader_node, "TransparentWithZWrite"
                )
                if (
                    not isinstance(transparent_with_z_write, (float, int))
                    or math.fabs(transparent_with_z_write) < float_info.epsilon
                ):
                    material_prop_setter(2, 5, 10, 0, False, 3000, "Transparent")
                else:
                    material_prop_setter(3, 5, 10, 1, False, 2501, "Transparent")
            keyword_map.update(
                {"_ALPHABLEND_ON": b_mat.blend_method not in ("OPAQUE", "CLIP")}
            )
            keyword_map.update({"_ALPHAPREMULTIPLY_ON": False})

            mtoon_float_dict["_MToonVersion"] = MtoonUnversioned.version
            mtoon_float_dict["_CullMode"] = (
                2 if b_mat.use_backface_culling else 0
            )  # no cull or bf cull
            mtoon_float_dict[
                "_OutlineCullMode"
            ] = 1  # front face cull (for invert normal outline)
            mtoon_float_dict["_DebugMode"] = 0
            keyword_map.update({"MTOON_DEBUG_NORMAL": False})
            keyword_map.update({"MTOON_DEBUG_LITSHADERATE": False})
            if use_normalmap:
                keyword_map.update({"_NORMALMAP": use_normalmap})

            # for pbr_fallback
            if b_mat.blend_method == "OPAQUE":
                transparent_method = "OPAQUE"
                transparency_cutoff = None
            elif b_mat.blend_method == "CLIP":
                transparent_method = "MASK"
                transparency_cutoff = b_mat.alpha_threshold
            else:
                transparent_method = "BLEND"
                transparency_cutoff = None
            pbr_dict = pbr_fallback(
                b_mat,
                base_color=mtoon_vector_dict.get("_Color"),
                base_color_texture=main_texture,
                normal_texture=normal_texture,
                normal_texture_scale=mtoon_float_dict.get("_BumpScale"),
                emissive_texture=emissive_texture,
                transparent_method=transparent_method,
                transparency_cutoff=transparency_cutoff,
                double_sided=not b_mat.use_backface_culling,
                texture_transform=main_texture_transform,
            )

            mtoon_dict.update(
                {
                    "keywordMap": make_json(keyword_map),
                    "tagMap": make_json(tag_map),
                    "floatProperties": make_json(mtoon_float_dict),
                    "vectorProperties": make_json(mtoon_vector_dict),
                    "textureProperties": make_json(mtoon_texture_dict),
                }
            )

            return mtoon_dict, pbr_dict

        def make_gltf_mat_dict(
            b_mat: bpy.types.Material, gltf_shader_node: bpy.types.Node
        ) -> Tuple[Dict[str, Json], Dict[str, Json]]:
            gltf_dict = {}
            gltf_dict["name"] = b_mat.name
            gltf_dict["shader"] = "VRM_USE_GLTFSHADER"
            gltf_dict["keywordMap"] = {}
            gltf_dict["tagMap"] = {}
            gltf_dict["floatProperties"] = {}
            gltf_dict["vectorProperties"] = {}
            gltf_dict["textureProperties"] = {}
            gltf_dict["extras"] = {"VRM_Addon_for_Blender_legacy_gltf_material": {}}

            if b_mat.blend_method == "OPAQUE":
                transparent_method = "OPAQUE"
                transparency_cutoff = None
            elif b_mat.blend_method == "CLIP":
                transparent_method = "MASK"
                transparency_cutoff = b_mat.alpha_threshold
            else:
                transparent_method = "BLEND"
                transparency_cutoff = None

            unlit_value = shader.get_float_value(gltf_shader_node, "unlit")
            if unlit_value is None:
                unlit = None
            else:
                unlit = unlit_value > 0.5
            pbr_dict = pbr_fallback(
                b_mat,
                base_color=shader.get_rgba_value(
                    gltf_shader_node, "base_Color", 0.0, 1.0
                ),
                metalness=shader.get_float_value(
                    gltf_shader_node, "metallic", 0.0, 1.0
                ),
                roughness=shader.get_float_value(
                    gltf_shader_node, "roughness", 0.0, 1.0
                ),
                base_color_texture=shader.get_image_name_and_sampler_type(
                    gltf_shader_node, "color_texture"
                ),
                metallic_roughness_texture=shader.get_image_name_and_sampler_type(
                    gltf_shader_node, "metallic_roughness_texture"
                ),
                transparent_method=transparent_method,
                transparency_cutoff=transparency_cutoff,
                unlit=unlit,
                double_sided=not b_mat.use_backface_culling,
            )

            def pbr_tex_add(texture_type: str, socket_name: str) -> None:
                img = shader.get_image_name_and_sampler_type(
                    gltf_shader_node, socket_name
                )
                if img is not None:
                    pbr_dict[texture_type] = {"index": add_texture(*img), "texCoord": 0}
                else:
                    logger.warning(f"No image: {socket_name}")

            pbr_tex_add("normalTexture", "normal")
            pbr_tex_add("emissiveTexture", "emissive_texture")
            pbr_tex_add("occlusionTexture", "occlusion_texture")
            emissive_factor = shader.get_rgb_value(
                gltf_shader_node, "emissive_color", 0.0, 1.0
            )
            if emissive_factor is None:
                emissive_factor = (0, 0, 0)
            pbr_dict["emissiveFactor"] = list(emissive_factor)

            return gltf_dict, pbr_dict

        def make_transzw_mat_dict(
            b_mat: bpy.types.Material, transzw_shader_node: bpy.types.Node
        ) -> Tuple[Dict[str, Json], Dict[str, Json]]:
            zw_dict = {}
            zw_dict["name"] = b_mat.name
            zw_dict["shader"] = "VRM/UnlitTransparentZWrite"
            zw_dict["renderQueue"] = 2600
            zw_dict["keywordMap"] = {}
            zw_dict["tagMap"] = {"RenderType": "Transparent"}
            zw_dict["floatProperties"] = {}
            zw_dict["vectorProperties"] = {}
            zw_dict["textureProperties"] = {}
            color_tex = shader.get_image_name_and_sampler_type(
                transzw_shader_node, "Main_Texture"
            )
            if color_tex is not None:
                zw_dict["textureProperties"] = {"_MainTex": add_texture(*color_tex)}
                zw_dict["vectorProperties"] = {"_MainTex": [0, 0, 1, 1]}
            pbr_dict = pbr_fallback(
                b_mat, base_color_texture=color_tex, transparent_method="BLEND"
            )

            return zw_dict, pbr_dict

        def add_gltf2_io_texture(
            gltf2_io_texture_info: object,
        ) -> Json:
            source = getattr(
                getattr(gltf2_io_texture_info, "index", None), "source", None
            )
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
                source_buffer_view_data = bytes()

            image_index = None
            for name, data, index in gltf2_io_texture_images:
                if name != source_name or data != source_buffer_view_data:
                    continue
                image_index = index
                break
            if image_index is None:
                image_index = self.glb_bin_collector.get_new_image_id()
                gltf2_io_texture_images.append(
                    (source_name, source_buffer_view_data, image_index)
                )
                image_base_name = re.sub(
                    r"^BlenderVrmAddonImport[0-9]+Image[0-9]+_", "", source_name
                )
                image_name = image_base_name
                for count in range(100000):
                    if count:
                        image_name = image_base_name + "." + str(count)
                    if image_name not in image_id_dict:
                        break
                image_id_dict[image_name] = image_index
                ImageBin(
                    source_buffer_view_data,
                    image_name,
                    source_mime_type,
                    self.glb_bin_collector,
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

            # VRoid Hub may not support a mipmap
            if min_filter in [
                GL_NEAREST_MIPMAP_LINEAR,
                GL_NEAREST_MIPMAP_NEAREST,
            ]:
                min_filter = GL_NEAREST
            elif min_filter in [
                GL_LINEAR_MIPMAP_NEAREST,
                GL_LINEAR_MIPMAP_LINEAR,
            ]:
                min_filter = GL_LINEAR

            sampler_dict_key = (
                wrap_s,
                wrap_t,
                mag_filter,
                min_filter,
            )

            if sampler_dict_key not in sampler_dict:
                sampler_dict.update({sampler_dict_key: len(sampler_dict)})
            if (image_index, sampler_dict[sampler_dict_key]) not in texture_dict:
                texture_dict.update(
                    {(image_index, sampler_dict[sampler_dict_key]): len(texture_dict)}
                )
            texture_info: Dict[str, Union[int, float]] = {
                "index": texture_dict[(image_index, sampler_dict[sampler_dict_key])],
                "texCoord": 0,  # TODO
            }
            if hasattr(gltf2_io_texture_info, "scale") and isinstance(
                gltf2_io_texture_info.scale, (int, float)
            ):
                texture_info["scale"] = gltf2_io_texture_info.scale
            if hasattr(gltf2_io_texture_info, "strength") and isinstance(
                gltf2_io_texture_info.strength, (int, float)
            ):
                texture_info["strength"] = gltf2_io_texture_info.strength
            return make_json(texture_info)

        def make_non_vrm_mat_dict(
            b_mat: bpy.types.Material,
        ) -> Tuple[Dict[str, Json], Dict[str, Json]]:
            vrm_dict: Dict[str, Json] = {
                "name": b_mat.name,
                "shader": "VRM_USE_GLTFSHADER",
                "keywordMap": {},
                "tagMap": {},
                "floatProperties": {},
                "vectorProperties": {},
                "textureProperties": {},
            }
            fallback = (vrm_dict, {"name": b_mat.name})

            pbr_dict: Dict[str, Json] = {}
            pbr_dict["name"] = b_mat.name

            if bpy.app.version < (2, 83):
                return fallback

            if bpy.app.version >= (3, 6):
                module_name = (
                    "io_scene_gltf2.blender.exp.material.gltf2_blender_gather_materials"
                )
            else:
                module_name = (
                    "io_scene_gltf2.blender.exp.gltf2_blender_gather_materials"
                )
            try:
                gltf2_blender_gather_materials = importlib.import_module(module_name)
            except ModuleNotFoundError:
                logger.exception("Failed to import glTF 2.0 Add-on")
                return fallback
            gather_material = gltf2_blender_gather_materials.gather_material

            gltf2_io_material: Optional[object] = None
            try:
                if bpy.app.version >= (3, 2):
                    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/master/addons/io_scene_gltf2/blender/exp/gltf2_blender_gather_primitives.py#L71-L96
                    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/9e08d423a803da52eb08fbc93d9aa99f3f681a27/addons/io_scene_gltf2/blender/exp/gltf2_blender_gather_materials.py#L42
                    gltf2_io_material = gather_material(
                        b_mat, 0, self.gltf2_addon_export_settings
                    )
                elif bpy.app.version >= (2, 91):
                    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/abd8380e19dbe5e5fb9042513ad6b744032bc9bc/addons/io_scene_gltf2/blender/exp/gltf2_blender_gather_materials.py#L32
                    gltf2_io_material = gather_material(
                        b_mat, self.gltf2_addon_export_settings
                    )
                else:
                    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/ac3471cae42b34fc69fda75fa404117272fa9560/addons/io_scene_gltf2/blender/exp/gltf2_blender_gather_materials.py#L32
                    gltf2_io_material = gather_material(
                        b_mat,
                        not b_mat.use_backface_culling,
                        self.gltf2_addon_export_settings,
                    )

                alpha_cutoff = getattr(gltf2_io_material, "alpha_cutoff", None)
                if isinstance(alpha_cutoff, (int, float)):
                    pbr_dict["alphaCutoff"] = alpha_cutoff

                alpha_mode = getattr(gltf2_io_material, "alpha_mode", None)
                if isinstance(alpha_mode, str):
                    pbr_dict["alphaMode"] = alpha_mode

                double_sided = getattr(gltf2_io_material, "double_sided", None)
                if isinstance(double_sided, bool):
                    pbr_dict["doubleSided"] = double_sided

                emissive_factor = getattr(gltf2_io_material, "emissive_factor", None)
                if isinstance(emissive_factor, abc.Sequence):
                    pbr_dict["emissiveFactor"] = make_json(emissive_factor)

                assign_dict(
                    pbr_dict,
                    "emissiveTexture",
                    add_gltf2_io_texture(
                        getattr(gltf2_io_material, "emissive_texture", None)
                    ),
                )

                extensions = getattr(gltf2_io_material, "extensions", None)
                if isinstance(extensions, dict):
                    extensions_dict: Dict[str, Json] = {}

                    # https://github.com/KhronosGroup/glTF/tree/19a1d820040239bca1327fc26220ae8cae9f948c/extensions/2.0/Khronos/KHR_materials_unlit
                    if extensions.get("KHR_materials_unlit") is not None:
                        extensions_dict["KHR_materials_unlit"] = {}

                    # https://github.com/KhronosGroup/glTF/blob/9c4a3567384b4d9f2706cdd9623bbb5ca7b341ad/extensions/2.0/Khronos/KHR_materials_emissive_strength
                    khr_materials_emissive_strength = getattr(
                        extensions.get("KHR_materials_emissive_strength"),
                        "extension",
                        None,
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

                    if extensions_dict:
                        pbr_dict["extensions"] = extensions_dict

                assign_dict(
                    pbr_dict,
                    "normalTexture",
                    add_gltf2_io_texture(
                        getattr(gltf2_io_material, "normal_texture", None)
                    ),
                )

                assign_dict(
                    pbr_dict,
                    "occlusionTexture",
                    add_gltf2_io_texture(
                        getattr(gltf2_io_material, "occlusion_texture", None)
                    ),
                )

                pbr_metallic_roughness = getattr(
                    gltf2_io_material, "pbr_metallic_roughness", None
                )
                if pbr_metallic_roughness is not None:
                    pbr_metallic_roughness_dict: Dict[str, Json] = {}

                    base_color_factor = getattr(
                        pbr_metallic_roughness, "base_color_factor", None
                    )
                    if isinstance(base_color_factor, abc.Sequence):
                        pbr_metallic_roughness_dict["baseColorFactor"] = make_json(
                            base_color_factor
                        )

                    assign_dict(
                        pbr_metallic_roughness_dict,
                        "baseColorTexture",
                        add_gltf2_io_texture(
                            getattr(pbr_metallic_roughness, "base_color_texture", None)
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
                        add_gltf2_io_texture(
                            getattr(
                                pbr_metallic_roughness,
                                "metallic_roughness_texture",
                                None,
                            )
                        ),
                    )

                    roughness_factor = getattr(
                        pbr_metallic_roughness, "roughness_factor", None
                    )
                    if isinstance(roughness_factor, (int, float)):
                        pbr_metallic_roughness_dict[
                            "roughnessFactor"
                        ] = roughness_factor

                    pbr_dict["pbrMetallicRoughness"] = pbr_metallic_roughness_dict
            except Exception:
                logger.exception(
                    "Failed to generate glTF Material using glTF 2.0 add-on"
                )
                return fallback

            return vrm_dict, pbr_dict

        def add_mtoon1_downgraded_texture(
            texture: Union[Mtoon0TexturePropertyGroup, Mtoon1TexturePropertyGroup],
            texture_properties: Dict[str, int],
            texture_properties_key: str,
            vector_properties: Dict[str, Sequence[float]],
        ) -> Optional[Dict[str, Json]]:
            if not texture.source:
                return None

            index = add_texture(
                texture.source.name,
                Mtoon1SamplerPropertyGroup.WRAP_ID_TO_NUMBER[texture.sampler.wrap_s],
                Mtoon1SamplerPropertyGroup.MAG_FILTER_ID_TO_NUMBER[
                    texture.sampler.mag_filter
                ],
                Mtoon1SamplerPropertyGroup.WRAP_ID_TO_NUMBER[texture.sampler.wrap_t],
                Mtoon1SamplerPropertyGroup.MIN_FILTER_ID_TO_NUMBER[
                    texture.sampler.min_filter
                ],
            )
            texture_properties[texture_properties_key] = index
            vector_properties[texture_properties_key] = [0, 0, 1, 1]

            result: Dict[str, Json] = {
                "index": index,
                "texCoord": 0,  # TODO:
            }
            return result

        def add_mtoon1_downgraded_texture_info(
            texture_info: Mtoon1TextureInfoPropertyGroup,
            texture_properties: Dict[str, int],
            texture_properties_key: str,
            vector_properties: Dict[str, Sequence[float]],
            khr_texture_transform: Optional[Mtoon1KhrTextureTransformPropertyGroup],
        ) -> Optional[Dict[str, Json]]:
            texture_info_dict = add_mtoon1_downgraded_texture(
                texture_info.index,
                texture_properties,
                texture_properties_key,
                vector_properties,
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

        def make_mtoon1_downgraded_mat_dict(
            b_mat: bpy.types.Material,
        ) -> Tuple[Dict[str, Json], Dict[str, Json]]:
            gltf = b_mat.vrm_addon_extension.mtoon1
            mtoon = gltf.extensions.vrmc_materials_mtoon

            material_dict: Dict[str, Json] = {
                "name": b_mat.name,
                "alphaMode": gltf.alpha_mode,
                "doubleSided": gltf.double_sided,
                "extensions": {"KHR_materials_unlit": {}},
            }
            pbr_metallic_roughness_dict: Dict[str, Json] = {
                "metallicFactor": 0,
                "roughnessFactor": 0.9,
            }
            keyword_map = {}
            tag_map = {}
            float_properties: Dict[str, float] = {}
            vector_properties: Dict[str, Sequence[float]] = {}
            texture_properties: Dict[str, int] = {}
            pbr_metallic_roughness_dict["baseColorFactor"] = list(
                gltf.pbr_metallic_roughness.base_color_factor
            )
            khr_texture_transform = (
                gltf.pbr_metallic_roughness.base_color_texture.extensions.khr_texture_transform
            )

            vector_properties["_Color"] = list(
                gltf.pbr_metallic_roughness.base_color_factor
            )

            if assign_dict(
                pbr_metallic_roughness_dict,
                "baseColorTexture",
                add_mtoon1_downgraded_texture_info(
                    gltf.pbr_metallic_roughness.base_color_texture,
                    texture_properties,
                    "_MainTex",
                    vector_properties,
                    khr_texture_transform,
                ),
            ):
                vector_properties["_MainTex"] = [
                    khr_texture_transform.offset[0],
                    khr_texture_transform.offset[1],
                    khr_texture_transform.scale[0],
                    khr_texture_transform.scale[1],
                ]

            vector_properties["_ShadeColor"] = list(mtoon.shade_color_factor) + [1]
            add_mtoon1_downgraded_texture_info(
                mtoon.shade_multiply_texture,
                texture_properties,
                "_ShadeTexture",
                vector_properties,
                khr_texture_transform,
            )

            float_properties["_BumpScale"] = gltf.normal_texture.scale
            if assign_dict(
                material_dict,
                "normalTexture",
                add_mtoon1_downgraded_texture_info(
                    gltf.normal_texture,
                    texture_properties,
                    "_BumpMap",
                    vector_properties,
                    khr_texture_transform,
                ),
            ):
                normal_texture_dict = material_dict.get("normalTexture")
                if isinstance(normal_texture_dict, dict):
                    normal_texture_dict["scale"] = gltf.normal_texture.scale
                keyword_map["_NORMALMAP"] = True

            add_mtoon1_downgraded_texture(
                gltf.mtoon0_shading_grade_texture,
                texture_properties,
                "_ShadingGradeTexture",
                vector_properties,
            )
            float_properties["_ShadingGradeRate"] = gltf.mtoon0_shading_grade_rate

            float_properties["_ShadeShift"] = convert.mtoon_shading_shift_1_to_0(
                mtoon.shading_toony_factor, mtoon.shading_shift_factor
            )
            float_properties["_ShadeToony"] = convert.mtoon_shading_toony_1_to_0(
                mtoon.shading_toony_factor, mtoon.shading_shift_factor
            )
            float_properties[
                "_IndirectLightIntensity"
            ] = convert.mtoon_gi_equalization_to_intensity(mtoon.gi_equalization_factor)
            float_properties["_RimLightingMix"] = gltf.mtoon0_rim_lighting_mix
            float_properties[
                "_RimFresnelPower"
            ] = mtoon.parametric_rim_fresnel_power_factor
            float_properties["_RimLift"] = mtoon.parametric_rim_lift_factor

            emissive_strength = (
                gltf.extensions.khr_materials_emissive_strength.emissive_strength
            )
            emissive_factor = Vector(gltf.emissive_factor)
            hdr_emissive_factor = emissive_factor * emissive_strength
            vector_properties["_EmissionColor"] = list(hdr_emissive_factor) + [1]
            if emissive_factor.length_squared > 0:
                material_dict["emissiveFactor"] = list(emissive_factor)

            assign_dict(
                material_dict,
                "emissiveTexture",
                add_mtoon1_downgraded_texture_info(
                    gltf.emissive_texture,
                    texture_properties,
                    "_EmissionMap",
                    vector_properties,
                    khr_texture_transform,
                ),
            )
            if pbr_metallic_roughness_dict:
                material_dict["pbrMetallicRoughness"] = pbr_metallic_roughness_dict

            add_mtoon1_downgraded_texture_info(
                mtoon.matcap_texture,
                texture_properties,
                "_SphereAdd",
                vector_properties,
                khr_texture_transform=None,
            )

            vector_properties["_RimColor"] = list(mtoon.parametric_rim_color_factor) + [
                1
            ]
            add_mtoon1_downgraded_texture_info(
                mtoon.rim_multiply_texture,
                texture_properties,
                "_RimTexture",
                vector_properties,
                khr_texture_transform,
            )

            vector_properties["_OutlineColor"] = list(mtoon.outline_color_factor) + [1]
            add_mtoon1_downgraded_texture_info(
                mtoon.outline_width_multiply_texture,
                texture_properties,
                "_OutlineWidthTexture",
                vector_properties,
                khr_texture_transform,
            )

            float_properties[
                "_UvAnimScrollX"
            ] = mtoon.uv_animation_scroll_x_speed_factor
            float_properties[
                "_UvAnimScrollY"
            ] = -mtoon.uv_animation_scroll_y_speed_factor
            float_properties[
                "_UvAnimRotation"
            ] = mtoon.uv_animation_rotation_speed_factor
            add_mtoon1_downgraded_texture_info(
                mtoon.uv_animation_mask_texture,
                texture_properties,
                "_UvAnimMaskTexture",
                vector_properties,
                khr_texture_transform,
            )

            float_properties["_OutlineLightingMix"] = mtoon.outline_lighting_mix_factor
            outline_color_mode = 1 if mtoon.outline_lighting_mix_factor > 0 else 0
            float_properties["_OutlineColorMode"] = outline_color_mode

            float_properties["_OutlineWidth"] = 0.0
            if mtoon.outline_width_mode == mtoon.OUTLINE_WIDTH_MODE_NONE:
                float_properties["_OutlineWidthMode"] = 0
                float_properties["_OutlineLightingMix"] = 0
                float_properties["_OutlineColorMode"] = 0
                set_mtoon_outline_keywords(keyword_map, False, False, False, False)
            elif mtoon.outline_width_mode == mtoon.OUTLINE_WIDTH_MODE_WORLD_COORDINATES:
                float_properties["_OutlineWidth"] = mtoon.outline_width_factor * 100
                float_properties["_OutlineWidthMode"] = 1
                if outline_color_mode == 0:
                    set_mtoon_outline_keywords(keyword_map, True, False, True, False)
                else:
                    set_mtoon_outline_keywords(keyword_map, True, False, False, True)
            elif (
                mtoon.outline_width_mode == mtoon.OUTLINE_WIDTH_MODE_SCREEN_COORDINATES
            ):
                float_properties["_OutlineWidth"] = mtoon.outline_width_factor * 200
                float_properties["_OutlineWidthMode"] = 2
                if outline_color_mode == 0:
                    set_mtoon_outline_keywords(keyword_map, False, True, True, False)
                else:
                    set_mtoon_outline_keywords(keyword_map, False, True, False, True)

            float_properties["_Cutoff"] = 0.5
            gltf.mtoon0_render_queue = (
                gltf.mtoon0_render_queue
            )  # call "mtoon0_render_queue()"
            if gltf.alpha_mode == gltf.ALPHA_MODE_OPAQUE:
                blend_mode = 0
                src_blend = 1
                dst_blend = 0
                z_write = 1
                alphatest_on = False
                render_queue = -1
                render_type = "Opaque"
            elif gltf.alpha_mode == gltf.ALPHA_MODE_MASK:
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

            add_mtoon1_downgraded_texture(
                gltf.mtoon0_receive_shadow_texture,
                texture_properties,
                "_ReceiveShadowTexture",
                vector_properties,
            )
            float_properties["_ReceiveShadowRate"] = gltf.mtoon0_receive_shadow_rate

            keyword_map["_ALPHABLEND_ON"] = b_mat.blend_method not in ("OPAQUE", "CLIP")
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
            elif b_mat.use_backface_culling:
                float_properties["_CullMode"] = 2
            else:
                float_properties["_CullMode"] = 0
            float_properties["_OutlineCullMode"] = 1
            float_properties["_DebugMode"] = 0
            float_properties[
                "_LightColorAttenuation"
            ] = gltf.mtoon0_light_color_attenuation
            float_properties[
                "_OutlineScaledMaxDistance"
            ] = gltf.mtoon0_outline_scaled_max_distance

            keyword_map["MTOON_DEBUG_NORMAL"] = False
            keyword_map["MTOON_DEBUG_LITSHADERATE"] = False

            mtoon_dict: Dict[str, Json] = {
                "name": b_mat.name,
                "shader": "VRM/MToon",
                "keywordMap": make_json(keyword_map),
                "tagMap": make_json(tag_map),
                "floatProperties": make_json(float_properties),
                "vectorProperties": make_json(vector_properties),
                "textureProperties": make_json(texture_properties),
                "renderQueue": render_queue,
            }

            return mtoon_dict, material_dict

        for b_mat in search.export_materials(self.export_objects):
            material_properties_dict: Dict[str, Json] = {}
            pbr_dict: Dict[str, Json] = {}
            if b_mat.vrm_addon_extension.mtoon1.enabled:
                material_properties_dict, pbr_dict = make_mtoon1_downgraded_mat_dict(
                    b_mat
                )
            elif not b_mat.node_tree:
                material_properties_dict, pbr_dict = make_non_vrm_mat_dict(b_mat)
            elif b_mat.get("vrm_shader") == "MToon_unversioned":
                for node in b_mat.node_tree.nodes:
                    if node.type == "OUTPUT_MATERIAL":
                        mtoon_shader_node = node.inputs["Surface"].links[0].from_node
                        (
                            material_properties_dict,
                            pbr_dict,
                        ) = make_mtoon_unversioned_extension_dict(
                            b_mat, mtoon_shader_node
                        )
                        break
            elif b_mat.get("vrm_shader") == "GLTF":
                for node in b_mat.node_tree.nodes:
                    if node.type == "OUTPUT_MATERIAL":
                        gltf_shader_node = node.inputs["Surface"].links[0].from_node
                        material_properties_dict, pbr_dict = make_gltf_mat_dict(
                            b_mat, gltf_shader_node
                        )
                        break
            elif b_mat.get("vrm_shader") == "TRANSPARENT_ZWRITE":
                for node in b_mat.node_tree.nodes:
                    if node.type == "OUTPUT_MATERIAL":
                        zw_shader_node = node.inputs["Surface"].links[0].from_node
                        material_properties_dict, pbr_dict = make_transzw_mat_dict(
                            b_mat, zw_shader_node
                        )
                        break
            else:
                material_properties_dict, pbr_dict = make_non_vrm_mat_dict(b_mat)

            glb_material_list.append(pbr_dict)
            vrm_material_props_list.append(material_properties_dict)

        apply_texture_and_sampler_to_dict()
        self.json_dict["materials"] = glb_material_list
        self.json_dict.update(
            {"extensions": {"VRM": {"materialProperties": vrm_material_props_list}}}
        )

    def joint_id_from_node_name_solver(
        self, node_name: str, node_id_dict: Dict[str, int]
    ) -> int:
        # 存在しないボーンを指してる場合は-1を返す
        node_id = node_id_dict.get(node_name)
        if not isinstance(node_id, int):
            return -1
        skin_dicts = self.json_dict.get("skins")
        if not isinstance(skin_dicts, list) or not skin_dicts:
            return -1
        skin_dict = skin_dicts[0]
        if not isinstance(skin_dict, dict):
            return -1
        joints = skin_dict.get("joints")
        if not isinstance(joints, list):
            return -1
        if node_id not in joints:
            return -1
        return joints.index(node_id)

    @staticmethod
    def fetch_morph_vertex_normal_difference(
        mesh_data: bpy.types.Mesh,
    ) -> Dict[str, List[List[float]]]:
        exclusion_vertex_indices = set()
        for polygon in mesh_data.polygons:
            material = mesh_data.materials[polygon.material_index]
            if material is None:
                continue
            # Use non-evaluated material
            material = bpy.data.materials.get(material.name)
            if material is None:
                continue
            if material.vrm_addon_extension.mtoon1.export_shape_key_normals:
                continue
            if material.vrm_addon_extension.mtoon1.enabled:
                exclusion_vertex_indices.update(polygon.vertices)
                continue
            node = search.vrm_shader_node(material)
            if not node:
                continue
            if node.node_tree["SHADER"] == "MToon_unversioned":
                exclusion_vertex_indices.update(polygon.vertices)

        morph_normal_diff_dict = {}
        vert_base_normal_dict = {}
        for kb in mesh_data.shape_keys.key_blocks:
            # 頂点のノーマルではなくsplit(loop)のノーマルを使う
            # https://github.com/KhronosGroup/glTF-Blender-IO/pull/1129
            split_normals = kb.normals_split_get()

            vertex_normal_vectors = [Vector([0.0, 0.0, 0.0])] * len(mesh_data.vertices)
            for loop_index in range(len(split_normals) // 3):
                loop = mesh_data.loops[loop_index]
                if loop.vertex_index in exclusion_vertex_indices:
                    continue
                v = Vector(
                    [
                        split_normals[loop_index * 3 + 0],
                        split_normals[loop_index * 3 + 1],
                        split_normals[loop_index * 3 + 2],
                    ]
                )
                if v.length <= float_info.epsilon:
                    continue
                vertex_normal_vectors[loop.vertex_index] = (
                    vertex_normal_vectors[loop.vertex_index] + v
                )

            vertex_normals = [0.0] * len(vertex_normal_vectors) * 3
            for index, _ in enumerate(vertex_normal_vectors):
                if index in exclusion_vertex_indices:
                    continue
                n = vertex_normal_vectors[index]
                if n.length <= float_info.epsilon:
                    continue
                n = n.normalized()
                vertex_normals[index * 3 + 0] = n[0]
                vertex_normals[index * 3 + 1] = n[1]
                vertex_normals[index * 3 + 2] = n[2]

            vert_base_normal_dict.update({kb.name: vertex_normals})
        reference_key_name = mesh_data.shape_keys.reference_key.name
        for k, v in vert_base_normal_dict.items():
            if k == reference_key_name:
                continue
            values = []
            for vert_morph_normal, vert_base_normal in zip(
                zip(*[iter(v)] * 3),
                zip(*[iter(vert_base_normal_dict[reference_key_name])] * 3),
            ):
                values.append(
                    [vert_morph_normal[i] - vert_base_normal[i] for i in range(3)]
                )
            morph_normal_diff_dict.update({k: values})
        return morph_normal_diff_dict

    def is_skin_mesh(self, mesh: bpy.types.Object) -> bool:
        while mesh:
            if [True for m in mesh.modifiers if m.type == "ARMATURE"]:
                return True
            if not mesh.parent:
                return True
            if (
                mesh.parent_type == "BONE"
                and mesh.parent.type == "ARMATURE"
                and mesh.parent_bone is not None
            ):
                return False
            if (
                mesh.parent_type != "OBJECT"
                or mesh.parent.type not in search.MESH_CONVERTIBLE_OBJECT_TYPES
            ):
                return True
            mesh = mesh.parent
        return True

    @staticmethod
    def min_max(minmax: List[List[float]], position: List[float]) -> None:
        for i in range(3):
            minmax[0][i] = position[i] if position[i] < minmax[0][i] else minmax[0][i]
            minmax[1][i] = position[i] if position[i] > minmax[1][i] else minmax[1][i]

    # FB_ngon_encodeのため、ngonを扇状に割る。また、分割前の連続したポリゴンが最初の頂点を共有する場合、ポリゴンごとに最初の頂点を別の構成する頂点に変更する
    # import時に、起点が同じ連続した三角を一つのngonとして結合することで、ngonを再生できる
    # メリット：ポリゴンのインデックスにトリックがあるだけで基本的に容量が変わらず、拡張非対応であればそのまま読めば普通に三角として表示できる
    # 欠点：ngon対応がない場合、扇状分割はtriangulate("Beautiful")等に比して分割後が汚く見える可能性が高い
    # また、ngonが凸包ポリゴンで無い場合、見た目が破綻する(例：鈍角三角形の底辺を接合した4角形)
    @staticmethod
    def tessface_fan(
        bm: bmesh.types.BMesh, export_fb_ngon_encoding: bool
    ) -> List[Tuple[int, List[bmesh.types.BMLoop]]]:
        if not export_fb_ngon_encoding:
            return [
                (loops[0].face.material_index, loops)
                for loops in bm.calc_loop_triangles()
                if loops
            ]

        # TODO: 凹や穴の空いたNゴンに対応
        faces = bm.faces
        sorted_faces = sorted(
            faces,
            key=lambda f: int(  # material_indexの型をintとして明示的に指定しないとmypyがエラーになる
                f.material_index
            ),
        )
        polys: List[Tuple[int, List[bmesh.types.BMLoop]]] = []
        for face in sorted_faces:
            if len(face.loops) <= 3:
                if polys and face.loops[0].vert.index == polys[-1][1][0].vert.index:
                    polys.append(
                        (
                            face.material_index,
                            [face.loops[n] for n in [1, 2, 0]],
                        )
                    )
                else:
                    polys.append((face.material_index, face.loops[:]))
            else:
                if polys and face.loops[0].vert.index == polys[-1][1][0].vert.index:
                    for i in range(0, len(face.loops) - 2):
                        polys.append(
                            (
                                face.material_index,
                                [
                                    face.loops[-1],
                                    face.loops[i],
                                    face.loops[i + 1],
                                ],
                            )
                        )
                else:
                    for i in range(1, len(face.loops) - 1):
                        polys.append(
                            (
                                face.material_index,
                                [
                                    face.loops[0],
                                    face.loops[i],
                                    face.loops[i + 1],
                                ],
                            )
                        )
        return polys

    def mesh_to_bin_and_dict(self) -> None:
        mesh_dicts = self.json_dict.get("meshes")
        if not isinstance(mesh_dicts, list):
            mesh_dicts = []
            self.json_dict["meshes"] = mesh_dicts

        meshes = [
            obj
            for obj in self.export_objects
            if obj.type in search.MESH_CONVERTIBLE_OBJECT_TYPES
        ]
        while True:
            swapped = False
            for mesh in list(meshes):
                if (
                    mesh.parent_type == "OBJECT"
                    and mesh.parent
                    and mesh.parent.type in search.MESH_CONVERTIBLE_OBJECT_TYPES
                    and meshes.index(mesh) < meshes.index(mesh.parent)
                ):
                    meshes.remove(mesh)
                    meshes.append(mesh)
                    swapped = True
            if not swapped:
                break

        for mesh in meshes:
            is_skin_mesh = self.is_skin_mesh(mesh)
            node_dict = {
                "name": mesh.name,
                "translation": self.axis_blender_to_glb(mesh.location),
                "rotation": [0, 0, 0, 1],  # このへんは規約なので
                "scale": [1, 1, 1],  # このへんは規約なので
            }
            if is_skin_mesh:
                node_dict["translation"] = [0, 0, 0]  # skinnedmeshはtransformを無視される

            node_dicts = self.json_dict.get("nodes")
            if not isinstance(node_dicts, list):
                node_dicts = []
                self.json_dict["nodes"] = node_dicts

            node_dicts.append(node_dict)

            mesh_node_id = len(node_dicts) - 1

            if is_skin_mesh:
                first_scene_nodes = deep.get(self.json_dict, ["scenes", 0, "nodes"])
                if isinstance(first_scene_nodes, list):
                    first_scene_nodes.append(mesh_node_id)
            else:
                if mesh.parent_type == "BONE":
                    parent_node = (
                        [
                            node_dict
                            for node_dict in node_dicts
                            if isinstance(node_dict, dict)
                            and node_dict.get("name") == mesh.parent_bone
                        ]
                        + [None]
                    )[0]
                elif mesh.parent_type == "OBJECT":
                    parent_node = (
                        [
                            node_dict
                            for node_dict in node_dicts
                            if isinstance(node_dict, dict)
                            and node_dict.get("name") == mesh.parent.name
                        ]
                        + [None]
                    )[0]
                else:
                    parent_node = None
                base_pos = [0, 0, 0]
                if parent_node:
                    children = parent_node.get("children")
                    if not isinstance(children, list):
                        children = []
                        parent_node["children"] = children
                    children.append(mesh_node_id)
                    if mesh.parent_type == "BONE":
                        base_pos = (
                            self.armature.matrix_world
                            @ self.armature.pose.bones[mesh.parent_bone].matrix.to_4x4()
                        ).to_translation()
                    else:
                        base_pos = mesh.parent.matrix_world.to_translation()
                else:
                    first_scene_nodes = deep.get(self.json_dict, ["scenes", 0, "nodes"])
                    if isinstance(first_scene_nodes, list):
                        first_scene_nodes.append(mesh_node_id)
                mesh_pos = mesh.matrix_world.to_translation()
                relate_pos = [mesh_pos[i] - base_pos[i] for i in range(3)]

                if 0 <= mesh_node_id < len(node_dicts):
                    mesh_node_dict = node_dicts[mesh_node_id]
                    if isinstance(mesh_node_dict, dict):
                        mesh_node_dict["translation"] = make_json(
                            self.axis_blender_to_glb(relate_pos)
                        )

            # Check added to resolve https://github.com/saturday06/VRM-Addon-for-Blender/issues/70
            if self.context.view_layer.objects.active is not None:
                bpy.ops.object.mode_set(mode="OBJECT")

            # https://docs.blender.org/api/2.80/bpy.types.Depsgraph.html
            depsgraph = self.context.evaluated_depsgraph_get()
            mesh_owner = mesh.evaluated_get(depsgraph)
            mesh_from_mesh_owner = mesh_owner.to_mesh(
                preserve_all_data_layers=True, depsgraph=depsgraph
            )
            if not mesh_from_mesh_owner:
                continue
            mesh_data = mesh_from_mesh_owner.copy()
            for prop in mesh.data.keys():
                mesh_data[prop] = mesh.data[prop]

            mesh.hide_viewport = False
            mesh.hide_select = False
            self.context.view_layer.objects.active = mesh
            bpy.ops.object.mode_set(mode="EDIT")

            mesh_data_transform = Matrix.Identity(4)
            if not is_skin_mesh:
                mesh_data_transform @= Matrix.Translation(
                    -mesh.matrix_world.to_translation()
                )
            mesh_data_transform @= mesh.matrix_world
            mesh_data.transform(mesh_data_transform, shape_keys=True)
            mesh_data.calc_loop_triangles()
            mesh_data.calc_normals_split()

            bm = bmesh.new()
            bm.from_mesh(mesh_data)

            # temporary used
            material_dicts = self.json_dict.get("materials")
            if not isinstance(material_dicts, list):
                material_dicts = []
                self.json_dict["materials"] = material_dicts

            mat_id_dict = {
                str(material_dict.get("name")): i
                for i, material_dict in enumerate(material_dicts)
                if isinstance(material_dict, dict)
            }
            material_slot_dict = {
                i: slot.material.name
                for i, slot in enumerate(mesh.material_slots)
                if slot.name and slot.material.name
            }
            node_id_dict: Dict[str, int] = {
                str(node_dict.get("name")): i
                for i, node_dict in enumerate(node_dicts)
                if isinstance(node_dict, dict)
            }

            v_group_name_dict = {i: vg.name for i, vg in enumerate(mesh.vertex_groups)}
            fmin, fmax = FLOAT_NEGATIVE_MAX, FLOAT_POSITIVE_MAX
            unique_vertex_id = 0
            # {(uv...,vertex_index):unique_vertex_id} (uvと頂点番号が同じ頂点は同じものとして省くようにする)
            unique_vertex_dict: Dict[Tuple[object, ...], int] = {}
            uvlayers_dict = {
                i: uvlayer.name for i, uvlayer in enumerate(mesh_data.uv_layers)
            }

            primitive_index_bin_dict: Dict[Optional[int], bytearray] = {
                mat_id_dict[mat.name]: bytearray()
                for mat in mesh.material_slots
                if mat.name
            }
            primitive_index_vertex_count: Dict[Optional[int], int] = {
                mat_id_dict[mat.name]: 0 for mat in mesh.material_slots if mat.name
            }

            shape_pos_bin_dict: Dict[str, bytearray] = {}
            shape_normal_bin_dict: Dict[str, bytearray] = {}
            shape_min_max_dict: Dict[str, List[List[float]]] = {}
            morph_normal_diff_dict: Dict[str, List[List[float]]] = {}
            if mesh_data.shape_keys is not None:
                # 0番目Basisは省く
                shape_pos_bin_dict = {
                    shape.name: bytearray()
                    for shape in mesh_data.shape_keys.key_blocks[1:]
                }
                shape_normal_bin_dict = {
                    shape.name: bytearray()
                    for shape in mesh_data.shape_keys.key_blocks[1:]
                }
                shape_min_max_dict = {
                    shape.name: [[fmax, fmax, fmax], [fmin, fmin, fmin]]
                    for shape in mesh_data.shape_keys.key_blocks[1:]
                }
                # {morphname:{vertexid:[diff_X,diff_y,diff_z]}}
                morph_normal_diff_dict = self.fetch_morph_vertex_normal_difference(
                    mesh_data
                )
            position_bin = bytearray()
            position_min_max = [[fmax, fmax, fmax], [fmin, fmin, fmin]]
            normal_bin = bytearray()
            joints_bin = bytearray()
            weights_bin = bytearray()
            texcoord_bins = {
                uvlayer_id: bytearray() for uvlayer_id in uvlayers_dict.keys()
            }
            float_vec4_packer = struct.Struct("<ffff").pack
            float_vec3_packer = struct.Struct("<fff").pack
            float_pair_packer = struct.Struct("<ff").pack
            unsigned_int_scalar_packer = struct.Struct("<I").pack
            unsigned_short_vec4_packer = struct.Struct("<HHHH").pack

            for material_index, loops in self.tessface_fan(
                bm, self.export_fb_ngon_encoding
            ):
                for loop in loops:
                    uv_list = []
                    for uvlayer_name in uvlayers_dict.values():
                        uv_layer = bm.loops.layers.uv[uvlayer_name]
                        uv_list.extend([loop[uv_layer].uv[0], loop[uv_layer].uv[1]])

                    # 頂点のノーマルではなくloopのノーマルを使う。これで失うものはあると思うが、
                    # glTF 2.0アドオンと同一にしておくのが無難だろうと判断。
                    # https://github.com/KhronosGroup/glTF-Blender-IO/pull/1127
                    vert_normal = mesh_data.loops[loop.index].normal
                    vertex_key = (*uv_list, *vert_normal, loop.vert.index)
                    cached_vert_id = unique_vertex_dict.get(
                        vertex_key
                    )  # keyがなければNoneを返す
                    if cached_vert_id is not None:
                        primitive_index = None
                        material_slot_name = material_slot_dict.get(material_index)
                        if isinstance(material_slot_name, str):
                            primitive_index = mat_id_dict[material_slot_name]
                        primitive_index_bin_dict[primitive_index].extend(
                            unsigned_int_scalar_packer(cached_vert_id)
                        )
                        primitive_index_vertex_count[primitive_index] += 1
                        continue
                    unique_vertex_dict[vertex_key] = unique_vertex_id
                    for uvlayer_id, uvlayer_name in uvlayers_dict.items():
                        uv_layer = bm.loops.layers.uv[uvlayer_name]
                        uv = loop[uv_layer].uv
                        texcoord_bins[uvlayer_id].extend(
                            float_pair_packer(uv[0], 1 - uv[1])
                        )  # blenderとglbのuvは上下逆
                    for shape_name in shape_pos_bin_dict:
                        shape_layer = bm.verts.layers.shape[shape_name]
                        morph_pos = self.axis_blender_to_glb(
                            [
                                loop.vert[shape_layer][i] - loop.vert.co[i]
                                for i in range(3)
                            ]
                        )
                        shape_pos_bin_dict[shape_name].extend(
                            float_vec3_packer(*morph_pos)
                        )
                        shape_normal_bin_dict[shape_name].extend(
                            float_vec3_packer(
                                *self.axis_blender_to_glb(
                                    morph_normal_diff_dict[shape_name][loop.vert.index]
                                )
                            )
                        )
                        self.min_max(shape_min_max_dict[shape_name], morph_pos)
                    if is_skin_mesh:
                        weight_and_joint_list: List[Tuple[float, int]] = []
                        for v_group in mesh_data.vertices[loop.vert.index].groups:
                            v_group_name = v_group_name_dict.get(v_group.group)
                            if v_group_name is None:
                                continue
                            joint_id = self.joint_id_from_node_name_solver(
                                v_group_name, node_id_dict
                            )
                            # 存在しないボーンを指してる場合は-1を返されてるので、その場合は飛ばす
                            if joint_id == -1:
                                continue
                            # ウエイトがゼロのジョイントの値は無視してゼロになるようにする
                            # https://github.com/KhronosGroup/glTF/tree/f33f90ad9439a228bf90cde8319d851a52a3f470/specification/2.0#skinned-mesh-attributes
                            if v_group.weight < float_info.epsilon:
                                continue

                            weight_and_joint_list.append((v_group.weight, joint_id))

                        while len(weight_and_joint_list) < 4:
                            weight_and_joint_list.append((0.0, 0))

                        weight_and_joint_list.sort(reverse=True)

                        if len(weight_and_joint_list) > 4:
                            logger.warning(
                                f"Joints on vertex id:{loop.vert.index} in: {mesh.name} are truncated"
                            )
                            weight_and_joint_list = weight_and_joint_list[:4]

                        weights = [weight for weight, _ in weight_and_joint_list]
                        joints = [joint for _, joint in weight_and_joint_list]

                        if sum(weights) < float_info.epsilon:
                            logger.warning(
                                f"No weight on vertex id:{loop.vert.index} in: {mesh.name}"
                            )

                            # Attach near bone
                            bone_name: Optional[str] = None
                            mesh_parent = mesh
                            while (
                                mesh_parent
                                and mesh_parent.type
                                in search.MESH_CONVERTIBLE_OBJECT_TYPES
                                and mesh_parent != mesh
                            ):
                                if (
                                    mesh_parent.parent_type == "BONE"
                                    and mesh_parent.parent_bone
                                    in self.armature.data.bones
                                ):
                                    bone_name = mesh_parent.parent_bone
                                    break
                                mesh_parent = mesh.parent
                            if not bone_name:
                                for (
                                    human_bone
                                ) in (
                                    self.armature.data.vrm_addon_extension.vrm0.humanoid.human_bones
                                ):
                                    if human_bone.bone == "hips":
                                        bone_name = human_bone.node.bone_name
                                if (
                                    bone_name is None
                                    or bone_name not in self.armature.data.bones
                                ):
                                    raise ValueError("No hips bone found")
                            bone_index = next(
                                index
                                for index, node_dict in enumerate(node_dicts)
                                if isinstance(node_dict, dict)
                                and node_dict.get("name") == bone_name
                            )
                            weights = [1.0, 0, 0, 0]
                            joints = [bone_index, 0, 0, 0]

                        normalized_weights = normalize_weights_compatible_with_gl_float(
                            weights
                        )
                        joints_bin.extend(unsigned_short_vec4_packer(*joints))
                        weights_bin.extend(float_vec4_packer(*normalized_weights))

                    vert_location = self.axis_blender_to_glb(loop.vert.co)
                    position_bin.extend(float_vec3_packer(*vert_location))
                    self.min_max(position_min_max, vert_location)
                    normal_bin.extend(
                        float_vec3_packer(*self.axis_blender_to_glb(vert_normal))
                    )
                    primitive_index = None
                    material_slot_name = material_slot_dict.get(material_index)
                    if isinstance(material_slot_name, str):
                        primitive_index = mat_id_dict[material_slot_name]
                    if primitive_index not in primitive_index_bin_dict:
                        primitive_index_bin_dict[primitive_index] = bytearray()
                    if primitive_index not in primitive_index_vertex_count:
                        primitive_index_vertex_count[primitive_index] = 0
                    primitive_index_bin_dict[primitive_index].extend(
                        unsigned_int_scalar_packer(unique_vertex_id)
                    )
                    primitive_index_vertex_count[primitive_index] += 1
                    unique_vertex_id += 1

            # DONE :index position, uv, normal, position morph,JOINT WEIGHT
            # TODO: morph_normal, v_color...?
            primitive_glbs_dict = {
                mat_id: GlbBin(
                    index_bin,
                    "SCALAR",
                    GL_UNSIGNED_INT,
                    primitive_index_vertex_count[mat_id],
                    None,
                    self.glb_bin_collector,
                )
                for mat_id, index_bin in primitive_index_bin_dict.items()
                if index_bin
            }

            if not primitive_glbs_dict:
                bm.free()
                continue

            mesh_index = len(mesh_dicts)
            node_dict["mesh"] = mesh_index
            if is_skin_mesh:
                # TODO: 決め打ちってどうよ:一体のモデルなのだから2つもあっては困る(から決め打ち(やめろ(やだ))
                node_dict["skin"] = 0

            pos_glb = GlbBin(
                position_bin,
                "VEC3",
                GL_FLOAT,
                unique_vertex_id,
                position_min_max,
                self.glb_bin_collector,
            )
            nor_glb = GlbBin(
                normal_bin,
                "VEC3",
                GL_FLOAT,
                unique_vertex_id,
                None,
                self.glb_bin_collector,
            )
            uv_glbs = [
                GlbBin(
                    texcoord_bin,
                    "VEC2",
                    GL_FLOAT,
                    unique_vertex_id,
                    None,
                    self.glb_bin_collector,
                )
                for texcoord_bin in texcoord_bins.values()
            ]

            joints_glb = None
            weights_glb = None
            if is_skin_mesh:
                joints_glb = GlbBin(
                    joints_bin,
                    "VEC4",
                    GL_UNSIGNED_SHORT,
                    unique_vertex_id,
                    None,
                    self.glb_bin_collector,
                )
                weights_glb = GlbBin(
                    weights_bin,
                    "VEC4",
                    GL_FLOAT,
                    unique_vertex_id,
                    None,
                    self.glb_bin_collector,
                )

            morph_pos_glbs = None
            morph_normal_glbs = None
            if shape_pos_bin_dict:
                morph_pos_glbs = [
                    GlbBin(
                        morph_pos_bin,
                        "VEC3",
                        GL_FLOAT,
                        unique_vertex_id,
                        morph_minmax,
                        self.glb_bin_collector,
                    )
                    for morph_pos_bin, morph_minmax in zip(
                        shape_pos_bin_dict.values(), shape_min_max_dict.values()
                    )
                ]
                morph_normal_glbs = [
                    GlbBin(
                        morph_normal_bin,
                        "VEC3",
                        GL_FLOAT,
                        unique_vertex_id,
                        None,
                        self.glb_bin_collector,
                    )
                    for morph_normal_bin in shape_normal_bin_dict.values()
                ]

            primitive_list = []
            for primitive_id, index_glb in primitive_glbs_dict.items():
                primitive: Dict[str, Json] = {"mode": 4}
                if primitive_id is not None:
                    primitive["material"] = primitive_id
                primitive["indices"] = index_glb.accessor_id
                attributes_dict: Dict[str, Json] = {
                    "POSITION": pos_glb.accessor_id,
                    "NORMAL": nor_glb.accessor_id,
                }
                primitive["attributes"] = attributes_dict
                if is_skin_mesh:
                    if joints_glb is None:
                        raise ValueError("joints glb is None")
                    if weights_glb is None:
                        raise ValueError("weights glb is None")
                    attributes_dict.update(
                        {
                            "JOINTS_0": joints_glb.accessor_id,
                            "WEIGHTS_0": weights_glb.accessor_id,
                        }
                    )
                attributes_dict.update(
                    {
                        f"TEXCOORD_{i}": uv_glb.accessor_id
                        for i, uv_glb in enumerate(uv_glbs)
                    }
                )
                if shape_pos_bin_dict:
                    if morph_pos_glbs and morph_normal_glbs:
                        primitive["targets"] = [
                            {
                                "POSITION": morph_pos_glb.accessor_id,
                                "NORMAL": morph_normal_glb.accessor_id,
                            }
                            for morph_pos_glb, morph_normal_glb in zip(
                                morph_pos_glbs, morph_normal_glbs
                            )
                        ]
                    primitive["extras"] = {
                        "targetNames": list(shape_pos_bin_dict.keys())
                    }
                primitive_list.append(primitive)
            self.mesh_name_to_index[mesh.name] = mesh_index

            mesh_dict = {
                "name": mesh.data.name,
                "primitives": primitive_list,
            }
            if self.export_fb_ngon_encoding:
                mesh_dict["extensions"] = {"FB_ngon_encoding": {}}

            mesh_dicts.append(mesh_dict)
            bm.free()

            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.mode_set(mode="OBJECT")

    def exporter_name(self) -> str:
        v = addon_version()
        if environ.get("BLENDER_VRM_USE_TEST_EXPORTER_VERSION") == "true":
            v = (999, 999, 999)
        return "saturday06_blender_vrm_exporter_experimental_" + ".".join(map(str, v))

    def gltf_meta_to_dict(self) -> None:
        extensions_used = []

        base_extensions_dicts: List[Json] = []
        base_extensions_dicts.append(self.json_dict)

        for mesh_dict in deep.get_list(self.json_dict, ["meshes"], []):
            base_extensions_dicts.append(mesh_dict)

        for material_dict in deep.get_list(self.json_dict, ["materials"], []):
            if not isinstance(material_dict, dict):
                continue
            base_extensions_dicts.append(material_dict)
            base_extensions_dicts.append(
                deep.get(material_dict, ["pbrMetallicRoughness", "baseColorTexture"])
            )
            base_extensions_dicts.append(
                deep.get(
                    material_dict, ["pbrMetallicRoughness", "metallicRoughnessTexture"]
                )
            )
            base_extensions_dicts.append(material_dict.get("normalTexture"))
            base_extensions_dicts.append(material_dict.get("emissiveTexture"))
            base_extensions_dicts.append(material_dict.get("occlusionTexture"))

        for base_extensions_dict in base_extensions_dicts:
            if not isinstance(base_extensions_dict, dict):
                continue
            extensions_dict = base_extensions_dict.get("extensions")
            if not isinstance(extensions_dict, dict):
                continue
            for key in extensions_dict:
                if key not in extensions_used:
                    extensions_used.append(key)

        extensions_used.sort()

        gltf_meta_dict: Dict[str, Json] = {
            "extensionsUsed": make_json(extensions_used),
            "asset": {
                "generator": self.exporter_name(),
                "version": "2.0",  # glTF version
            },
        }

        self.json_dict.update(gltf_meta_dict)

    def vrm_meta_to_dict(self) -> None:
        node_dicts = self.json_dict["nodes"]
        if not isinstance(node_dicts, list):
            node_dicts = []
            self.json_dict["nodes"] = node_dicts

        mesh_dicts = self.json_dict["meshes"]
        if not isinstance(mesh_dicts, list):
            mesh_dicts = []
            self.json_dict["meshes"] = mesh_dicts

        # materialProperties は material_to_dict()で処理する
        # vrm extension
        meta = self.armature.data.vrm_addon_extension.vrm0.meta
        vrm_extension_dict: Dict[str, Json] = {
            "exporterVersion": self.exporter_name(),
            "specVersion": "0.0",
        }

        # meta
        vrm_extension_meta_dict = {
            "title": meta.title,
            "version": meta.version,
            "author": meta.author,
            "contactInformation": meta.contact_information,
            "reference": meta.reference,
            "allowedUserName": meta.allowed_user_name,
            "violentUssageName": meta.violent_ussage_name,  # noqa: SC200
            "sexualUssageName": meta.sexual_ussage_name,  # noqa: SC200
            "commercialUssageName": meta.commercial_ussage_name,  # noqa: SC200
            "otherPermissionUrl": meta.other_permission_url,
            "licenseName": meta.license_name,
            "otherLicenseUrl": meta.other_license_url,
        }
        vrm_extension_dict["meta"] = vrm_extension_meta_dict
        if meta.texture and meta.texture.name:
            thumbnail_indices = [
                index
                for index, image_bin in enumerate(self.glb_bin_collector.image_bins)
                if image_bin.name == meta.texture.name
            ]
            if thumbnail_indices:
                sampler_dicts = self.json_dict.get("samplers")
                if not isinstance(sampler_dicts, list):
                    sampler_dicts = []
                    self.json_dict["samplers"] = sampler_dicts
                # TODO: remove duplication
                sampler_dicts.append(
                    {
                        "magFilter": GL_LINEAR,
                        "minFilter": GL_LINEAR,
                        "wrapS": GL_REPEAT,
                        "wrapT": GL_REPEAT,
                    }
                )

                texture_dicts = self.json_dict.get("textures")
                if not isinstance(texture_dicts, list):
                    texture_dicts = []
                    self.json_dict["textures"] = texture_dicts
                texture_dicts.append(
                    {
                        "sampler": len(sampler_dicts) - 1,
                        "source": thumbnail_indices[0],
                    },
                )
                vrm_extension_meta_dict["texture"] = len(texture_dicts) - 1

        # humanoid
        node_name_id_dict = {
            node_dict.get("name"): i
            for i, node_dict in enumerate(node_dicts)
            if isinstance(node_dict, dict)
        }
        human_bone_dicts: List[Json] = []
        humanoid_dict: Dict[str, Json] = {"humanBones": human_bone_dicts}
        vrm_extension_dict["humanoid"] = humanoid_dict
        humanoid = self.armature.data.vrm_addon_extension.vrm0.humanoid
        for human_bone_name in HumanBoneSpecifications.all_names:
            for human_bone in humanoid.human_bones:
                if (
                    human_bone.bone != human_bone_name
                    or not human_bone.node.bone_name
                    or human_bone.node.bone_name not in node_name_id_dict
                ):
                    continue
                human_bone_dict = {
                    "bone": human_bone_name,
                    "node": node_name_id_dict[human_bone.node.bone_name],
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

        # firstPerson
        first_person_dict: Dict[str, Json] = {}
        vrm_extension_dict["firstPerson"] = first_person_dict
        first_person = self.armature.data.vrm_addon_extension.vrm0.first_person

        if first_person.first_person_bone.bone_name:
            first_person_dict["firstPersonBone"] = node_name_id_dict[
                first_person.first_person_bone.bone_name
            ]
        else:
            name = [
                human_bone.node.bone_name
                for human_bone in self.armature.data.vrm_addon_extension.vrm0.humanoid.human_bones
                if human_bone.bone == "head"
            ][0]
            first_person_dict["firstPersonBone"] = node_name_id_dict[name]

        first_person_dict["firstPersonBoneOffset"] = {
            # Axis confusing
            "x": first_person.first_person_bone_offset[0],
            "y": first_person.first_person_bone_offset[2],
            "z": first_person.first_person_bone_offset[1],
        }

        mesh_annotation_dicts: List[Json] = []
        first_person_dict["meshAnnotations"] = mesh_annotation_dicts
        for mesh_annotation in first_person.mesh_annotations:
            if (
                mesh_annotation.mesh
                and mesh_annotation.mesh.mesh_object_name
                and mesh_annotation.mesh.mesh_object_name in bpy.data.objects
                and bpy.data.objects[mesh_annotation.mesh.mesh_object_name].type
                == "MESH"
            ):
                matched_mesh_indices = [
                    i
                    for i, mesh_dict in enumerate(mesh_dicts)
                    if isinstance(mesh_dict, dict)
                    and mesh_dict.get("name")
                    == bpy.data.objects[mesh_annotation.mesh.mesh_object_name].data.name
                ]
                mesh_index = (matched_mesh_indices + [-1])[0]
            else:
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

        # blendShapeMaster
        blend_shape_group_dicts: List[Json] = []
        blend_shape_master_dict: Dict[str, Json] = {
            "blendShapeGroups": blend_shape_group_dicts
        }
        vrm_extension_dict["blendShapeMaster"] = blend_shape_master_dict

        # meshを名前からid
        # weightを0-1から0-100に
        # shape_indexを名前からindexに
        for (
            blend_shape_group
        ) in (
            self.armature.data.vrm_addon_extension.vrm0.blend_shape_master.blend_shape_groups
        ):
            blend_shape_group_dict = {}

            if not blend_shape_group.name:
                continue
            blend_shape_group_dict["name"] = blend_shape_group.name

            if not blend_shape_group.preset_name:
                continue
            blend_shape_group_dict["presetName"] = blend_shape_group.preset_name

            blend_shape_group_dict["binds"] = bind_dicts = []
            for bind in blend_shape_group.binds:
                bind_dict: Dict[str, object] = {}
                mesh = self.mesh_name_to_index.get(bind.mesh.mesh_object_name)
                if mesh is None:
                    logger.warning(f"{bind.mesh.mesh_object_name} => None")
                    continue
                bind_dict["mesh"] = mesh

                target_names = deep.get_list(
                    self.json_dict,
                    ["meshes", mesh, "primitives", 0, "extras", "targetNames"],
                    [],
                )

                if bind.index not in target_names:
                    continue

                bind_dict["index"] = target_names.index(bind.index)
                bind_dict["weight"] = min(max(bind.weight * 100, 0), 100)

                bind_dicts.append(bind_dict)

            blend_shape_group_dict["materialValues"] = material_value_dicts = []
            for material_value in blend_shape_group.material_values:
                if not material_value.material or not material_value.material.name:
                    continue

                material_value_dicts.append(
                    {
                        "materialName": material_value.material.name,
                        "propertyName": material_value.property_name,
                        "targetValue": [
                            float(v.value) for v in material_value.target_value
                        ],
                    }
                )

            blend_shape_group_dict["isBinary"] = blend_shape_group.is_binary
            blend_shape_group_dicts.append(blend_shape_group_dict)

        # secondaryAnimation
        secondary_animation_dict: Dict[str, Json] = {}
        vrm_extension_dict["secondaryAnimation"] = secondary_animation_dict
        collider_group_dicts: List[Json] = []
        secondary_animation_dict["colliderGroups"] = collider_group_dicts
        secondary_animation = (
            self.armature.data.vrm_addon_extension.vrm0.secondary_animation
        )
        filtered_collider_groups = [
            collider_group
            for collider_group in secondary_animation.collider_groups
            if collider_group.node
            and collider_group.node.bone_name
            and collider_group.node.bone_name in node_name_id_dict
        ]
        collider_group_names = [
            collider_group.name for collider_group in filtered_collider_groups
        ]

        # boneGroup
        bone_group_dicts: List[Json] = []
        secondary_animation_dict["boneGroups"] = bone_group_dicts
        for bone_group in secondary_animation.bone_groups:
            bone_group_dict = {
                "comment": bone_group.comment,
                "stiffiness": bone_group.stiffiness,  # noqa: SC200
                "gravityPower": bone_group.gravity_power,
                "gravityDir": {
                    # Axis confusing
                    "x": bone_group.gravity_dir[0],
                    "y": bone_group.gravity_dir[2],
                    "z": bone_group.gravity_dir[1],
                },
                "dragForce": bone_group.drag_force,
                "center": node_name_id_dict.get(bone_group.center.bone_name, -1),
                "hitRadius": bone_group.hit_radius,
                "bones": [
                    node_name_id_dict[bone.bone_name]
                    for bone in bone_group.bones
                    if bone.bone_name in node_name_id_dict
                ],
            }
            collider_group_indices: List[int] = []
            for collider_group_name in bone_group.collider_groups:
                if collider_group_name.value not in collider_group_names:
                    continue
                index = collider_group_names.index(collider_group_name.value)
                collider_group_indices.append(index)

            bone_group_dict["colliderGroups"] = collider_group_indices
            bone_group_dicts.append(bone_group_dict)

        # colliderGroups
        for collider_group in filtered_collider_groups:
            collider_group_dict: Dict[str, Json] = {}
            collider_dicts: List[Json] = []
            collider_group_dict["colliders"] = collider_dicts
            collider_group_dicts.append(collider_group_dict)
            collider_group_dict["node"] = node_name_id_dict[
                collider_group.node.bone_name
            ]

            for collider in collider_group.colliders:
                collider_object = collider.bpy_object
                if (
                    not collider_object
                    or collider_object.parent_bone not in self.armature.pose.bones
                ):
                    continue

                collider_dict: Dict[str, Json] = {}
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

                offset_x, offset_y, offset_z = self.axis_blender_to_glb(offset)
                collider_dict["offset"] = {
                    "x": offset_x,
                    "y": offset_y,
                    "z": -offset_z,
                }
                collider_dicts.append(collider_dict)

        extensions_dict = self.json_dict.get("extensions")
        if not isinstance(extensions_dict, dict):
            extensions_dict = {}
            self.json_dict["extensions"] = extensions_dict
        base_vrm_extension_dict = extensions_dict.get("VRM")
        if not isinstance(base_vrm_extension_dict, dict):
            base_vrm_extension_dict = {}
            extensions_dict["VRM"] = base_vrm_extension_dict
        base_vrm_extension_dict.update(vrm_extension_dict)

        # secondary
        node_dicts.append(
            {
                "name": "secondary",
                "translation": [0.0, 0.0, 0.0],
                "rotation": [0.0, 0.0, 0.0, 1.0],
                "scale": [1.0, 1.0, 1.0],
            }
        )
        first_scene_nodes = deep.get(self.json_dict, ["scenes", 0, "nodes"])
        if isinstance(first_scene_nodes, list):
            first_scene_nodes.append(len(node_dicts) - 1)

    def fill_empty_material(self) -> None:
        # clusterではマテリアル無しのプリミティブが許可されないため、空のマテリアルを付与する。
        material_dicts = self.json_dict.get("materials")
        if not isinstance(material_dicts, list):
            material_dicts = []
            self.json_dict["materials"] = material_dicts

        mesh_dicts = self.json_dict.get("meshes")
        if not isinstance(mesh_dicts, list):
            mesh_dicts = []
            self.json_dict["meshes"] = mesh_dicts

        empty_material_index = len(material_dicts)
        create_empty_material = False
        for mesh_dict in mesh_dicts:
            if not isinstance(mesh_dict, dict):
                continue
            primitive_dicts = mesh_dict.get("primitives")
            if not isinstance(primitive_dicts, list):
                continue
            for primitive_dict in primitive_dicts:
                if not isinstance(primitive_dict, dict):
                    continue
                material_index = primitive_dict.get("material")
                if isinstance(material_index, int):
                    continue
                primitive_dict["material"] = empty_material_index
                create_empty_material = True

        if not create_empty_material:
            return

        name = "glTF_2_0_default_material"
        material_dicts.append({"name": name})

        extensions_dict = self.json_dict.get("extensions")
        if not isinstance(extensions_dict, dict):
            extensions_dict = {}
            self.json_dict["extensions"] = extensions_dict

        vrm_dict = extensions_dict.get("VRM")
        if not isinstance(vrm_dict, dict):
            vrm_dict = {}
            extensions_dict["VRM"] = vrm_dict

        material_property_dicts = vrm_dict.get("materialProperties")
        if not isinstance(material_property_dicts, list):
            material_property_dicts = []
            vrm_dict["materialProperties"] = material_property_dicts

        material_property_dicts.append(
            {
                "name": name,
                "shader": "VRM_USE_GLTFSHADER",
                "keywordMap": {},
                "tagMap": {},
                "floatProperties": {},
                "vectorProperties": {},
                "textureProperties": {},
            }
        )

    def pack(self) -> None:
        bin_json, bin_chunk = self.glb_bin_collector.pack_all()
        self.json_dict.update(bin_json)
        if not self.json_dict["meshes"]:
            del self.json_dict["meshes"]
        if not self.json_dict["materials"]:
            del self.json_dict["materials"]
        self.result = pack_glb(self.json_dict, bin_chunk)

    def cleanup(self) -> None:
        if self.use_dummy_armature:
            bpy.data.objects.remove(self.armature, do_unlink=True)


def normalize_weights_compatible_with_gl_float(
    weights: Sequence[float],
) -> Sequence[float]:
    if abs(sum(weights) - 1.0) < float_info.epsilon:
        return weights

    def to_gl_float(array4: Sequence[float]) -> Sequence[float]:
        return list(struct.unpack("<ffff", struct.pack("<ffff", *array4)))

    # Simulate export and import
    weights = to_gl_float(weights)
    for _ in range(10):
        next_weights = to_gl_float([weights[i] / sum(weights) for i in range(4)])
        error = abs(1 - math.fsum(weights))
        next_error = abs(1 - math.fsum(next_weights))
        if error >= float_info.epsilon and error > next_error:
            weights = next_weights
        else:
            break

    return weights
