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
import string
import struct
import tempfile
import traceback
from collections import OrderedDict, abc
from math import floor
from sys import float_info
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import bgl
import bmesh
import bpy
from mathutils import Matrix, Quaternion

from ..common import deep, gltf
from ..common.char import INTERNAL_NAME_PREFIX
from ..common.human_bone import HumanBones
from ..common.mtoon_constants import MaterialMtoon
from ..common.version import version
from ..editor import migration, search
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

    MESH_CONVERTIBLE_OBJECT_TYPES = [
        "CURVE",
        "FONT",
        "MESH",
        # "META",  # Disable until the glTF 2.0 add-on supports it
        "SURFACE",
    ]

    def __init__(self, export_objects: List[bpy.types.Object]) -> None:
        self.export_objects = export_objects
        self.vrm_version: Optional[str] = None
        self.json_dic: Dict[str, Any] = OrderedDict()
        self.bin = b""
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
        self.vrm_version = "0.0"
        try:
            self.setup_pose()
            self.image_to_bin()
            self.armature_to_node_and_scenes_dic()
            self.material_to_dic()
            self.mesh_to_bin_and_dic()
            self.json_dic["scene"] = 0
            self.gltf_meta_to_dic()
            self.vrm_meta_to_dic()  # colliderとかmetaとか....
            self.pack()
        finally:
            self.restore_pose()
            self.cleanup()
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
        humanoid_props = self.armature.data.vrm_addon_extension.vrm0.humanoid

        pose_library: Optional[bpy.types.Action] = None
        pose_index: Optional[int] = None
        if (
            humanoid_props.pose_library
            and humanoid_props.pose_library.name in bpy.data.actions
            and humanoid_props.pose_marker_name
        ):
            pose_library = humanoid_props.pose_library
            if pose_library:
                for search_pose_index, search_pose_marker in enumerate(
                    pose_library.pose_markers.values()
                ):
                    if search_pose_marker.name == humanoid_props.pose_marker_name:
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
        used_materials = []
        for mesh in [
            obj
            for obj in self.export_objects
            if obj.type in self.MESH_CONVERTIBLE_OBJECT_TYPES
        ]:
            for mat in mesh.data.materials:
                if mat and mat not in used_materials:
                    if "vrm_shader" in mat:
                        del mat["vrm_shader"]
                    used_materials.append(mat)

        # image fetching
        for node, mat in search.shader_nodes_and_materials(used_materials):
            if node.node_tree["SHADER"] == "MToon_unversioned":
                mat["vrm_shader"] = "MToon_unversioned"
                for shader_vals in MaterialMtoon.texture_kind_exchange_dic.values():

                    # Support models that were loaded by earlier versions (1.3.5 or earlier), which had this typo
                    #
                    # Those models have node.inputs["NomalmapTexture"] instead of "NormalmapTexture".  # noqa: SC100
                    # But 'shader_vals' which comes from MaterialMtoon.texture_kind_exchange_dic is "NormalmapTexture".
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
            if (
                image.source == "FILE"
                and not image.is_dirty
                and image.file_format in ["PNG", "JPEG"]
            ):
                if image.packed_file is not None:
                    image_bin = image.packed_file.data
                else:
                    with open(image.filepath_from_user(), "rb") as f:
                        image_bin = f.read()
                filetype = "image/" + image.file_format.lower()
            else:
                filetype = "image/png"
                with tempfile.TemporaryDirectory() as temp_dir:
                    export_image: Optional[bpy.types.Image] = None
                    try:
                        if image.size[0] > 0 and image.size[1] > 0:
                            export_image = image.copy()
                            # https://github.com/KhronosGroup/glTF-Blender-IO/issues/894#issuecomment-579094775
                            export_image.update()
                            # https://github.com/KhronosGroup/glTF-Blender-IO/commit/0ea9e74c40977a36bbccb7b823fe8bf5955fc528
                            export_image.pixels = image.pixels[:]
                        else:
                            print('Failed to load image "{image.name}"')
                            export_image = bpy.data.images.new(
                                INTERNAL_NAME_PREFIX + "TempVrmExport-" + image.name,
                                width=1,
                                height=1,
                            )
                        filepath = os.path.join(temp_dir, "image.png")
                        export_image.filepath_raw = filepath
                        export_image.file_format = "PNG"
                        export_image.save()
                    finally:
                        if export_image is not None:
                            bpy.data.images.remove(export_image)
                    with open(filepath, "rb") as f:
                        image_bin = f.read()

            name = image.name
            ImageBin(image_bin, name, filetype, self.glb_bin_collector)

    def armature_to_node_and_scenes_dic(self) -> None:
        nodes = []
        scene = []
        skins = []

        bone_id_dic = {
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
            node = OrderedDict(
                {
                    "name": b_bone.name,
                    "translation": self.axis_blender_to_glb(translation),
                    # "rotation":[0,0,0,1],
                    # "scale":[1,1,1],
                    "children": [bone_id_dic[ch.name] for ch in b_bone.children],
                }
            )
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
            root_bone_id = bone_id_dic[bone.name]
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
                skin["joints"].append(bone_id_dic[child.name])
                bone_children += list(child.children)
            nodes = sorted(nodes, key=lambda node: bone_id_dic[node["name"]])
            if has_human_bone:
                skins.append(skin)

        for skin in skins:
            skin_invert_matrix_bin = b""
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
                skin_invert_matrix_bin += f_4x4_packer(*inv_matrix)

            im_bin = GlbBin(
                skin_invert_matrix_bin,
                "MAT4",
                bgl.GL_FLOAT,
                len(skin["joints"]),
                None,
                self.glb_bin_collector,
            )
            skin["inverseBindMatrices"] = im_bin.accessor_id

        self.json_dic.update({"scenes": [{"nodes": scene}]})
        self.json_dic.update({"nodes": nodes})
        self.json_dic.update({"skins": skins})

    def material_to_dic(self) -> None:
        glb_material_list = []
        vrm_material_props_list = []
        gltf2_io_texture_images: List[Tuple[str, bytes, int]] = []

        image_id_dic = {
            image.name: image.image_id for image in self.glb_bin_collector.image_bins
        }
        sampler_dic: Dict[Tuple[int, int, int, int], int] = OrderedDict()
        texture_dic: Dict[Tuple[int, int], int] = OrderedDict()

        # region texture func

        def add_texture(image_name: str, wrap_type: int, filter_type: int) -> int:
            sampler_dic_key = (wrap_type, wrap_type, filter_type, filter_type)
            if sampler_dic_key not in sampler_dic.keys():
                sampler_dic.update({sampler_dic_key: len(sampler_dic)})
            if (
                image_id_dic[image_name],
                sampler_dic[sampler_dic_key],
            ) not in texture_dic.keys():
                texture_dic.update(
                    {
                        (
                            image_id_dic[image_name],
                            sampler_dic[sampler_dic_key],
                        ): len(texture_dic)
                    }
                )
            return texture_dic[(image_id_dic[image_name], sampler_dic[sampler_dic_key])]

        def apply_texture_and_sampler_to_dic() -> None:
            if sampler_dic:
                sampler_list = self.json_dic["samplers"] = []
                for sampler in sampler_dic.keys():
                    sampler_list.append(
                        {
                            "wrapS": sampler[0],
                            "wrapT": sampler[1],
                            "magFilter": sampler[2],
                            "minFilter": sampler[3],
                        }
                    )
            if texture_dic:
                textures = []
                for tex in texture_dic:
                    texture = {"sampler": tex[1], "source": tex[0]}
                    textures.append(texture)
                self.json_dic.update({"textures": textures})

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
            fallback_dic = {
                "name": b_mat.name,
                "pbrMetallicRoughness": {
                    "baseColorFactor": base_color,
                    "metallicFactor": metalness,
                    "roughnessFactor": roughness,
                },
            }
            for k, v in fallback_dic["pbrMetallicRoughness"].items():
                if v is None:
                    del fallback_dic["pbrMetallicRoughness"][k]

            if base_color_texture is not None:
                texture_info = {
                    "index": add_texture(*base_color_texture),
                    "texCoord": 0,
                }
                if texture_transform is not None:
                    texture_transform.add_to(texture_info)
                fallback_dic["pbrMetallicRoughness"].update(
                    {"baseColorTexture": texture_info}  # TODO:
                )
            if metallic_roughness_texture is not None:
                texture_info = {
                    "index": add_texture(*metallic_roughness_texture),
                    "texCoord": 0,  # TODO:
                }
                if texture_transform is not None:
                    texture_transform.add_to(texture_info)
                fallback_dic["pbrMetallicRoughness"].update(
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
                fallback_dic["normalTexture"] = normal_texture_info
            if occlusion_texture is not None:
                occlusion_texture_info = {
                    "index": add_texture(*occlusion_texture),
                    "texCoord": 0,  # TODO:
                }
                if texture_transform is not None:
                    texture_transform.add_to(occlusion_texture_info)
                fallback_dic["occlusionTexture"] = occlusion_texture_info
            if emissive_texture is not None:
                emissive_texture_info = {
                    "index": add_texture(*emissive_texture),
                    "texCoord": 0,  # TODO:
                }
                if texture_transform is not None:
                    texture_transform.add_to(emissive_texture_info)
                fallback_dic["emissiveTexture"] = emissive_texture_info

            fallback_dic["alphaMode"] = transparent_method
            if transparent_method == "MASK":
                fallback_dic["alphaCutoff"] = (
                    0.5 if transparency_cutoff is None else transparency_cutoff
                )
            if unlit:
                fallback_dic["extensions"] = {"KHR_materials_unlit": {}}
            fallback_dic["doubleSided"] = double_sided
            return fallback_dic

        # region util func
        def get_texture_name_and_sampler_type(
            shader_node: bpy.types.Node, input_socket_name: str
        ) -> Optional[Tuple[str, int, int]]:
            if (
                input_socket_name == "NormalmapTexture"
                and "NormalmapTexture" not in shader_node.inputs
                and "NomalmapTexture" in shader_node.inputs
            ):
                input_socket_name = "NomalmapTexture"
            if (
                not shader_node.inputs.get(input_socket_name)
                or not shader_node.inputs.get(input_socket_name).links
            ):
                return None

            tex_name = (
                shader_node.inputs.get(input_socket_name).links[0].from_node.image.name
            )
            # blender is ('Linear', 'Closest', 'Cubic', 'Smart') glTF is Linear, Closest
            if (
                shader_node.inputs.get(input_socket_name)
                .links[0]
                .from_node.interpolation
                == "Closest"
            ):
                filter_type = bgl.GL_NEAREST
            else:
                filter_type = bgl.GL_LINEAR
            # blender is ('REPEAT', 'EXTEND', 'CLIP') glTF is CLAMP_TO_EDGE,MIRRORED_REPEAT,REPEAT
            if (
                shader_node.inputs.get(input_socket_name).links[0].from_node.extension
                == "REPEAT"
            ):
                wrap_type = bgl.GL_REPEAT
            else:
                wrap_type = bgl.GL_CLAMP_TO_EDGE
            return tex_name, wrap_type, filter_type

        def get_float_value(
            shader_node: bpy.types.Node, input_socket_name: str
        ) -> Optional[float]:
            float_val = None
            if shader_node.inputs.get(input_socket_name):
                if shader_node.inputs.get(input_socket_name).links:
                    float_val = (
                        shader_node.inputs.get(input_socket_name)
                        .links[0]
                        .from_node.outputs[0]
                        .default_value
                    )
                else:
                    float_val = shader_node.inputs.get(input_socket_name).default_value
            return float_val

        def get_rgba_val(
            shader_node: bpy.types.Node, input_socket_name: str
        ) -> Optional[List[float]]:
            rgba_val = None
            if shader_node.inputs.get(input_socket_name):
                if shader_node.inputs.get(input_socket_name).links:
                    rgba_val = [
                        shader_node.inputs.get(input_socket_name)
                        .links[0]
                        .from_node.outputs[0]
                        .default_value[i]
                        for i in range(4)
                    ]
                else:
                    rgba_val = [
                        shader_node.inputs.get(input_socket_name).default_value[i]
                        for i in range(4)
                    ]
            return rgba_val

        # endregion util func

        def make_mtoon_unversioned_extension_dic(
            b_mat: bpy.types.Material, mtoon_shader_node: bpy.types.Node
        ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
            mtoon_dic: Dict[str, Any] = OrderedDict()
            mtoon_dic["name"] = b_mat.name
            mtoon_dic["shader"] = "VRM/MToon"
            mtoon_dic["keywordMap"] = {}
            keyword_map = mtoon_dic["keywordMap"]
            mtoon_dic["tagMap"] = {}
            tag_map = mtoon_dic["tagMap"]
            mtoon_dic["floatProperties"] = OrderedDict()
            mtoon_float_dic: Dict[str, float] = mtoon_dic["floatProperties"]
            mtoon_dic["vectorProperties"] = OrderedDict()
            mtoon_vector_dic: Dict[str, List[float]] = mtoon_dic["vectorProperties"]
            mtoon_dic["textureProperties"] = OrderedDict()
            mtoon_texture_dic = mtoon_dic["textureProperties"]

            outline_width_mode = 0
            outline_color_mode = 0
            for float_key, float_prop in [
                (k, val)
                for k, val in MaterialMtoon.float_props_exchange_dic.items()
                if val is not None
            ]:
                float_val = get_float_value(mtoon_shader_node, float_prop)
                if float_val is not None:
                    mtoon_float_dic[float_key] = float_val
                    if float_key == "_OutlineWidthMode":
                        outline_width_mode = min(max(round(float_val), 0), 2)
                        mtoon_float_dic[float_key] = int(outline_width_mode)
                    if float_key == "_OutlineColorMode":
                        outline_color_mode = min(max(round(float_val), 0), 1)
                        mtoon_float_dic[float_key] = int(outline_color_mode)

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
                dict.fromkeys(MaterialMtoon.vector_props_exchange_dic.values())
            )
            for remove_vec_prop in MaterialMtoon.texture_kind_exchange_dic.values():
                if remove_vec_prop in vec_props:
                    vec_props.remove(remove_vec_prop)

            for vector_key, vector_prop in [
                (k, v)
                for k, v in MaterialMtoon.vector_props_exchange_dic.items()
                if v in vec_props
            ]:
                vector_val = get_rgba_val(mtoon_shader_node, vector_prop)
                if vector_val is not None:
                    mtoon_vector_dic[vector_key] = vector_val

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
            ) in MaterialMtoon.texture_kind_exchange_dic.items():
                tex = get_texture_name_and_sampler_type(mtoon_shader_node, texture_prop)
                if tex is None:
                    continue

                mtoon_texture_dic[texture_key] = add_texture(*tex)
                mtoon_vector_dic[texture_key] = [0, 0, 1, 1]
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
                            mtoon_vector_dic[texture_key] = [
                                uv_offset_scaling_node.translation[0],
                                uv_offset_scaling_node.translation[1],
                                uv_offset_scaling_node.scale[0],
                                uv_offset_scaling_node.scale[1],
                            ]
                        else:
                            mtoon_vector_dic[texture_key] = [
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
                        mtoon_vector_dic[texture_key] = [0, 0, 1, 1]
                    main_texture_transform = LegacyVrmExporter.KhrTextureTransform(
                        offset=(
                            mtoon_vector_dic[texture_key][0],
                            mtoon_vector_dic[texture_key][1],
                        ),
                        scale=(
                            mtoon_vector_dic[texture_key][2],
                            mtoon_vector_dic[texture_key][3],
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
                mtoon_float_dic["_BlendMode"] = blend_mode
                mtoon_float_dic["_SrcBlend"] = src_blend
                mtoon_float_dic["_DstBlend"] = dst_blend
                mtoon_float_dic["_ZWrite"] = z_write
                if alphatest:
                    keyword_map.update({"_ALPHATEST_ON": alphatest})
                mtoon_dic["renderQueue"] = render_queue
                tag_map["RenderType"] = render_type

            if b_mat.blend_method == "OPAQUE":
                material_prop_setter(0, 1, 0, 1, False, -1, "Opaque")
            elif b_mat.blend_method == "CLIP":
                material_prop_setter(1, 1, 0, 1, True, 2450, "TransparentCutout")
                mtoon_float_dic["_Cutoff"] = b_mat.alpha_threshold
            else:  # transparent and Z_TRANSPARENCY or Raytrace
                material_prop_setter(2, 5, 10, 0, False, 3000, "Transparent")
            keyword_map.update(
                {"_ALPHABLEND_ON": b_mat.blend_method not in ("OPAQUE", "CLIP")}
            )
            keyword_map.update({"_ALPHAPREMULTIPLY_ON": False})

            mtoon_float_dic["_MToonVersion"] = MaterialMtoon.version
            mtoon_float_dic["_CullMode"] = (
                2 if b_mat.use_backface_culling else 0
            )  # no cull or bf cull
            mtoon_float_dic[
                "_OutlineCullMode"
            ] = 1  # front face cull (for invert normal outline)
            mtoon_float_dic["_DebugMode"] = 0
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
            pbr_dic = pbr_fallback(
                b_mat,
                base_color=mtoon_vector_dic.get("_Color"),
                base_color_texture=main_texture,
                normal_texture=normal_texture,
                normal_texture_scale=mtoon_float_dic.get("_BumpScale"),
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
                mtoon_ext_dic: Dict[str, Any] = {}
                mtoon_ext_dic["properties"] = {}
                mt_prop = mtoon_ext_dic["properties"]
                mt_prop["version"] = "3.2"
                blend_mode = mtoon_float_dic.get("_BlendMode")
                if blend_mode == 0:
                    blend_mode_str = "opaque"
                elif blend_mode == 1:
                    blend_mode_str = "cutout"
                else:
                    blend_mode_str = "transparent"
                # TODO transparentWithZWrite
                mt_prop["renderMode"] = blend_mode_str

                mt_prop["cullMode"] = (
                    # mtoon_float_dic.get("_CullMode") == "back"
                    "on"
                    if b_mat.use_backface_culling
                    else "off"
                )  # no cull or bf cull
                # TODO unknown number
                mt_prop["renderQueueOffsetNumber"] = 0

                mt_prop["litFactor"] = mtoon_vector_dic.get("_Color")
                mt_prop["litMultiplyTexture"] = mtoon_texture_dic.get("_MainTex")
                mt_prop["shadeFactor"] = mtoon_vector_dic.get("_ShadeColor")
                mt_prop["shadeMultiplyTexture"] = mtoon_texture_dic.get("_ShadeTexture")
                mt_prop["cutoutThresholdFactor"] = mtoon_float_dic.get("_Cutoff")
                mt_prop["shadingShiftFactor"] = mtoon_float_dic.get("_ShadeShift")
                mt_prop["shadingToonyFactor"] = mtoon_float_dic.get("_ShadeToony")
                mt_prop["shadowReceiveMultiplierFactor"] = mtoon_float_dic.get(
                    "_ReceiveShadowRate"
                )
                mt_prop[
                    "shadowReceiveMultiplierMultiplyTexture"
                ] = mtoon_texture_dic.get("_ReceiveShadowTexture")
                mt_prop["litAndShadeMixingMultiplierFactor"] = mtoon_float_dic.get(
                    "_ShadingGradeRate"
                )
                mt_prop[
                    "litAndShadeMixingMultiplierMultiplyTexture"
                ] = mtoon_texture_dic.get("_ShadingGradeTexture")
                mt_prop["lightColorAttenuationFactor"] = mtoon_float_dic.get(
                    "_LightColorAttenuation"
                )
                mt_prop["giIntensityFactor"] = mtoon_float_dic.get(
                    "_IndirectLightIntensity"
                )
                mt_prop["normalTexture"] = mtoon_texture_dic.get("_BumpMap")
                mt_prop["normalScaleFactor"] = mtoon_float_dic.get("_BumpScale")
                mt_prop["emissionFactor"] = mtoon_vector_dic.get("_EmissionColor")
                mt_prop["emissionMultiplyTexture"] = mtoon_texture_dic.get(
                    "_EmissionMap"
                )
                mt_prop["additiveTexture"] = mtoon_texture_dic.get("_SphereAdd")
                mt_prop["rimFactor"] = mtoon_vector_dic.get("_RimColor")
                mt_prop["rimMultiplyTexture"] = mtoon_texture_dic.get("_RimTexture")
                mt_prop["rimLightingMixFactor"] = mtoon_float_dic.get("_RimLightingMix")
                mt_prop["rimFresnelPowerFactor"] = mtoon_float_dic.get(
                    "_RimFresnelPower"
                )
                mt_prop["rimLiftFactor"] = mtoon_float_dic.get("_RimLift")
                mt_prop["outlineWidthMode"] = [
                    "none",
                    "worldCoordinates",
                    "screenCoordinates",
                ][floor(mtoon_float_dic.get("_OutlineWidthMode", 0))]
                mt_prop["outlineWidthFactor"] = mtoon_vector_dic.get("_OutlineColor")
                mt_prop["outlineWidthMultiplyTexture"] = mtoon_texture_dic.get(
                    "_OutlineWidthTexture"
                )
                mt_prop["outlineScaledMaxDistanceFactor"] = mtoon_float_dic.get(
                    "_OutlineScaledMaxDistance"
                )
                mt_prop["outlineColorMode"] = ["fixedColor", "mixedLighting"][
                    floor(mtoon_float_dic.get("_OutlineLightingMix", 0))
                ]
                mt_prop["outlineFactor"] = mtoon_float_dic.get("_OutlineWidth")
                mt_prop["outlineLightingMixFactor"] = mtoon_float_dic.get(
                    "OutlineLightingMix"
                )

                uv_transforms = mtoon_vector_dic.get("_MainTex")
                if uv_transforms is None:
                    uv_transforms = [0, 0, 1, 1]
                mt_prop["mainTextureLeftBottomOriginOffset"] = uv_transforms[0:2]
                mt_prop["mainTextureLeftBottomOriginScale"] = uv_transforms[2:4]
                mt_prop["uvAnimationMaskTexture"] = mtoon_texture_dic.get(
                    "_UvAnimMaskTexture"
                )
                mt_prop["uvAnimationScrollXSpeedFactor"] = mtoon_float_dic.get(
                    "_UvAnimScrollX"
                )
                mt_prop["uvAnimationScrollYSpeedFactor"] = mtoon_float_dic.get(
                    "_UvAnimScrollY"
                )
                mt_prop["uvAnimationRotationSpeedFactor"] = mtoon_float_dic.get(
                    "_UvAnimRotation"
                )
                garbage_list = []
                for k, v in mt_prop.items():
                    if v is None:
                        garbage_list.append(k)
                for garbage in garbage_list:
                    mt_prop.pop(garbage)

                pbr_dic["extensions"].update({"VRMC_materials_mtoon": mtoon_ext_dic})
            return mtoon_dic, pbr_dic

        def make_gltf_mat_dic(
            b_mat: bpy.types.Material, gltf_shader_node: bpy.types.Node
        ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
            gltf_dic = OrderedDict()
            gltf_dic["name"] = b_mat.name
            gltf_dic["shader"] = "VRM_USE_GLTFSHADER"
            gltf_dic["keywordMap"] = {}
            gltf_dic["tagMap"] = {}
            gltf_dic["floatProperties"] = {}
            gltf_dic["vectorProperties"] = {}
            gltf_dic["textureProperties"] = {}
            gltf_dic["extras"] = {"VRM_Addon_for_Blender_legacy_gltf_material": {}}

            if b_mat.blend_method == "OPAQUE":
                transparent_method = "OPAQUE"
                transparency_cutoff = None
            elif b_mat.blend_method == "CLIP":
                transparent_method = "MASK"
                transparency_cutoff = b_mat.alpha_threshold
            else:
                transparent_method = "BLEND"
                transparency_cutoff = None

            unlit_value = get_float_value(gltf_shader_node, "unlit")
            if unlit_value is None:
                unlit = None
            else:
                unlit = unlit_value > 0.5
            pbr_dic = pbr_fallback(
                b_mat,
                base_color=get_rgba_val(gltf_shader_node, "base_Color"),
                metalness=get_float_value(gltf_shader_node, "metallic"),
                roughness=get_float_value(gltf_shader_node, "roughness"),
                base_color_texture=get_texture_name_and_sampler_type(
                    gltf_shader_node, "color_texture"
                ),
                metallic_roughness_texture=get_texture_name_and_sampler_type(
                    gltf_shader_node, "metallic_roughness_texture"
                ),
                transparent_method=transparent_method,
                transparency_cutoff=transparency_cutoff,
                unlit=unlit,
                double_sided=not b_mat.use_backface_culling,
            )

            def pbr_tex_add(texture_type: str, socket_name: str) -> None:
                img = get_texture_name_and_sampler_type(gltf_shader_node, socket_name)
                if img is not None:
                    pbr_dic[texture_type] = {"index": add_texture(*img), "texCoord": 0}
                else:
                    print(socket_name)

            pbr_tex_add("normalTexture", "normal")
            pbr_tex_add("emissiveTexture", "emissive_texture")
            pbr_tex_add("occlusionTexture", "occlusion_texture")
            emissive_factor = get_rgba_val(gltf_shader_node, "emissive_color")
            if emissive_factor is None:
                emissive_factor = [0, 0, 0]
            else:
                emissive_factor = emissive_factor[0:3]
            pbr_dic["emissiveFactor"] = emissive_factor

            return gltf_dic, pbr_dic

        def make_transzw_mat_dic(
            b_mat: bpy.types.Material, transzw_shader_node: bpy.types.Node
        ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
            zw_dic = OrderedDict()
            zw_dic["name"] = b_mat.name
            zw_dic["shader"] = "VRM/UnlitTransparentZWrite"
            zw_dic["renderQueue"] = 2600
            zw_dic["keywordMap"] = {}
            zw_dic["tagMap"] = {"RenderType": "Transparent"}
            zw_dic["floatProperties"] = {}
            zw_dic["vectorProperties"] = {}
            zw_dic["textureProperties"] = {}
            color_tex = get_texture_name_and_sampler_type(
                transzw_shader_node, "Main_Texture"
            )
            if color_tex is not None:
                zw_dic["textureProperties"] = {"_MainTex": add_texture(*color_tex)}
                zw_dic["vectorProperties"] = {"_MainTex": [0, 0, 1, 1]}
            pbr_dic = pbr_fallback(
                b_mat, base_color_texture=color_tex, transparent_method="BLEND"
            )

            return zw_dic, pbr_dic

        def add_gltf2_io_texture(
            gltf2_io_texture_info: Any,
        ) -> Dict[str, Union[int, float]]:
            image = gltf2_io_texture_info.index.source
            found = False
            for (name, data, index) in gltf2_io_texture_images:
                if name != image.name or data != image.buffer_view.data:
                    continue
                image_index = index
                image_name = {value: key for key, value in image_id_dic.items()}[
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
                    if image_name not in image_id_dic:
                        break
                image_id_dic[image_name] = image_index
                ImageBin(
                    image.buffer_view.data,
                    image_name,
                    image.mime_type,
                    self.glb_bin_collector,
                )

            sampler = gltf2_io_texture_info.index.sampler
            if sampler is None:
                sampler_dic_key = (
                    bgl.GL_REPEAT,
                    bgl.GL_REPEAT,
                    bgl.GL_LINEAR,
                    bgl.GL_LINEAR,
                )
            else:
                sampler_dic_key = (
                    sampler.wrap_s or bgl.GL_REPEAT,
                    sampler.wrap_t or bgl.GL_REPEAT,
                    sampler.mag_filter or bgl.GL_LINEAR,
                    sampler.min_filter or bgl.GL_LINEAR,
                )

                # VRoid Hub may not support a mipmap
                if sampler_dic_key[3] in [
                    bgl.GL_NEAREST_MIPMAP_LINEAR,
                    bgl.GL_NEAREST_MIPMAP_NEAREST,
                ]:
                    sampler_dic_key = sampler_dic_key[0:3] + (bgl.GL_NEAREST,)
                elif sampler_dic_key[3] in [
                    bgl.GL_LINEAR_MIPMAP_NEAREST,
                    bgl.GL_LINEAR_MIPMAP_LINEAR,
                ]:
                    sampler_dic_key = sampler_dic_key[0:3] + (bgl.GL_LINEAR,)

            if sampler_dic_key not in sampler_dic.keys():
                sampler_dic.update({sampler_dic_key: len(sampler_dic)})
            if (image_index, sampler_dic[sampler_dic_key]) not in texture_dic.keys():
                texture_dic.update(
                    {(image_index, sampler_dic[sampler_dic_key]): len(texture_dic)}
                )
            texture_info: Dict[str, Union[int, float]] = {
                "index": texture_dic[(image_index, sampler_dic[sampler_dic_key])],
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

        def make_non_vrm_mat_dic(
            b_mat: bpy.types.Material,
        ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
            vrm_dic = {
                "name": b_mat.name,
                "shader": "VRM_USE_GLTFSHADER",
                "keywordMap": {},
                "tagMap": {},
                "floatProperties": {},
                "vectorProperties": {},
                "textureProperties": {},
            }
            fallback = (vrm_dic, {"name": b_mat.name})

            pbr_dic: Dict[str, Any] = {}
            pbr_dic["name"] = b_mat.name

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
            }
            try:
                if bpy.app.version >= (2, 91):
                    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/abd8380e19dbe5e5fb9042513ad6b744032bc9bc/addons/io_scene_gltf2/blender/exp/gltf2_blender_gather_materials.py#L32
                    gltf2_io_material = gather_material(b_mat, export_settings)
                else:
                    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/ac3471cae42b34fc69fda75fa404117272fa9560/addons/io_scene_gltf2/blender/exp/gltf2_blender_gather_materials.py#L32
                    gltf2_io_material = gather_material(
                        b_mat, not b_mat.use_backface_culling, export_settings
                    )

                if isinstance(gltf2_io_material.alpha_cutoff, (int, float)):
                    pbr_dic["alphaCutoff"] = gltf2_io_material.alpha_cutoff
                if isinstance(gltf2_io_material.alpha_mode, str):
                    pbr_dic["alphaMode"] = gltf2_io_material.alpha_mode
                if isinstance(gltf2_io_material.double_sided, bool):
                    pbr_dic["doubleSided"] = gltf2_io_material.double_sided
                if isinstance(gltf2_io_material.emissive_factor, abc.Sequence):
                    pbr_dic["emissiveFactor"] = gltf2_io_material.emissive_factor
                if gltf2_io_material.emissive_texture is not None:
                    pbr_dic["emissiveTexture"] = add_gltf2_io_texture(
                        gltf2_io_material.emissive_texture
                    )
                if isinstance(gltf2_io_material.extensions, dict):
                    pbr_dic["extensions"] = {}
                    # https://github.com/KhronosGroup/glTF/tree/master/extensions/2.0/Khronos/KHR_materials_unli
                    if (
                        gltf2_io_material.extensions.get("KHR_materials_unlit")
                        is not None
                    ):
                        pbr_dic["extensions"].update({"KHR_materials_unlit": {}})
                if gltf2_io_material.normal_texture is not None:
                    pbr_dic["normalTexture"] = add_gltf2_io_texture(
                        gltf2_io_material.normal_texture
                    )
                if gltf2_io_material.occlusion_texture is not None:
                    pbr_dic["occlusionTexture"] = add_gltf2_io_texture(
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
                    pbr_dic["pbrMetallicRoughness"] = pbr_metallic_roughness
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

            return vrm_dic, pbr_dic

        # endregion function separate by shader

        used_materials = []
        for mesh in [
            obj
            for obj in self.export_objects
            if obj.type in self.MESH_CONVERTIBLE_OBJECT_TYPES
        ]:
            for mat in mesh.data.materials:
                if mat and mat not in used_materials:
                    used_materials.append(mat)

        for b_mat in used_materials:
            material_properties_dic: Dict[str, Any] = {}
            pbr_dic: Dict[str, Any] = {}
            if b_mat.get("vrm_shader") == "MToon_unversioned":
                for node in b_mat.node_tree.nodes:
                    if node.type == "OUTPUT_MATERIAL":
                        mtoon_shader_node = node.inputs["Surface"].links[0].from_node
                        (
                            material_properties_dic,
                            pbr_dic,
                        ) = make_mtoon_unversioned_extension_dic(
                            b_mat, mtoon_shader_node
                        )
                        break
            elif b_mat.get("vrm_shader") == "GLTF":
                for node in b_mat.node_tree.nodes:
                    if node.type == "OUTPUT_MATERIAL":
                        gltf_shader_node = node.inputs["Surface"].links[0].from_node
                        material_properties_dic, pbr_dic = make_gltf_mat_dic(
                            b_mat, gltf_shader_node
                        )
                        break
            elif b_mat.get("vrm_shader") == "TRANSPARENT_ZWRITE":
                for node in b_mat.node_tree.nodes:
                    if node.type == "OUTPUT_MATERIAL":
                        zw_shader_node = node.inputs["Surface"].links[0].from_node
                        material_properties_dic, pbr_dic = make_transzw_mat_dic(
                            b_mat, zw_shader_node
                        )
                        break
            else:
                material_properties_dic, pbr_dic = make_non_vrm_mat_dic(b_mat)

            glb_material_list.append(pbr_dic)
            vrm_material_props_list.append(material_properties_dic)

        apply_texture_and_sampler_to_dic()
        self.json_dic.update({"materials": glb_material_list})
        vrm_version = self.vrm_version
        if vrm_version is None:
            raise Exception("vrm version is None")
        if vrm_version.startswith("0."):
            self.json_dic.update(
                {"extensions": {"VRM": {"materialProperties": vrm_material_props_list}}}
            )

    def joint_id_from_node_name_solver(
        self, node_name: str, node_id_dic: Dict[str, int]
    ) -> int:
        try:
            node_id = node_id_dic[node_name]
            joints = self.json_dic["skins"][0]["joints"]
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
        morph_normal_diff_dic = {}
        vert_base_normal_dic = OrderedDict()
        for kb in mesh_data.shape_keys.key_blocks:
            vert_base_normal_dic.update({kb.name: kb.normals_vertex_get()})
        reference_key_name = mesh_data.shape_keys.reference_key.name
        for k, v in vert_base_normal_dic.items():
            if k == reference_key_name:
                continue
            values = []
            for vert_morph_normal, vert_base_normal in zip(
                zip(*[iter(v)] * 3),
                zip(*[iter(vert_base_normal_dic[reference_key_name])] * 3),
            ):
                values.append(
                    [vert_morph_normal[i] - vert_base_normal[i] for i in range(3)]
                )
            morph_normal_diff_dic.update({k: values})
        return morph_normal_diff_dic

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
                or mesh.parent.type not in self.MESH_CONVERTIBLE_OBJECT_TYPES
            ):
                return True
            mesh = mesh.parent
        return True

    def mesh_to_bin_and_dic(self) -> None:
        self.json_dic["meshes"] = []
        vrm_version = self.vrm_version
        if vrm_version is None:
            raise Exception("vrm version is None")

        meshes = [
            obj
            for obj in self.export_objects
            if obj.type in self.MESH_CONVERTIBLE_OBJECT_TYPES
        ]
        while True:
            swapped = False
            for mesh in list(meshes):
                if (
                    mesh.parent_type == "OBJECT"
                    and mesh.parent
                    and mesh.parent.type in self.MESH_CONVERTIBLE_OBJECT_TYPES
                    and meshes.index(mesh) < meshes.index(mesh.parent)
                ):
                    meshes.remove(mesh)
                    meshes.append(mesh)
                    swapped = True
            if not swapped:
                break

        for mesh in meshes:
            is_skin_mesh = self.is_skin_mesh(mesh)
            node_dic = OrderedDict(
                {
                    "name": mesh.name,
                    "translation": self.axis_blender_to_glb(mesh.location),
                    "rotation": [0, 0, 0, 1],  # このへんは規約なので
                    "scale": [1, 1, 1],  # このへんは規約なので
                }
            )
            if is_skin_mesh:
                node_dic["translation"] = [0, 0, 0]  # skinnedmeshはtransformを無視される
            self.json_dic["nodes"].append(node_dic)

            mesh_node_id = len(self.json_dic["nodes"]) - 1

            if is_skin_mesh:
                self.json_dic["scenes"][0]["nodes"].append(mesh_node_id)
            else:
                if mesh.parent_type == "BONE":
                    parent_node = (
                        [
                            node
                            for node in self.json_dic["nodes"]
                            if node["name"] == mesh.parent_bone
                        ]
                        + [None]
                    )[0]
                elif mesh.parent_type == "OBJECT":
                    parent_node = (
                        [
                            node
                            for node in self.json_dic["nodes"]
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
                    self.json_dic["scenes"][0]["nodes"].append(mesh_node_id)
                mesh_pos = mesh.matrix_world.to_translation()
                relate_pos = [mesh_pos[i] - base_pos[i] for i in range(3)]
                self.json_dic["nodes"][mesh_node_id][
                    "translation"
                ] = self.axis_blender_to_glb(relate_pos)

            # region hell
            # Check added to resolve https://github.com/saturday06/VRM_Addon_for_Blender/issues/70
            if bpy.context.view_layer.objects.active is not None:
                bpy.ops.object.mode_set(mode="OBJECT")

            # https://docs.blender.org/api/2.80/bpy.types.Depsgraph.html
            depsgraph = bpy.context.evaluated_depsgraph_get()
            mesh_owner = mesh.evaluated_get(depsgraph)
            mesh_data = mesh_owner.to_mesh(
                preserve_all_data_layers=True, depsgraph=depsgraph
            ).copy()
            for prop in mesh.data.keys():
                mesh_data[prop] = mesh.data[prop]

            mesh.hide_viewport = False
            mesh.hide_select = False
            bpy.context.view_layer.objects.active = mesh
            bpy.ops.object.mode_set(mode="EDIT")

            bm_temp = bmesh.new()
            mesh_data_transform = Matrix.Identity(4)
            if not is_skin_mesh:
                mesh_data_transform @= Matrix.Translation(
                    -mesh.matrix_world.to_translation()
                )
            mesh_data_transform @= mesh.matrix_world
            mesh_data.transform(mesh_data_transform, shape_keys=True)
            bm_temp.from_mesh(mesh_data)
            bmesh.ops.triangulate(bm_temp, faces=bm_temp.faces[:])
            bm_temp.to_mesh(mesh_data)
            bm_temp.free()

            if mesh_data.has_custom_normals:
                mesh_data.calc_loop_triangles()
                mesh_data.calc_normals_split()

            bm = bmesh.new()
            bm.from_mesh(mesh_data)

            # region temporary used
            mat_id_dic = {
                mat["name"]: i for i, mat in enumerate(self.json_dic["materials"])
            }
            material_slot_dic = {
                i: mat.name for i, mat in enumerate(mesh.material_slots) if mat.name
            }
            node_id_dic = {
                node["name"]: i for i, node in enumerate(self.json_dic["nodes"])
            }

            v_group_name_dic = {i: vg.name for i, vg in enumerate(mesh.vertex_groups)}
            fmin, fmax = gltf.FLOAT_NEGATIVE_MAX, gltf.FLOAT_POSITIVE_MAX
            unique_vertex_id = 0
            # {(uv...,vertex_index):unique_vertex_id} (uvと頂点番号が同じ頂点は同じものとして省くようにする)
            unique_vertex_dic: Dict[Tuple[Any, ...], int] = {}
            uvlayers_dic = {
                i: uvlayer.name for i, uvlayer in enumerate(mesh_data.uv_layers)
            }

            # endregion  temporary_used
            primitive_index_bin_dic: Dict[Optional[int], bytes] = OrderedDict(
                {mat_id_dic[mat.name]: b"" for mat in mesh.material_slots if mat.name}
            )
            if not primitive_index_bin_dic:
                primitive_index_bin_dic[None] = b""
            primitive_index_vertex_count: Dict[Optional[int], int] = OrderedDict(
                {mat_id_dic[mat.name]: 0 for mat in mesh.material_slots if mat.name}
            )
            if not primitive_index_vertex_count:
                primitive_index_vertex_count[None] = 0

            shape_pos_bin_dic: Dict[str, bytes] = {}
            shape_normal_bin_dic: Dict[str, bytes] = {}
            shape_min_max_dic: Dict[str, List[List[float]]] = {}
            morph_normal_diff_dic: Dict[str, List[List[float]]] = {}
            if mesh_data.shape_keys is not None:
                # 0番目Basisは省く
                shape_pos_bin_dic = OrderedDict(
                    {shape.name: b"" for shape in mesh_data.shape_keys.key_blocks[1:]}
                )
                shape_normal_bin_dic = OrderedDict(
                    {shape.name: b"" for shape in mesh_data.shape_keys.key_blocks[1:]}
                )
                shape_min_max_dic = OrderedDict(
                    {
                        shape.name: [[fmax, fmax, fmax], [fmin, fmin, fmin]]
                        for shape in mesh_data.shape_keys.key_blocks[1:]
                    }
                )
                morph_normal_diff_dic = (
                    self.fetch_morph_vertex_normal_difference(mesh_data)
                    if vrm_version.startswith("0.")
                    else {}
                )  # {morphname:{vertexid:[diff_X,diff_y,diff_z]}}
            position_bin = b""
            position_min_max = [[fmax, fmax, fmax], [fmin, fmin, fmin]]
            normal_bin = b""
            joints_bin = b""
            weights_bin = b""
            texcoord_bins = {uvlayer_id: b"" for uvlayer_id in uvlayers_dic.keys()}
            float_vec4_packer = struct.Struct("<ffff").pack
            float_vec3_packer = struct.Struct("<fff").pack
            float_pair_packer = struct.Struct("<ff").pack
            unsigned_int_scalar_packer = struct.Struct("<I").pack
            unsigned_short_vec4_packer = struct.Struct("<HHHH").pack

            def min_max(minmax: List[List[float]], position: List[float]) -> None:
                for i in range(3):
                    minmax[0][i] = (
                        position[i] if position[i] < minmax[0][i] else minmax[0][i]
                    )
                    minmax[1][i] = (
                        position[i] if position[i] > minmax[1][i] else minmax[1][i]
                    )

            for face in bm.faces:
                for loop in face.loops:
                    uv_list = []
                    for uvlayer_name in uvlayers_dic.values():
                        uv_layer = bm.loops.layers.uv[uvlayer_name]
                        uv_list += [loop[uv_layer].uv[0], loop[uv_layer].uv[1]]

                    vert_normal = [0, 0, 0]
                    if mesh_data.has_custom_normals:
                        tri = mesh_data.loop_triangles[face.index]
                        vid = -1
                        for i, _vid in enumerate(tri.vertices):
                            if _vid == loop.vert.index:
                                vid = i
                        if vid == -1:
                            print("something wrong in custom normal export")
                        vert_normal = tri.split_normals[vid]
                    else:
                        if face.smooth:
                            vert_normal = loop.vert.normal
                        else:
                            vert_normal = face.normal

                    vertex_key = (*uv_list, *vert_normal, loop.vert.index)
                    cached_vert_id = unique_vertex_dic.get(
                        vertex_key
                    )  # keyがなければNoneを返す
                    if cached_vert_id is not None:
                        primitive_index = None
                        if face.material_index in material_slot_dic:
                            primitive_index = mat_id_dic[
                                material_slot_dic[face.material_index]
                            ]
                        primitive_index_bin_dic[
                            primitive_index
                        ] += unsigned_int_scalar_packer(cached_vert_id)
                        primitive_index_vertex_count[primitive_index] += 1
                        continue
                    unique_vertex_dic[vertex_key] = unique_vertex_id
                    for uvlayer_id, uvlayer_name in uvlayers_dic.items():
                        uv_layer = bm.loops.layers.uv[uvlayer_name]
                        uv = loop[uv_layer].uv
                        texcoord_bins[uvlayer_id] += float_pair_packer(
                            uv[0], 1 - uv[1]
                        )  # blenderとglbのuvは上下逆
                    for shape_name in shape_pos_bin_dic:
                        shape_layer = bm.verts.layers.shape[shape_name]
                        morph_pos = self.axis_blender_to_glb(
                            [
                                loop.vert[shape_layer][i] - loop.vert.co[i]
                                for i in range(3)
                            ]
                        )
                        shape_pos_bin_dic[shape_name] += float_vec3_packer(*morph_pos)
                        if vrm_version.startswith("0."):
                            shape_normal_bin_dic[shape_name] += float_vec3_packer(
                                *self.axis_blender_to_glb(
                                    morph_normal_diff_dic[shape_name][loop.vert.index]
                                )
                            )
                        min_max(shape_min_max_dic[shape_name], morph_pos)
                    if is_skin_mesh:
                        weight_and_joint_list: List[Tuple[float, int]] = []
                        for v_group in mesh_data.vertices[loop.vert.index].groups:
                            v_group_name = v_group_name_dic.get(v_group.group)
                            if v_group_name is None:
                                continue
                            joint_id = self.joint_id_from_node_name_solver(
                                v_group_name, node_id_dic
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
                                in self.MESH_CONVERTIBLE_OBJECT_TYPES
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
                                for index, node in enumerate(self.json_dic["nodes"])
                                if node["name"] == bone_name
                            )
                            weights = [1.0, 0, 0, 0]
                            joints = [bone_index, 0, 0, 0]

                        normalized_weights = normalize_weights_compatible_with_gl_float(
                            weights
                        )
                        joints_bin += unsigned_short_vec4_packer(*joints)
                        weights_bin += float_vec4_packer(*normalized_weights)

                    vert_location = self.axis_blender_to_glb(loop.vert.co)
                    position_bin += float_vec3_packer(*vert_location)
                    min_max(position_min_max, vert_location)
                    normal_bin += float_vec3_packer(
                        *self.axis_blender_to_glb(vert_normal)
                    )
                    primitive_index = None
                    if face.material_index in material_slot_dic:
                        primitive_index = mat_id_dic[
                            material_slot_dic[face.material_index]
                        ]
                    primitive_index_bin_dic[
                        primitive_index
                    ] += unsigned_int_scalar_packer(unique_vertex_id)
                    primitive_index_vertex_count[primitive_index] += 1
                    unique_vertex_id += 1  # noqa: SIM113

            # DONE :index position, uv, normal, position morph,JOINT WEIGHT
            # TODO: morph_normal, v_color...?
            primitive_glbs_dic = OrderedDict(
                {
                    mat_id: GlbBin(
                        index_bin,
                        "SCALAR",
                        bgl.GL_UNSIGNED_INT,
                        primitive_index_vertex_count[mat_id],
                        None,
                        self.glb_bin_collector,
                    )
                    for mat_id, index_bin in primitive_index_bin_dic.items()
                    if index_bin != b""
                }
            )

            if not primitive_glbs_dic:
                bm.free()
                continue

            mesh_index = len(self.json_dic["meshes"])
            node_dic["mesh"] = mesh_index
            if is_skin_mesh:
                # TODO: 決め打ちってどうよ:一体のモデルなのだから2つもあっては困る(から決め打ち(やめろ(やだ))
                node_dic["skin"] = 0

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
            if len(shape_pos_bin_dic.keys()) != 0:
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
                        shape_pos_bin_dic.values(), shape_min_max_dic.values()
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
                        for morph_normal_bin in shape_normal_bin_dic.values()
                    ]

            primitive_list = []
            for primitive_id, index_glb in primitive_glbs_dic.items():
                primitive: Dict[str, Any] = OrderedDict({"mode": 4})
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
                if len(shape_pos_bin_dic.keys()) != 0:
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
                        "targetNames": list(shape_pos_bin_dic.keys())
                    }
                primitive_list.append(primitive)
            if mesh.name not in self.mesh_name_to_index:
                self.mesh_name_to_index[mesh.name] = mesh_index
            self.mesh_name_to_index[mesh.data.name] = mesh_index
            self.json_dic["meshes"].append(
                OrderedDict({"name": mesh.data.name, "primitives": primitive_list})
            )
            bm.free()
            # endregion hell

            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.mode_set(mode="OBJECT")

    def exporter_name(self) -> str:
        v = version()
        if os.environ.get("BLENDER_VRM_USE_TEST_EXPORTER_VERSION") == "true":
            v = (999, 999, 999)
        return "saturday06_blender_vrm_exporter_experimental_" + ".".join(map(str, v))

    def gltf_meta_to_dic(self) -> None:
        gltf_meta_dic = {
            "extensionsUsed": [
                "VRM",
                "KHR_materials_unlit",
                "KHR_texture_transform",
                "VRMC_materials_mtoon",
            ],
            "asset": {
                "generator": self.exporter_name(),
                "version": "2.0",  # glTF version
            },
        }

        self.json_dic.update(gltf_meta_dic)

    def vrm_meta_to_dic(self) -> None:
        # materialProperties は material_to_dic()で処理する
        # region vrm_extension
        meta_props = self.armature.data.vrm_addon_extension.vrm0.meta
        vrm_extension_dict: Dict[str, Any] = OrderedDict()
        vrm_version = self.vrm_version
        if vrm_version is None:
            raise Exception("vrm version is None")
        if vrm_version.startswith("0."):
            vrm_extension_dict["exporterVersion"] = self.exporter_name()
        vrm_extension_dict["specVersion"] = self.vrm_version
        # region meta
        vrm_extension_dict["meta"] = {
            "title": meta_props.title,
            "version": meta_props.version,
            "author": meta_props.author,
            "contactInformation": meta_props.contact_information,
            "reference": meta_props.reference,
            "allowedUserName": meta_props.allowed_user_name,
            "violentUssageName": meta_props.violent_ussage_name,  # noqa: SC200
            "sexualUssageName": meta_props.sexual_ussage_name,  # noqa: SC200
            "commercialUssageName": meta_props.commercial_ussage_name,  # noqa: SC200
            "otherPermissionUrl": meta_props.other_permission_url,
            "licenseName": meta_props.license_name,
            "otherLicenseUrl": meta_props.other_license_url,
        }
        if meta_props.texture and meta_props.texture.name:
            thumbnail_indices = [
                index
                for index, image_bin in enumerate(self.glb_bin_collector.image_bins)
                if image_bin.name == meta_props.texture.name
            ]
            if thumbnail_indices:
                if "samplers" not in self.json_dic:
                    self.json_dic["samplers"] = []
                self.json_dic["samplers"].append(
                    {
                        "magFilter": bgl.GL_LINEAR,
                        "minFilter": bgl.GL_LINEAR,
                        "wrapS": bgl.GL_REPEAT,
                        "wrapT": bgl.GL_REPEAT,
                    }
                )
                if "textures" not in self.json_dic:
                    self.json_dic["textures"] = []
                self.json_dic["textures"].append(
                    {
                        "sampler": len(self.json_dic["samplers"]) - 1,
                        "source": thumbnail_indices[0],
                    },
                )
                vrm_extension_dict["meta"]["texture"] = (
                    len(self.json_dic["textures"]) - 1
                )
        # endregion meta

        # region humanoid
        node_name_id_dict = {
            node["name"]: i for i, node in enumerate(self.json_dic["nodes"])
        }
        humanoid_dict: Dict[str, Any] = {"humanBones": []}
        vrm_extension_dict["humanoid"] = humanoid_dict
        humanoid_props = self.armature.data.vrm_addon_extension.vrm0.humanoid
        for human_bone_name in HumanBones.all_names:
            for human_bone_props in humanoid_props.human_bones:
                if (
                    human_bone_props.bone != human_bone_name
                    or not human_bone_props.node.value
                    or human_bone_props.node.value not in node_name_id_dict
                ):
                    continue
                human_bone_dict = {
                    "bone": human_bone_name,
                    "node": node_name_id_dict[human_bone_props.node.value],
                    "useDefaultValues": human_bone_props.use_default_values,
                }
                humanoid_dict["humanBones"].append(human_bone_dict)
                if not human_bone_props.use_default_values:
                    human_bone_dict.update(
                        {
                            "min": {
                                "x": human_bone_props.min[0],
                                "y": human_bone_props.min[1],
                                "z": human_bone_props.min[2],
                            },
                            "max": {
                                "x": human_bone_props.max[0],
                                "y": human_bone_props.max[1],
                                "z": human_bone_props.max[2],
                            },
                            "center": {
                                "x": human_bone_props.center[0],
                                "y": human_bone_props.center[1],
                                "z": human_bone_props.center[2],
                            },
                            "axisLength": human_bone_props.axis_length,
                        }
                    )
                break
        humanoid_dict["armStretch"] = humanoid_props.arm_stretch
        humanoid_dict["legStretch"] = humanoid_props.leg_stretch
        humanoid_dict["upperArmTwist"] = humanoid_props.upper_arm_twist
        humanoid_dict["lowerArmTwist"] = humanoid_props.lower_arm_twist
        humanoid_dict["upperLegTwist"] = humanoid_props.upper_leg_twist
        humanoid_dict["lowerLegTwist"] = humanoid_props.lower_leg_twist
        humanoid_dict["feetSpacing"] = humanoid_props.feet_spacing
        humanoid_dict["hasTranslationDoF"] = humanoid_props.has_translation_dof
        # endregion humanoid

        # region firstPerson
        first_person_dict: Dict[str, Any] = {}
        vrm_extension_dict["firstPerson"] = first_person_dict
        first_person_props = self.armature.data.vrm_addon_extension.vrm0.first_person

        if first_person_props.first_person_bone.value:
            first_person_dict["firstPersonBone"] = node_name_id_dict[
                first_person_props.first_person_bone.value
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
            "x": first_person_props.first_person_bone_offset[0],
            "y": first_person_props.first_person_bone_offset[2],
            "z": first_person_props.first_person_bone_offset[1],
        }

        mesh_annotations: List[Dict[str, Any]] = []
        first_person_dict["meshAnnotations"] = mesh_annotations
        for mesh_annotation_props in first_person_props.mesh_annotations:
            if not mesh_annotation_props.mesh or not mesh_annotation_props.mesh.value:
                mesh_index = -1
            else:
                matched_mesh_indices = [
                    i
                    for i, mesh in enumerate(self.json_dic["meshes"])
                    if mesh["name"] == mesh_annotation_props.mesh.value
                ]
                mesh_index = (matched_mesh_indices + [-1])[0]
            mesh_annotations.append(
                {
                    "mesh": mesh_index,
                    "firstPersonFlag": mesh_annotation_props.first_person_flag,
                }
            )
        first_person_dict["lookAtTypeName"] = first_person_props.look_at_type_name
        for (look_at_props, look_at_dict_key) in [
            (
                first_person_props.look_at_horizontal_inner,
                "lookAtHorizontalInner",
            ),
            (
                first_person_props.look_at_horizontal_outer,
                "lookAtHorizontalOuter",
            ),
            (
                first_person_props.look_at_vertical_down,
                "lookAtVerticalDown",
            ),
            (
                first_person_props.look_at_vertical_up,
                "lookAtVerticalUp",
            ),
        ]:
            first_person_dict[look_at_dict_key] = {
                "curve": list(look_at_props.curve),
                "xRange": look_at_props.x_range,
                "yRange": look_at_props.y_range,
            }
        # endregion firstPerson
        # region blendShapeMaster
        vrm_extension_dict["blendShapeMaster"] = {}
        vrm_extension_dict["blendShapeMaster"][
            "blendShapeGroups"
        ] = blend_shape_groups = []

        # meshを名前からid
        # weightを0-1から0-100に
        # shape_indexを名前からindexに
        for (
            blend_shape_group_props
        ) in (
            self.armature.data.vrm_addon_extension.vrm0.blend_shape_master.blend_shape_groups
        ):
            blend_shape_group_dict = {}

            if not blend_shape_group_props.name:
                continue
            blend_shape_group_dict["name"] = blend_shape_group_props.name

            if not blend_shape_group_props.preset_name:
                continue
            blend_shape_group_dict["presetName"] = blend_shape_group_props.preset_name

            blend_shape_group_dict["binds"] = binds = []
            for bind_props in blend_shape_group_props.binds:
                bind_dict: Dict[str, Any] = {}
                mesh = self.mesh_name_to_index.get(bind_props.mesh.value)
                if mesh is None:
                    continue
                bind_dict["mesh"] = mesh

                target_names = deep.get_list(
                    self.json_dic,
                    ["meshes", mesh, "primitives", 0, "extras", "targetNames"],
                    [],
                )

                if bind_props.index not in target_names:
                    continue

                bind_dict["index"] = target_names.index(bind_props.index)
                bind_dict["weight"] = min(max(bind_props.weight * 100, 0), 100)

                binds.append(bind_dict)

            blend_shape_group_dict["materialValues"] = material_values = []
            for material_value_props in blend_shape_group_props.material_values:
                if (
                    not material_value_props.material
                    or not material_value_props.material.name
                ):
                    continue

                material_values.append(
                    {
                        "materialName": material_value_props.material.name,
                        "propertyName": material_value_props.property_name,
                        "targetValue": list(
                            map(
                                lambda v: float(v.value),
                                material_value_props.target_value,
                            )
                        ),
                    }
                )

            blend_shape_group_dict["isBinary"] = blend_shape_group_props.is_binary
            blend_shape_groups.append(blend_shape_group_dict)
        # endregion blendShapeMaster

        # region secondaryAnimation
        secondary_animation_dict: Dict[str, Any] = {}
        vrm_extension_dict["secondaryAnimation"] = secondary_animation_dict
        collider_groups: List[Dict[str, Any]] = []
        secondary_animation_dict["colliderGroups"] = collider_groups
        secondary_animation_props = (
            self.armature.data.vrm_addon_extension.vrm0.secondary_animation
        )
        collider_group_names = [
            collider_group_props.name
            for collider_group_props in secondary_animation_props.collider_groups
        ]

        # region boneGroup
        secondary_animation_dict["boneGroups"] = bone_groups = []
        for bone_group_props in secondary_animation_props.bone_groups:
            bone_group_dict = {
                "comment": bone_group_props.comment,
                "stiffiness": bone_group_props.stiffiness,  # noqa: SC200
                "gravityPower": bone_group_props.gravity_power,
                "gravityDir": {
                    # Axis confusing
                    "x": bone_group_props.gravity_dir[0],
                    "y": bone_group_props.gravity_dir[2],
                    "z": bone_group_props.gravity_dir[1],
                },
                "dragForce": bone_group_props.drag_force,
                "center": node_name_id_dict.get(bone_group_props.center.value, -1),
                "hitRadius": bone_group_props.hit_radius,
                "bones": [
                    node_name_id_dict[bone.value]
                    for bone in bone_group_props.bones
                    if bone.value in node_name_id_dict
                ],
            }
            collider_group_indices: List[int] = []
            for collider_group_name_props in bone_group_props.collider_groups:
                if collider_group_name_props.value not in collider_group_names:
                    continue
                index = collider_group_names.index(collider_group_name_props.value)
                collider_group_indices.append(index)

            bone_group_dict["colliderGroups"] = collider_group_indices
            bone_groups.append(bone_group_dict)
        # endregion boneGroup

        # region colliderGroups
        for collider_group_props in secondary_animation_props.collider_groups:
            collider_group_dict: Dict[str, Any] = {}
            collider_group_dict["colliders"] = colliders = []
            collider_groups.append(collider_group_dict)

            if collider_group_props.node and collider_group_props.node.value:
                collider_group_dict["node"] = node_name_id_dict[
                    collider_group_props.node.value
                ]
            else:
                collider_group_dict["node"] = -1
                continue

            for collider_props in collider_group_props.colliders:
                collider_object = collider_props.blender_object
                if collider_object.parent_bone not in self.armature.pose.bones:
                    continue

                collider: Dict[str, Any] = {}
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

                if isinstance(collider_object.empty_display_size, (int, float)):
                    collider["radius"] = collider_object.empty_display_size

                collider["offset"] = OrderedDict(
                    zip(
                        ("x", "y", "z"),
                        self.axis_blender_to_glb(offset),
                    )
                )
                collider["offset"]["z"] = collider["offset"]["z"] * -1
                colliders.append(collider)
        # endregion colliderGroups
        # endregion secondaryAnimation
        extension_name = "VRM" if vrm_version.startswith("0.") else "VRMC_vrm"
        self.json_dic["extensions"][extension_name].update(vrm_extension_dict)
        # endregion vrm_extension

        # region secondary
        self.json_dic["nodes"].append(
            {
                "name": "secondary",
                "translation": [0.0, 0.0, 0.0],
                "rotation": [0.0, 0.0, 0.0, 1.0],
                "scale": [1.0, 1.0, 1.0],
            }
        )
        self.json_dic["scenes"][0]["nodes"].append(len(self.json_dic["nodes"]) - 1)

    def pack(self) -> None:
        bin_json, self.bin = self.glb_bin_collector.pack_all()
        self.json_dic.update(bin_json)
        if not self.json_dic["meshes"]:
            del self.json_dic["meshes"]
        if not self.json_dic["materials"]:
            del self.json_dic["materials"]
        self.result = gltf.pack_glb(self.json_dic, self.bin)

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
