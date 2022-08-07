"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import datetime
import math
import os
import re
import secrets
import statistics
import string
import struct
import traceback
from collections import abc
from math import floor
from sys import float_info
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import bgl
import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector

from ..common import deep, gltf, shader
from ..common.char import INTERNAL_NAME_PREFIX
from ..common.mtoon_constants import MaterialMtoon
from ..common.version import version
from ..common.vrm0.human_bone import HumanBoneSpecifications
from ..editor import migration, search
from ..external import io_scene_gltf2_support
from .abstract_base_vrm_exporter import AbstractBaseVrmExporter
from .glb_bin_collection import GlbBin, GlbBinCollection, ImageBin


class LegacyVrmExporter(AbstractBaseVrmExporter):
    class KhrTextureTransform:
        def __init__(self, offset: Tuple[float, float], scale: Tuple[float, float]):
            self.offset = offset
            self.scale = scale

        def add_to(self, texture_info: Dict[str, Any]) -> None:
            texture_info.update(
                {
                    "extensions": {
                        "KHR_texture_transform": {
                            "scale": self.scale,
                            "offset": self.offset,
                        }
                    }
                }
            )

    def __init__(
        self, export_objects: List[bpy.types.Object], export_fb_ngon_encoding: bool
    ) -> None:
        self.export_objects = export_objects
        self.export_fb_ngon_encoding = export_fb_ngon_encoding
        self.vrm_version: Optional[str] = None
        self.json_dict: Dict[str, Any] = {}
        self.glb_bin_collector = GlbBinCollection()
        self.use_dummy_armature = False
        self.export_id = "BlenderVrmAddonExport" + (
            "".join(secrets.choice(string.digits) for _ in range(10))
        )
        self.mesh_name_to_index: Dict[str, int] = {}
        armatures = [obj for obj in self.export_objects if obj.type == "ARMATURE"]
        if armatures:
            self.armature = armatures[0]
        else:
            dummy_armature_key = self.export_id + "DummyArmatureKey"
            bpy.ops.icyp.make_basic_armature(
                "EXEC_DEFAULT", custom_property_name=dummy_armature_key
            )
            for obj in bpy.context.selectable_objects:
                if obj.type == "ARMATURE" and dummy_armature_key in obj:
                    self.export_objects.append(obj)
                    self.armature = obj
            if not self.armature:
                raise Exception("Failed to generate default armature")
            self.use_dummy_armature = True
        migration.migrate(self.armature.name, defer=False)

        self.original_pose_library: Optional[bpy.types.Action] = None
        self.saved_current_pose_library: Optional[bpy.types.Action] = None
        self.saved_pose_position: Optional[str] = None
        self.result: Optional[bytes] = None

    def export_vrm(self) -> Optional[bytes]:
        wm = bpy.context.window_manager
        wm.progress_begin(0, 9)
        try:
            self.vrm_version = "0.0"
            self.setup_pose()
            wm.progress_update(1)
            self.image_to_bin()
            wm.progress_update(2)
            self.armature_to_node_and_scenes_dict()
            wm.progress_update(3)
            self.material_to_dict()
            wm.progress_update(4)
            self.mesh_to_bin_and_dict()
            wm.progress_update(5)
            self.json_dict["scene"] = 0
            self.gltf_meta_to_dict()
            wm.progress_update(6)
            self.vrm_meta_to_dict()  # colliderとかmetaとか....
            wm.progress_update(7)
            self.fill_empty_material()
            wm.progress_update(8)
            self.pack()
        finally:
            try:
                self.restore_pose()
                self.cleanup()
            finally:
                wm.progress_end()
        return self.result

    @staticmethod
    def axis_blender_to_glb(vec3: Sequence[float]) -> List[float]:
        return [vec3[i] * t for i, t in zip([0, 2, 1], [-1, 1, 1])]

    def setup_pose(self) -> None:
        if bpy.context.view_layer.objects.active is not None:
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = self.armature
        bpy.ops.object.mode_set(mode="POSE")

        self.saved_pose_position = self.armature.data.pose_position
        humanoid = self.armature.data.vrm_addon_extension.vrm0.humanoid

        pose_library: Optional[bpy.types.Action] = None
        pose_index: Optional[int] = None
        if (
            humanoid.pose_library
            and humanoid.pose_library.name in bpy.data.actions
            and humanoid.pose_marker_name
        ):
            pose_library = humanoid.pose_library
            if pose_library:
                for search_pose_index, search_pose_marker in enumerate(
                    pose_library.pose_markers.values()
                ):
                    if search_pose_marker.name == humanoid.pose_marker_name:
                        pose_index = search_pose_index
                        self.armature.data.pose_position = "POSE"
                        break

        self.original_pose_library = self.armature.pose_library
        self.saved_current_pose_library = bpy.data.actions.new(
            INTERNAL_NAME_PREFIX + self.export_id + "SavedCurrentPoseLibrary"
        )

        self.armature.pose_library = self.saved_current_pose_library
        bpy.ops.poselib.pose_add(
            name=INTERNAL_NAME_PREFIX + self.export_id + "SavedCurrentPose"
        )

        if pose_library and pose_index is not None:
            self.armature.pose_library = pose_library
            bpy.ops.poselib.apply_pose(pose_index=pose_index)

    def restore_pose(self) -> None:
        if bpy.context.view_layer.objects.active is not None:
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = self.armature
        bpy.ops.object.mode_set(mode="POSE")

        if self.saved_current_pose_library:
            self.armature.pose_library = self.saved_current_pose_library
            bpy.ops.poselib.apply_pose(pose_index=0)
            bpy.ops.poselib.unlink()

        self.armature.pose_library = self.original_pose_library

        if (
            self.saved_current_pose_library
            and not self.saved_current_pose_library.users
        ):
            bpy.data.actions.remove(self.saved_current_pose_library)

        if self.saved_pose_position:
            self.armature.data.pose_position = self.saved_pose_position

        bpy.ops.object.mode_set(mode="OBJECT")

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
                for shader_vals in MaterialMtoon.texture_kind_exchange_dict.values():

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
                for k in gltf.TEXTURE_INPUT_NAMES:
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

        # thumbnail
        ext = self.armature.data.vrm_addon_extension
        if (
            ext.vrm0.meta.texture
            and ext.vrm0.meta.texture.name
            and ext.vrm0.meta.texture not in used_images
        ):
            used_images.append(ext.vrm0.meta.texture)

        image_to_image_index = (
            lambda used_image: bpy.data.images.index(used_image)
            if used_image in bpy.data.images.items()
            else len(bpy.data.images) + used_images.index(used_image)
        )
        for image in sorted(used_images, key=image_to_image_index):
            image_bin, filetype = io_scene_gltf2_support.image_to_image_bytes(image)
            ImageBin(image_bin, image.name, filetype, self.glb_bin_collector)

    def armature_to_node_and_scenes_dict(self) -> None:
        nodes = []
        scene = []
        skins = []

        bone_id_dict = {
            b.name: bone_id for bone_id, b in enumerate(self.armature.pose.bones)
        }

        def bone_to_node(b_bone: bpy.types.PoseBone) -> Dict[str, Any]:
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
            if len(node["children"]) == 0:
                del node["children"]
            return node

        human_bone_node_names = [
            human_bone.node.value
            for human_bone in self.armature.data.vrm_addon_extension.vrm0.humanoid.human_bones
        ]

        for bone in self.armature.pose.bones:
            if bone.parent is not None:
                continue

            has_human_bone = False
            if bone.name in human_bone_node_names:
                has_human_bone = True
            skin: Dict[str, Any] = {"joints": []}
            root_bone_id = bone_id_dict[bone.name]
            skin["joints"].append(root_bone_id)
            skin["skeleton"] = root_bone_id
            scene.append(root_bone_id)
            nodes.append(bone_to_node(bone))
            bone_children = list(bone.children)
            while bone_children:
                child = bone_children.pop()
                if child.name in human_bone_node_names:
                    has_human_bone = True
                nodes.append(bone_to_node(child))
                skin["joints"].append(bone_id_dict[child.name])
                bone_children.extend(list(child.children))
            nodes = sorted(nodes, key=lambda node: bone_id_dict[node["name"]])
            if has_human_bone:
                skins.append(skin)

        for skin in skins:
            skin_invert_matrix_bin = bytearray()
            f_4x4_packer = struct.Struct("<16f").pack
            for node_id in skin["joints"]:
                bone_name = nodes[node_id]["name"]
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
                bgl.GL_FLOAT,
                len(skin["joints"]),
                None,
                self.glb_bin_collector,
            )
            skin["inverseBindMatrices"] = im_bin.accessor_id

        self.json_dict.update({"scenes": [{"nodes": scene}]})
        self.json_dict.update({"nodes": nodes})
        self.json_dict.update({"skins": skins})

    def material_to_dict(self) -> None:
        glb_material_list = []
        vrm_material_props_list = []
        gltf2_io_texture_images: List[Tuple[str, bytes, int]] = []

        image_id_dict = {
            image.name: image.image_id for image in self.glb_bin_collector.image_bins
        }
        sampler_dict: Dict[Tuple[int, int, int, int], int] = {}
        texture_dict: Dict[Tuple[int, int], int] = {}

        # region texture func

        def add_texture(image_name: str, wrap_type: int, filter_type: int) -> int:
            sampler_dict_key = (wrap_type, wrap_type, filter_type, filter_type)
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
                sampler_list = self.json_dict["samplers"] = []
                for sampler in sampler_dict:
                    sampler_list.append(
                        {
                            "wrapS": sampler[0],
                            "wrapT": sampler[1],
                            "magFilter": sampler[2],
                            "minFilter": sampler[3],
                        }
                    )
            if texture_dict:
                textures = []
                for tex in texture_dict:
                    texture = {"sampler": tex[1], "source": tex[0]}
                    textures.append(texture)
                self.json_dict.update({"textures": textures})

        # region function separate by shader
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
        ) -> Dict[str, Any]:
            """transparent_method = {"OPAQUE","MASK","BLEND"}"""
            if base_color is None:
                base_color = (1, 1, 1, 1)
            if metalness is None:
                metalness = 0
            if roughness is None:
                roughness = 0.9
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
                texture_info = {
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
                normal_texture_info: Dict[str, Union[int, float]] = {
                    "index": add_texture(*normal_texture),
                    "texCoord": 0,  # TODO:
                }
                if normal_texture_scale is not None:
                    normal_texture_info["scale"] = normal_texture_scale
                if texture_transform is not None:
                    texture_transform.add_to(normal_texture_info)
                fallback_dict["normalTexture"] = normal_texture_info
            if occlusion_texture is not None:
                occlusion_texture_info = {
                    "index": add_texture(*occlusion_texture),
                    "texCoord": 0,  # TODO:
                }
                if texture_transform is not None:
                    texture_transform.add_to(occlusion_texture_info)
                fallback_dict["occlusionTexture"] = occlusion_texture_info
            if emissive_texture is not None:
                emissive_texture_info = {
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

        def make_mtoon_unversioned_extension_dict(
            b_mat: bpy.types.Material, mtoon_shader_node: bpy.types.Node
        ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
            mtoon_dict: Dict[str, Any] = {}
            mtoon_dict["name"] = b_mat.name
            mtoon_dict["shader"] = "VRM/MToon"
            mtoon_dict["keywordMap"] = {}
            keyword_map = mtoon_dict["keywordMap"]
            mtoon_dict["tagMap"] = {}
            tag_map = mtoon_dict["tagMap"]
            mtoon_dict["floatProperties"] = {}
            mtoon_float_dict: Dict[str, float] = mtoon_dict["floatProperties"]
            mtoon_dict["vectorProperties"] = {}
            mtoon_vector_dict: Dict[str, List[float]] = mtoon_dict["vectorProperties"]
            mtoon_dict["textureProperties"] = {}
            mtoon_texture_dict = mtoon_dict["textureProperties"]

            outline_width_mode = 0
            outline_color_mode = 0
            for float_key, float_prop in [
                (k, val)
                for k, val in MaterialMtoon.float_props_exchange_dict.items()
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

            def outline_keyword_set(
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

            if outline_width_mode < 1:
                outline_keyword_set(False, False, False, False)
            elif outline_width_mode < 2:
                if outline_color_mode < 1:
                    outline_keyword_set(True, False, True, False)
                else:
                    outline_keyword_set(True, False, False, True)

            elif outline_width_mode >= 2:
                if outline_color_mode < 1:
                    outline_keyword_set(False, True, True, False)
                else:
                    outline_keyword_set(False, True, False, True)

            vec_props = list(
                dict.fromkeys(MaterialMtoon.vector_props_exchange_dict.values())
            )
            for remove_vec_prop in MaterialMtoon.texture_kind_exchange_dict.values():
                if remove_vec_prop in vec_props:
                    vec_props.remove(remove_vec_prop)

            for vector_key, vector_prop in [
                (k, v)
                for k, v in MaterialMtoon.vector_props_exchange_dict.items()
                if v in vec_props
            ]:
                vector_val = shader.get_rgba_val(mtoon_shader_node, vector_prop)
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
            ) in MaterialMtoon.texture_kind_exchange_dict.items():
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
                        if bpy.app.version <= (2, 80):
                            mtoon_vector_dict[texture_key] = [
                                uv_offset_scaling_node.translation[0],
                                uv_offset_scaling_node.translation[1],
                                uv_offset_scaling_node.scale[0],
                                uv_offset_scaling_node.scale[1],
                            ]
                        else:
                            mtoon_vector_dict[texture_key] = [
                                uv_offset_scaling_node.inputs["Location"].default_value[
                                    0
                                ],
                                uv_offset_scaling_node.inputs["Location"].default_value[
                                    1
                                ],
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

            mtoon_float_dict["_MToonVersion"] = MaterialMtoon.version
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
            vrm_version = self.vrm_version
            if vrm_version is None:
                raise Exception("vrm version is None")
            if vrm_version.startswith("1."):
                mtoon_ext_dict: Dict[str, Any] = {}
                mtoon_ext_dict["properties"] = {}
                mt_prop = mtoon_ext_dict["properties"]
                mt_prop["version"] = "3.2"
                blend_mode = mtoon_float_dict.get("_BlendMode")
                if blend_mode == 0:
                    blend_mode_str = "opaque"
                elif blend_mode == 1:
                    blend_mode_str = "cutout"
                else:
                    blend_mode_str = "transparent"
                # TODO transparentWithZWrite
                mt_prop["renderMode"] = blend_mode_str

                mt_prop["cullMode"] = (
                    # mtoon_float_dict.get("_CullMode") == "back"
                    "on"
                    if b_mat.use_backface_culling
                    else "off"
                )  # no cull or bf cull
                # TODO unknown number
                mt_prop["renderQueueOffsetNumber"] = 0

                mt_prop["litFactor"] = mtoon_vector_dict.get("_Color")
                mt_prop["litMultiplyTexture"] = mtoon_texture_dict.get("_MainTex")
                mt_prop["shadeFactor"] = mtoon_vector_dict.get("_ShadeColor")
                mt_prop["shadeMultiplyTexture"] = mtoon_texture_dict.get(
                    "_ShadeTexture"
                )
                mt_prop["cutoutThresholdFactor"] = mtoon_float_dict.get("_Cutoff")
                mt_prop["shadingShiftFactor"] = mtoon_float_dict.get("_ShadeShift")
                mt_prop["shadingToonyFactor"] = mtoon_float_dict.get("_ShadeToony")
                mt_prop["shadowReceiveMultiplierFactor"] = mtoon_float_dict.get(
                    "_ReceiveShadowRate"
                )
                mt_prop[
                    "shadowReceiveMultiplierMultiplyTexture"
                ] = mtoon_texture_dict.get("_ReceiveShadowTexture")
                mt_prop["litAndShadeMixingMultiplierFactor"] = mtoon_float_dict.get(
                    "_ShadingGradeRate"
                )
                mt_prop[
                    "litAndShadeMixingMultiplierMultiplyTexture"
                ] = mtoon_texture_dict.get("_ShadingGradeTexture")
                mt_prop["lightColorAttenuationFactor"] = mtoon_float_dict.get(
                    "_LightColorAttenuation"
                )
                mt_prop["giIntensityFactor"] = mtoon_float_dict.get(
                    "_IndirectLightIntensity"
                )
                mt_prop["normalTexture"] = mtoon_texture_dict.get("_BumpMap")
                mt_prop["normalScaleFactor"] = mtoon_float_dict.get("_BumpScale")
                mt_prop["emissionFactor"] = mtoon_vector_dict.get("_EmissionColor")
                mt_prop["emissionMultiplyTexture"] = mtoon_texture_dict.get(
                    "_EmissionMap"
                )
                mt_prop["additiveTexture"] = mtoon_texture_dict.get("_SphereAdd")
                mt_prop["rimFactor"] = mtoon_vector_dict.get("_RimColor")
                mt_prop["rimMultiplyTexture"] = mtoon_texture_dict.get("_RimTexture")
                mt_prop["rimLightingMixFactor"] = mtoon_float_dict.get(
                    "_RimLightingMix"
                )
                mt_prop["rimFresnelPowerFactor"] = mtoon_float_dict.get(
                    "_RimFresnelPower"
                )
                mt_prop["rimLiftFactor"] = mtoon_float_dict.get("_RimLift")
                mt_prop["outlineWidthMode"] = [
                    "none",
                    "worldCoordinates",
                    "screenCoordinates",
                ][floor(mtoon_float_dict.get("_OutlineWidthMode", 0))]
                mt_prop["outlineWidthFactor"] = mtoon_vector_dict.get("_OutlineColor")
                mt_prop["outlineWidthMultiplyTexture"] = mtoon_texture_dict.get(
                    "_OutlineWidthTexture"
                )
                mt_prop["outlineScaledMaxDistanceFactor"] = mtoon_float_dict.get(
                    "_OutlineScaledMaxDistance"
                )
                mt_prop["outlineColorMode"] = ["fixedColor", "mixedLighting"][
                    floor(mtoon_float_dict.get("_OutlineLightingMix", 0))
                ]
                mt_prop["outlineFactor"] = mtoon_float_dict.get("_OutlineWidth")
                mt_prop["outlineLightingMixFactor"] = mtoon_float_dict.get(
                    "OutlineLightingMix"
                )

                uv_transforms = mtoon_vector_dict.get("_MainTex")
                if uv_transforms is None:
                    uv_transforms = [0, 0, 1, 1]
                mt_prop["mainTextureLeftBottomOriginOffset"] = uv_transforms[0:2]
                mt_prop["mainTextureLeftBottomOriginScale"] = uv_transforms[2:4]
                mt_prop["uvAnimationMaskTexture"] = mtoon_texture_dict.get(
                    "_UvAnimMaskTexture"
                )
                mt_prop["uvAnimationScrollXSpeedFactor"] = mtoon_float_dict.get(
                    "_UvAnimScrollX"
                )
                mt_prop["uvAnimationScrollYSpeedFactor"] = mtoon_float_dict.get(
                    "_UvAnimScrollY"
                )
                mt_prop["uvAnimationRotationSpeedFactor"] = mtoon_float_dict.get(
                    "_UvAnimRotation"
                )
                garbage_list = []
                for k, v in mt_prop.items():
                    if v is None:
                        garbage_list.append(k)
                for garbage in garbage_list:
                    mt_prop.pop(garbage)

                pbr_dict["extensions"].update({"VRMC_materials_mtoon": mtoon_ext_dict})
            return mtoon_dict, pbr_dict

        def make_gltf_mat_dict(
            b_mat: bpy.types.Material, gltf_shader_node: bpy.types.Node
        ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
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
                base_color=shader.get_rgba_val(gltf_shader_node, "base_Color"),
                metalness=shader.get_float_value(gltf_shader_node, "metallic"),
                roughness=shader.get_float_value(gltf_shader_node, "roughness"),
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
                    print(socket_name)

            pbr_tex_add("normalTexture", "normal")
            pbr_tex_add("emissiveTexture", "emissive_texture")
            pbr_tex_add("occlusionTexture", "occlusion_texture")
            emissive_factor = shader.get_rgba_val(gltf_shader_node, "emissive_color")
            if emissive_factor is None:
                emissive_factor = [0, 0, 0]
            else:
                emissive_factor = emissive_factor[0:3]
            pbr_dict["emissiveFactor"] = emissive_factor

            return gltf_dict, pbr_dict

        def make_transzw_mat_dict(
            b_mat: bpy.types.Material, transzw_shader_node: bpy.types.Node
        ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
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
            gltf2_io_texture_info: Any,
        ) -> Dict[str, Union[int, float]]:
            image = gltf2_io_texture_info.index.source
            found = False
            for (name, data, index) in gltf2_io_texture_images:
                if name != image.name or data != image.buffer_view.data:
                    continue
                image_index = index
                image_name = {value: key for key, value in image_id_dict.items()}[
                    image_index
                ]
                found = True
                break
            if not found:
                image_index = self.glb_bin_collector.get_new_image_id()
                gltf2_io_texture_images.append(
                    (image.name, image.buffer_view.data, image_index)
                )
                image_base_name = re.sub(
                    r"^BlenderVrmAddonImport[0-9]+Image[0-9]+_", "", image.name
                )
                for count in range(100000):
                    image_name = image_base_name
                    if count:
                        image_name += "." + str(count)
                    if image_name not in image_id_dict:
                        break
                image_id_dict[image_name] = image_index
                ImageBin(
                    image.buffer_view.data,
                    image_name,
                    image.mime_type,
                    self.glb_bin_collector,
                )

            sampler = gltf2_io_texture_info.index.sampler
            if sampler is None:
                sampler_dict_key = (
                    bgl.GL_REPEAT,
                    bgl.GL_REPEAT,
                    bgl.GL_LINEAR,
                    bgl.GL_LINEAR,
                )
            else:
                sampler_dict_key = (
                    sampler.wrap_s or bgl.GL_REPEAT,
                    sampler.wrap_t or bgl.GL_REPEAT,
                    sampler.mag_filter or bgl.GL_LINEAR,
                    sampler.min_filter or bgl.GL_LINEAR,
                )

                # VRoid Hub may not support a mipmap
                if sampler_dict_key[3] in [
                    bgl.GL_NEAREST_MIPMAP_LINEAR,
                    bgl.GL_NEAREST_MIPMAP_NEAREST,
                ]:
                    sampler_dict_key = sampler_dict_key[0:3] + (bgl.GL_NEAREST,)
                elif sampler_dict_key[3] in [
                    bgl.GL_LINEAR_MIPMAP_NEAREST,
                    bgl.GL_LINEAR_MIPMAP_LINEAR,
                ]:
                    sampler_dict_key = sampler_dict_key[0:3] + (bgl.GL_LINEAR,)

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
            return texture_info

        def make_non_vrm_mat_dict(
            b_mat: bpy.types.Material,
        ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
            vrm_dict = {
                "name": b_mat.name,
                "shader": "VRM_USE_GLTFSHADER",
                "keywordMap": {},
                "tagMap": {},
                "floatProperties": {},
                "vectorProperties": {},
                "textureProperties": {},
            }
            fallback = (vrm_dict, {"name": b_mat.name})

            pbr_dict: Dict[str, Any] = {}
            pbr_dict["name"] = b_mat.name

            if bpy.app.version < (2, 83):
                return fallback

            try:
                from io_scene_gltf2.blender.exp.gltf2_blender_gather_materials import (
                    gather_material,
                )  # pyright: reportMissingImports=false
            except ImportError as e:
                print(f"Failed to import glTF 2.0 Add-on: {e}")
                return fallback

            gltf2_io_material: Optional[Any] = None
            export_settings: Dict[str, Any] = {
                # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L522
                "timestamp": datetime.datetime.now(),
                # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L258-L268
                # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L552
                "gltf_materials": True,
                # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L120-L137
                # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L532
                "gltf_format": "GLB",
                # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L154-L168
                # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L533
                "gltf_image_format": "AUTO",
                # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L329-L333
                # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L569
                "gltf_extras": True,
                # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L611-L633
                "gltf_user_extensions": [],
                # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L606
                "gltf_binary": bytearray(),
                # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L176-L184
                # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L530
                "gltf_keep_original_textures": False,
                # https://github.com/KhronosGroup/glTF-Blender-IO/blob/bfe4ff8b1b5c26ba17b0531b67798376147d9fa7/addons/io_scene_gltf2/__init__.py
                "gltf_original_specular": False,
            }
            try:
                if bpy.app.version >= (3, 2):
                    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/master/addons/io_scene_gltf2/blender/exp/gltf2_blender_gather_primitives.py#L71-L96
                    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/9e08d423a803da52eb08fbc93d9aa99f3f681a27/addons/io_scene_gltf2/blender/exp/gltf2_blender_gather_materials.py#L42
                    gltf2_io_material = gather_material(b_mat, 0, export_settings)
                elif bpy.app.version >= (2, 91):
                    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/abd8380e19dbe5e5fb9042513ad6b744032bc9bc/addons/io_scene_gltf2/blender/exp/gltf2_blender_gather_materials.py#L32
                    gltf2_io_material = gather_material(b_mat, export_settings)
                else:
                    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/ac3471cae42b34fc69fda75fa404117272fa9560/addons/io_scene_gltf2/blender/exp/gltf2_blender_gather_materials.py#L32
                    gltf2_io_material = gather_material(
                        b_mat, not b_mat.use_backface_culling, export_settings
                    )

                if isinstance(gltf2_io_material.alpha_cutoff, (int, float)):
                    pbr_dict["alphaCutoff"] = gltf2_io_material.alpha_cutoff
                if isinstance(gltf2_io_material.alpha_mode, str):
                    pbr_dict["alphaMode"] = gltf2_io_material.alpha_mode
                if isinstance(gltf2_io_material.double_sided, bool):
                    pbr_dict["doubleSided"] = gltf2_io_material.double_sided
                if isinstance(gltf2_io_material.emissive_factor, abc.Sequence):
                    pbr_dict["emissiveFactor"] = gltf2_io_material.emissive_factor
                if gltf2_io_material.emissive_texture is not None:
                    pbr_dict["emissiveTexture"] = add_gltf2_io_texture(
                        gltf2_io_material.emissive_texture
                    )
                if isinstance(gltf2_io_material.extensions, dict):
                    pbr_dict["extensions"] = {}
                    # https://github.com/KhronosGroup/glTF/tree/master/extensions/2.0/Khronos/KHR_materials_unli
                    if (
                        gltf2_io_material.extensions.get("KHR_materials_unlit")
                        is not None
                    ):
                        pbr_dict["extensions"].update({"KHR_materials_unlit": {}})
                if gltf2_io_material.normal_texture is not None:
                    pbr_dict["normalTexture"] = add_gltf2_io_texture(
                        gltf2_io_material.normal_texture
                    )
                if gltf2_io_material.occlusion_texture is not None:
                    pbr_dict["occlusionTexture"] = add_gltf2_io_texture(
                        gltf2_io_material.occlusion_texture
                    )
                if gltf2_io_material.pbr_metallic_roughness is not None:
                    pbr_metallic_roughness: Dict[str, Any] = {}
                    if isinstance(
                        gltf2_io_material.pbr_metallic_roughness.base_color_factor,
                        abc.Sequence,
                    ):
                        pbr_metallic_roughness[
                            "baseColorFactor"
                        ] = gltf2_io_material.pbr_metallic_roughness.base_color_factor
                    if (
                        gltf2_io_material.pbr_metallic_roughness.base_color_texture
                        is not None
                    ):
                        pbr_metallic_roughness[
                            "baseColorTexture"
                        ] = add_gltf2_io_texture(
                            gltf2_io_material.pbr_metallic_roughness.base_color_texture
                        )
                    if isinstance(
                        gltf2_io_material.pbr_metallic_roughness.metallic_factor,
                        (int, float),
                    ):
                        pbr_metallic_roughness[
                            "metallicFactor"
                        ] = gltf2_io_material.pbr_metallic_roughness.metallic_factor
                    if (
                        gltf2_io_material.pbr_metallic_roughness.metallic_roughness_texture
                        is not None
                    ):
                        pbr_metallic_roughness[
                            "metallicRoughnessTexture"
                        ] = add_gltf2_io_texture(
                            gltf2_io_material.pbr_metallic_roughness.metallic_roughness_texture
                        )
                    if isinstance(
                        gltf2_io_material.pbr_metallic_roughness.roughness_factor,
                        (int, float),
                    ):
                        pbr_metallic_roughness[
                            "roughnessFactor"
                        ] = gltf2_io_material.pbr_metallic_roughness.roughness_factor
                    pbr_dict["pbrMetallicRoughness"] = pbr_metallic_roughness
            except KeyError as e:
                traceback.print_exc()
                print(f"glTF Material KeyError: {e}")
                return fallback
            except TypeError as e:
                traceback.print_exc()
                print(f"glTF Material TypeError: {e}")
                return fallback
            except Exception as e:
                traceback.print_exc()
                print(f"glTF Material Exception: {e}")
                return fallback

            return vrm_dict, pbr_dict

        # endregion function separate by shader

        for b_mat in search.export_materials(self.export_objects):
            material_properties_dict: Dict[str, Any] = {}
            pbr_dict: Dict[str, Any] = {}
            if not b_mat.node_tree:
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
        self.json_dict.update({"materials": glb_material_list})
        vrm_version = self.vrm_version
        if vrm_version is None:
            raise Exception("vrm version is None")
        if vrm_version.startswith("0."):
            self.json_dict.update(
                {"extensions": {"VRM": {"materialProperties": vrm_material_props_list}}}
            )

    def joint_id_from_node_name_solver(
        self, node_name: str, node_id_dict: Dict[str, int]
    ) -> int:
        try:
            node_id = node_id_dict[node_name]
            joints = self.json_dict["skins"][0]["joints"]
            if not isinstance(joints, list):
                raise Exception("joints is not list")
            return joints.index(node_id)
        except (ValueError, KeyError):
            print(f"{node_name} bone may be not exist")
            return -1  # 存在しないボーンを指してる場合は-1を返す

    @staticmethod
    def fetch_morph_vertex_normal_difference(
        mesh_data: bpy.types.Mesh,
    ) -> Dict[str, List[List[float]]]:
        morph_normal_diff_dict = {}
        vert_base_normal_dict = {}
        for kb in mesh_data.shape_keys.key_blocks:
            # 頂点のノーマルではなくsplit(loop)のノーマルを使う
            # https://github.com/KhronosGroup/glTF-Blender-IO/pull/1129
            split_normals = kb.normals_split_get()

            vertex_normal_vectors = [Vector([0.0, 0.0, 0.0])] * len(mesh_data.vertices)
            for loop_index in range(len(split_normals) // 3):
                loop = mesh_data.loops[loop_index]
                v = Vector(
                    [
                        split_normals[loop_index * 3 + 0],
                        split_normals[loop_index * 3 + 1],
                        split_normals[loop_index * 3 + 2],
                    ]
                )
                vertex_normal_vectors[loop.vertex_index] = (
                    vertex_normal_vectors[loop.vertex_index] + v
                )

            vertex_normals = [0.0] * len(vertex_normal_vectors) * 3
            for index, _ in enumerate(vertex_normal_vectors):
                n = vertex_normal_vectors[index].normalized()
                if n.magnitude < float_info.epsilon:
                    vertex_normals[index * 3 + 2] = 1.0
                    continue
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
            if len([m for m in mesh.modifiers if m.type == "ARMATURE"]) > 0:
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
        self.json_dict["meshes"] = []
        vrm_version = self.vrm_version
        if vrm_version is None:
            raise Exception("vrm version is None")

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
            self.json_dict["nodes"].append(node_dict)

            mesh_node_id = len(self.json_dict["nodes"]) - 1

            if is_skin_mesh:
                self.json_dict["scenes"][0]["nodes"].append(mesh_node_id)
            else:
                if mesh.parent_type == "BONE":
                    parent_node = (
                        [
                            node
                            for node in self.json_dict["nodes"]
                            if node["name"] == mesh.parent_bone
                        ]
                        + [None]
                    )[0]
                elif mesh.parent_type == "OBJECT":
                    parent_node = (
                        [
                            node
                            for node in self.json_dict["nodes"]
                            if node["name"] == mesh.parent.name
                        ]
                        + [None]
                    )[0]
                else:
                    parent_node = None
                base_pos = [0, 0, 0]
                if parent_node:
                    if "children" in parent_node:
                        parent_node["children"].append(mesh_node_id)
                    else:
                        parent_node["children"] = [mesh_node_id]
                    if mesh.parent_type == "BONE":
                        base_pos = (
                            self.armature.matrix_world
                            @ self.armature.pose.bones[mesh.parent_bone].matrix.to_4x4()
                        ).to_translation()
                    else:
                        base_pos = mesh.parent.matrix_world.to_translation()
                else:
                    self.json_dict["scenes"][0]["nodes"].append(mesh_node_id)
                mesh_pos = mesh.matrix_world.to_translation()
                relate_pos = [mesh_pos[i] - base_pos[i] for i in range(3)]
                self.json_dict["nodes"][mesh_node_id][
                    "translation"
                ] = self.axis_blender_to_glb(relate_pos)

            # region hell
            # Check added to resolve https://github.com/saturday06/VRM_Addon_for_Blender/issues/70
            if bpy.context.view_layer.objects.active is not None:
                bpy.ops.object.mode_set(mode="OBJECT")

            # https://docs.blender.org/api/2.80/bpy.types.Depsgraph.html
            depsgraph = bpy.context.evaluated_depsgraph_get()
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
            bpy.context.view_layer.objects.active = mesh
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

            # region temporary used
            mat_id_dict = {
                mat["name"]: i for i, mat in enumerate(self.json_dict["materials"])
            }
            material_slot_dict = {
                i: mat.name for i, mat in enumerate(mesh.material_slots) if mat.name
            }
            node_id_dict = {
                node["name"]: i for i, node in enumerate(self.json_dict["nodes"])
            }

            v_group_name_dict = {i: vg.name for i, vg in enumerate(mesh.vertex_groups)}
            fmin, fmax = gltf.FLOAT_NEGATIVE_MAX, gltf.FLOAT_POSITIVE_MAX
            unique_vertex_id = 0
            # {(uv...,vertex_index):unique_vertex_id} (uvと頂点番号が同じ頂点は同じものとして省くようにする)
            unique_vertex_dict: Dict[Tuple[Any, ...], int] = {}
            uvlayers_dict = {
                i: uvlayer.name for i, uvlayer in enumerate(mesh_data.uv_layers)
            }

            # endregion  temporary_used
            primitive_index_bin_dict: Dict[Optional[int], bytearray] = {
                mat_id_dict[mat.name]: bytearray()
                for mat in mesh.material_slots
                if mat.name
            }
            if not primitive_index_bin_dict:
                primitive_index_bin_dict[None] = bytearray()
            primitive_index_vertex_count: Dict[Optional[int], int] = {
                mat_id_dict[mat.name]: 0 for mat in mesh.material_slots if mat.name
            }
            if not primitive_index_vertex_count:
                primitive_index_vertex_count[None] = 0

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
                morph_normal_diff_dict = (
                    self.fetch_morph_vertex_normal_difference(mesh_data)
                    if vrm_version.startswith("0.")
                    else {}
                )  # {morphname:{vertexid:[diff_X,diff_y,diff_z]}}
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
                        if vrm_version.startswith("0."):
                            shape_normal_bin_dict[shape_name].extend(
                                float_vec3_packer(
                                    *self.axis_blender_to_glb(
                                        morph_normal_diff_dict[shape_name][
                                            loop.vert.index
                                        ]
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
                            print(
                                f"Joints on vertex id:{loop.vert.index} in: {mesh.name} are truncated"
                            )
                            weight_and_joint_list = weight_and_joint_list[:4]

                        weights = [weight for weight, _ in weight_and_joint_list]
                        joints = [joint for _, joint in weight_and_joint_list]

                        if sum(weights) < float_info.epsilon:
                            print(
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
                                        bone_name = human_bone.node.value
                                if (
                                    bone_name is None
                                    or bone_name not in self.armature.data.bones
                                ):
                                    raise Exception("No hips bone found")
                            bone_index = next(
                                index
                                for index, node in enumerate(self.json_dict["nodes"])
                                if node["name"] == bone_name
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
                    bgl.GL_UNSIGNED_INT,
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

            mesh_index = len(self.json_dict["meshes"])
            node_dict["mesh"] = mesh_index
            if is_skin_mesh:
                # TODO: 決め打ちってどうよ:一体のモデルなのだから2つもあっては困る(から決め打ち(やめろ(やだ))
                node_dict["skin"] = 0

            pos_glb = GlbBin(
                position_bin,
                "VEC3",
                bgl.GL_FLOAT,
                unique_vertex_id,
                position_min_max,
                self.glb_bin_collector,
            )
            nor_glb = GlbBin(
                normal_bin,
                "VEC3",
                bgl.GL_FLOAT,
                unique_vertex_id,
                None,
                self.glb_bin_collector,
            )
            uv_glbs = [
                GlbBin(
                    texcoord_bin,
                    "VEC2",
                    bgl.GL_FLOAT,
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
                    bgl.GL_UNSIGNED_SHORT,
                    unique_vertex_id,
                    None,
                    self.glb_bin_collector,
                )
                weights_glb = GlbBin(
                    weights_bin,
                    "VEC4",
                    bgl.GL_FLOAT,
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
                        bgl.GL_FLOAT,
                        unique_vertex_id,
                        morph_minmax,
                        self.glb_bin_collector,
                    )
                    for morph_pos_bin, morph_minmax in zip(
                        shape_pos_bin_dict.values(), shape_min_max_dict.values()
                    )
                ]
                if vrm_version.startswith("0."):
                    morph_normal_glbs = [
                        GlbBin(
                            morph_normal_bin,
                            "VEC3",
                            bgl.GL_FLOAT,
                            unique_vertex_id,
                            None,
                            self.glb_bin_collector,
                        )
                        for morph_normal_bin in shape_normal_bin_dict.values()
                    ]

            primitive_list = []
            for primitive_id, index_glb in primitive_glbs_dict.items():
                primitive: Dict[str, Any] = {"mode": 4}
                if primitive_id is not None:
                    primitive["material"] = primitive_id
                primitive["indices"] = index_glb.accessor_id
                primitive["attributes"] = {
                    "POSITION": pos_glb.accessor_id,
                    "NORMAL": nor_glb.accessor_id,
                }
                if is_skin_mesh:
                    if joints_glb is None:
                        raise Exception("joints glb is None")
                    if weights_glb is None:
                        raise Exception("weights glb is None")
                    primitive["attributes"].update(
                        {
                            "JOINTS_0": joints_glb.accessor_id,
                            "WEIGHTS_0": weights_glb.accessor_id,
                        }
                    )
                primitive["attributes"].update(
                    {
                        f"TEXCOORD_{i}": uv_glb.accessor_id
                        for i, uv_glb in enumerate(uv_glbs)
                    }
                )
                if shape_pos_bin_dict:
                    vrm_version = self.vrm_version
                    if vrm_version is None:
                        raise Exception("vrm version is None")
                    if vrm_version.startswith("0."):
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
                    elif morph_pos_glbs:
                        primitive["targets"] = [
                            {"POSITION": morph_pos_glb.accessor_id}
                            for morph_pos_glb in morph_pos_glbs
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

            self.json_dict["meshes"].append(mesh_dict)
            bm.free()
            # endregion hell

            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.mode_set(mode="OBJECT")

    def exporter_name(self) -> str:
        v = version()
        if os.environ.get("BLENDER_VRM_USE_TEST_EXPORTER_VERSION") == "true":
            v = (999, 999, 999)
        return "saturday06_blender_vrm_exporter_experimental_" + ".".join(map(str, v))

    def gltf_meta_to_dict(self) -> None:
        extensions_used = [
            "VRM",
            "KHR_materials_unlit",
            "KHR_texture_transform",
            "VRMC_materials_mtoon",
        ]
        if self.export_fb_ngon_encoding:
            extensions_used.append("FB_ngon_encoding")
        gltf_meta_dict = {
            "extensionsUsed": extensions_used,
            "asset": {
                "generator": self.exporter_name(),
                "version": "2.0",  # glTF version
            },
        }

        self.json_dict.update(gltf_meta_dict)

    def vrm_meta_to_dict(self) -> None:
        # materialProperties は material_to_dict()で処理する
        # region vrm_extension
        meta = self.armature.data.vrm_addon_extension.vrm0.meta
        vrm_extension_dict: Dict[str, Any] = {}
        vrm_version = self.vrm_version
        if vrm_version is None:
            raise Exception("vrm version is None")
        if vrm_version.startswith("0."):
            vrm_extension_dict["exporterVersion"] = self.exporter_name()
        vrm_extension_dict["specVersion"] = self.vrm_version
        # region meta
        vrm_extension_dict["meta"] = {
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
        if meta.texture and meta.texture.name:
            thumbnail_indices = [
                index
                for index, image_bin in enumerate(self.glb_bin_collector.image_bins)
                if image_bin.name == meta.texture.name
            ]
            if thumbnail_indices:
                if "samplers" not in self.json_dict:
                    self.json_dict["samplers"] = []
                self.json_dict["samplers"].append(
                    {
                        "magFilter": bgl.GL_LINEAR,
                        "minFilter": bgl.GL_LINEAR,
                        "wrapS": bgl.GL_REPEAT,
                        "wrapT": bgl.GL_REPEAT,
                    }
                )
                if "textures" not in self.json_dict:
                    self.json_dict["textures"] = []
                self.json_dict["textures"].append(
                    {
                        "sampler": len(self.json_dict["samplers"]) - 1,
                        "source": thumbnail_indices[0],
                    },
                )
                vrm_extension_dict["meta"]["texture"] = (
                    len(self.json_dict["textures"]) - 1
                )
        # endregion meta

        # region humanoid
        node_name_id_dict = {
            node["name"]: i for i, node in enumerate(self.json_dict["nodes"])
        }
        humanoid_dict: Dict[str, Any] = {"humanBones": []}
        vrm_extension_dict["humanoid"] = humanoid_dict
        humanoid = self.armature.data.vrm_addon_extension.vrm0.humanoid
        for human_bone_name in HumanBoneSpecifications.all_names:
            for human_bone in humanoid.human_bones:
                if (
                    human_bone.bone != human_bone_name
                    or not human_bone.node.value
                    or human_bone.node.value not in node_name_id_dict
                ):
                    continue
                human_bone_dict = {
                    "bone": human_bone_name,
                    "node": node_name_id_dict[human_bone.node.value],
                    "useDefaultValues": human_bone.use_default_values,
                }
                humanoid_dict["humanBones"].append(human_bone_dict)
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
        # endregion humanoid

        # region firstPerson
        first_person_dict: Dict[str, Any] = {}
        vrm_extension_dict["firstPerson"] = first_person_dict
        first_person = self.armature.data.vrm_addon_extension.vrm0.first_person

        if first_person.first_person_bone.value:
            first_person_dict["firstPersonBone"] = node_name_id_dict[
                first_person.first_person_bone.value
            ]
        else:
            name = [
                human_bone.node.value
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

        mesh_annotation_dicts: List[Dict[str, Any]] = []
        first_person_dict["meshAnnotations"] = mesh_annotation_dicts
        for mesh_annotation in first_person.mesh_annotations:
            if (
                mesh_annotation.mesh
                and mesh_annotation.mesh.value
                and mesh_annotation.mesh.value in bpy.data.objects
                and bpy.data.objects[mesh_annotation.mesh.value].type == "MESH"
            ):
                matched_mesh_indices = [
                    i
                    for i, mesh in enumerate(self.json_dict["meshes"])
                    if mesh["name"]
                    == bpy.data.objects[mesh_annotation.mesh.value].data.name
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
        for (look_at, look_at_dict_key) in [
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
        # endregion firstPerson
        # region blendShapeMaster
        vrm_extension_dict["blendShapeMaster"] = {}
        vrm_extension_dict["blendShapeMaster"][
            "blendShapeGroups"
        ] = blend_shape_group_dicts = []

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
                bind_dict: Dict[str, Any] = {}
                mesh = self.mesh_name_to_index.get(bind.mesh.value)
                if mesh is None:
                    print(f"{bind.mesh.value} => None")
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
        # endregion blendShapeMaster

        # region secondaryAnimation
        secondary_animation_dict: Dict[str, Any] = {}
        vrm_extension_dict["secondaryAnimation"] = secondary_animation_dict
        collider_group_dicts: List[Dict[str, Any]] = []
        secondary_animation_dict["colliderGroups"] = collider_group_dicts
        secondary_animation = (
            self.armature.data.vrm_addon_extension.vrm0.secondary_animation
        )
        filtered_collider_groups = [
            collider_group
            for collider_group in secondary_animation.collider_groups
            if collider_group.node
            and collider_group.node.value
            and collider_group.node.value in node_name_id_dict
        ]
        collider_group_names = [
            collider_group.name for collider_group in filtered_collider_groups
        ]

        # region boneGroup
        secondary_animation_dict["boneGroups"] = bone_group_dicts = []
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
                "center": node_name_id_dict.get(bone_group.center.value, -1),
                "hitRadius": bone_group.hit_radius,
                "bones": [
                    node_name_id_dict[bone.value]
                    for bone in bone_group.bones
                    if bone.value in node_name_id_dict
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
        # endregion boneGroup

        # region colliderGroups
        for collider_group in filtered_collider_groups:
            collider_group_dict: Dict[str, Any] = {}
            collider_group_dict["colliders"] = collider_dicts = []
            collider_group_dicts.append(collider_group_dict)
            collider_group_dict["node"] = node_name_id_dict[collider_group.node.value]

            for collider in collider_group.colliders:
                collider_object = collider.bpy_object
                if (
                    not collider_object
                    or collider_object.parent_bone not in self.armature.pose.bones
                ):
                    continue

                collider_dict: Dict[str, Any] = {}
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

                collider_dict["offset"] = dict(
                    zip(
                        ("x", "y", "z"),
                        self.axis_blender_to_glb(offset),
                    )
                )
                collider_dict["offset"]["z"] = collider_dict["offset"]["z"] * -1
                collider_dicts.append(collider_dict)
        # endregion colliderGroups
        # endregion secondaryAnimation
        extension_name = "VRM" if vrm_version.startswith("0.") else "VRMC_vrm"
        self.json_dict["extensions"][extension_name].update(vrm_extension_dict)
        # endregion vrm_extension

        # region secondary
        self.json_dict["nodes"].append(
            {
                "name": "secondary",
                "translation": [0.0, 0.0, 0.0],
                "rotation": [0.0, 0.0, 0.0, 1.0],
                "scale": [1.0, 1.0, 1.0],
            }
        )
        self.json_dict["scenes"][0]["nodes"].append(len(self.json_dict["nodes"]) - 1)

    def fill_empty_material(self) -> None:
        # clusterではマテリアル無しのプリミティブが許可されないため、空のマテリアルを付与する。
        empty_material_index = len(self.json_dict["materials"])
        create_empty_material = False
        for mesh_dict in self.json_dict["meshes"]:
            primitives = mesh_dict.get("primitives")
            if not isinstance(primitives, abc.Iterable):
                continue
            for primitive_dict in primitives:
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
        self.json_dict["materials"].append({"name": name})
        self.json_dict["extensions"]["VRM"]["materialProperties"].append(
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
        self.result = gltf.pack_glb(self.json_dict, bin_chunk)

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


def matrix_loc_rot_scale(
    loc: Sequence[Union[int, float]],
    rot: Quaternion,
    scale: Sequence[Union[int, float]],
) -> Matrix:
    if bpy.app.version >= (2, 83):
        return Matrix.LocRotScale(loc, rot, scale)

    return (
        Matrix.Translation(loc)
        @ rot.to_matrix().to_4x4()
        @ Matrix.Scale(scale[0], 4, (1, 0, 0))
        @ Matrix.Scale(scale[1], 4, (0, 1, 0))
        @ Matrix.Scale(scale[2], 4, (0, 0, 1))
    )
