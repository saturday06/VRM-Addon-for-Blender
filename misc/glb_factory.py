"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""
from .glb_bin_collection import GlbBinCollection, ImageBin, GlbBin
from .version import addon_version
from ..gl_constants import GlConstants
from .. import vrm_types
from collections import OrderedDict
from math import floor
from mathutils import Matrix as bMatrix
import json
import struct
from sys import float_info
import bpy
import bmesh


class GlbObj:
    class ValidationError(Exception):
        pass

    def __init__(self):
        if bpy.ops.vrm.model_validate() != "{FINISHED}":
            raise self.ValidationError()

        self.json_dic = OrderedDict()
        self.bin = b""
        self.glb_bin_collector = GlbBinCollection()
        self.armature = [obj for obj in bpy.context.selected_objects if obj.type == "ARMATURE"][0]
        self.result = None

    def convert_bpy2glb(self, vrm_version):
        self.VRM_version = vrm_version
        self.image_to_bin()
        self.armature_to_node_and_scenes_dic()  # 親のないboneは1つだけ as root_bone
        self.material_to_dic()
        self.mesh_to_bin_and_dic()
        self.json_dic["scene"] = 0
        self.gltf_meta_to_dic()
        self.vrm_meta_to_dic()  # colliderとかmetaとか....
        self.finalize()
        return self.result

    @staticmethod
    def axis_blender_to_glb(vec3):
        return [vec3[i] * t for i, t in zip([0, 2, 1], [-1, 1, 1])]

    @staticmethod
    def textblock2str(textblock):
        return "".join([line.body for line in textblock.lines])

    def image_to_bin(self):
        # collect used image
        used_image = set()
        used_material_set = set()
        for mesh in [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]:
            for mat in mesh.data.materials:
                used_material_set.add(mat)

        shader_nodes = [
            (node.inputs["Surface"].links[0].from_node, mat)
            for mat in used_material_set
            for node in mat.node_tree.nodes
            if node.type == "OUTPUT_MATERIAL"
            and node.inputs["Surface"].links[0].from_node.type == "GROUP"
            and node.inputs["Surface"].links[0].from_node.node_tree.get("SHADER") is not None
        ]
        # image fetching
        for node, mat in shader_nodes:
            if node.node_tree["SHADER"] == "MToon_unversioned":
                mat["vrm_shader"] = "MToon_unversioned"
                for shader_vals in vrm_types.MaterialMtoon.texture_kind_exchange_dic.values():
                    if shader_vals is None:
                        continue
                    else:
                        if shader_vals == "ReceiveShadow_Texture":
                            if node.inputs[shader_vals + "_alpha"].links:
                                n = node.inputs[shader_vals + "_alpha"].links[0].from_node
                                used_image.add(n.image)
                        elif node.inputs[shader_vals].links:
                            n = node.inputs[shader_vals].links[0].from_node
                            used_image.add(n.image)
            elif node.node_tree["SHADER"] == "GLTF":
                mat["vrm_shader"] = "GLTF"
                texture_input_name_list = [
                    "color_texture",
                    "normal",
                    "emissive_texture",
                    "occlusion_texture",
                ]
                for k in texture_input_name_list:
                    if node.inputs[k].links:
                        n = node.inputs[k].links[0].from_node
                        used_image.add(n.image)

            elif node.node_tree["SHADER"] == "TRANSPARENT_ZWRITE":
                mat["vrm_shader"] = "TRANSPARENT_ZWRITE"
                if node.inputs["Main_Texture"].links:
                    n = node.inputs["Main_Texture"].links[0].from_node
                    used_image.add(n.image)
            else:
                # ?
                pass
        # thumbnail
        if self.armature.get("texture") is not None:
            used_image.add(bpy.data.images[self.armature["texture"]])

        for image in used_image:
            with open(image.filepath_from_user(), "rb") as f:
                image_bin = f.read()
            name = image.name
            filetype = "image/" + image.file_format.lower()
            ImageBin(image_bin, name, filetype, self.glb_bin_collector)
        return

    def armature_to_node_and_scenes_dic(self):
        nodes = []
        scene = []
        skins = []

        bone_id_dic = {b.name: bone_id for bone_id, b in enumerate(self.armature.data.bones)}

        def bone_to_node(b_bone):
            parent_head_local = b_bone.parent.head_local if b_bone.parent is not None else [0, 0, 0]
            node = OrderedDict(
                {
                    "name": b_bone.name,
                    "translation": self.axis_blender_to_glb(
                        [b_bone.head_local[i] - parent_head_local[i] for i in range(3)]
                    ),
                    # "rotation":[0,0,0,1],
                    # "scale":[1,1,1],
                    "children": [bone_id_dic[ch.name] for ch in b_bone.children],
                }
            )
            if len(node["children"]) == 0:
                del node["children"]
            return node

        skin = {"joints": []}
        for bone in self.armature.data.bones:
            if bone.parent is None:  # root bone
                root_bone_id = bone_id_dic[bone.name]
                skin["joints"].append(root_bone_id)
                skin["skeleton"] = root_bone_id
                scene.append(root_bone_id)
                nodes.append(bone_to_node(bone))
                bone_children = [b for b in bone.children]
                while bone_children:
                    child = bone_children.pop()
                    nodes.append(bone_to_node(child))
                    skin["joints"].append(bone_id_dic[child.name])
                    bone_children += [ch for ch in child.children]
                nodes = sorted(nodes, key=lambda node: bone_id_dic[node["name"]])
        skins.append(skin)

        skin_invert_matrix_bin = b""
        f_4x4_packer = struct.Struct("<16f").pack
        for node_id in skins[0]["joints"]:
            bone_name = nodes[node_id]["name"]
            bone_glb_world_pos = self.axis_blender_to_glb(self.armature.data.bones[bone_name].head_local)
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
            skin_invert_matrix_bin, "MAT4", GlConstants.FLOAT, len(skins[0]["joints"]), None, self.glb_bin_collector,
        )
        skins[0]["inverseBindMatrices"] = im_bin.accessor_id

        self.json_dic.update({"scenes": [{"nodes": scene}]})
        self.json_dic.update({"nodes": nodes})
        self.json_dic.update({"skins": skins})
        return

    def material_to_dic(self):
        glb_material_list = []
        vrm_material_props_list = []

        image_id_dic = {image.name: image.image_id for image in self.glb_bin_collector.image_bins}
        sampler_dic = OrderedDict()
        texture_dic = OrderedDict()
        sampler_count = 0
        texture_count = 0

        used_material_set = set()
        for mesh in [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]:
            for mat in mesh.data.materials:
                used_material_set.add(mat)
        # region texture func

        def add_texture(image_name, wrap_type, filter_type):
            nonlocal sampler_count
            nonlocal texture_count
            if (wrap_type, filter_type) not in sampler_dic.keys():
                sampler_dic.update({(wrap_type, filter_type): sampler_count})
                sampler_count += 1
            if (image_id_dic[image_name], sampler_dic[(wrap_type, filter_type)]) not in texture_dic.keys():
                texture_dic.update({(image_id_dic[image_name], sampler_dic[(wrap_type, filter_type)]): texture_count})
                texture_count += 1
            return texture_dic[(image_id_dic[image_name], sampler_dic[(wrap_type, filter_type)])]

        def apply_texture_and_sampler_to_dic():
            if sampler_count > 0:
                sampler_list = self.json_dic["samplers"] = []
                for sampler in sampler_dic.keys():
                    sampler_list.append(
                        {"magFilter": sampler[1], "minFilter": sampler[1], "wrapS": sampler[0], "wrapT": sampler[0]}
                    )
            if texture_count > 0:
                textures = []
                for tex in texture_dic:
                    texture = {"sampler": tex[1], "source": tex[0]}
                    textures.append(texture)
                self.json_dic.update({"textures": textures})

        # region function separate by shader
        def pbr_fallback(
            base_color=(1, 1, 1, 1),
            metalness=0,
            roughness=0.9,
            base_color_texture=(None, None, None),
            metallic_roughness_texture=(None, None, None),
            transparent_method="OPAQUE",
            transparency_cutoff=0.5,
            unlit=True,
            doublesided=False,
        ):
            """transparent_method = {"OPAQUE","MASK","BLEND"}"""
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

            if base_color_texture[0] is not None:
                fallback_dic["pbrMetallicRoughness"].update(
                    {"baseColorTexture": {"index": add_texture(*base_color_texture), "texCoord": 0}}  # TODO:
                )
            if metallic_roughness_texture[0] is not None:
                fallback_dic["pbrMetallicRoughness"].update(
                    {
                        "metallicRoughnessTexture": {
                            "index": add_texture(*metallic_roughness_texture),
                            "texCoord": 0,  # TODO:
                        }
                    }
                )
            fallback_dic["alphaMode"] = transparent_method
            if transparent_method == "MASK":
                fallback_dic["alphaCutoff"] = transparency_cutoff
            if unlit:
                fallback_dic["extensions"] = {"KHR_materials_unlit": {}}
            fallback_dic["doubleSided"] = doublesided
            return fallback_dic

        # region util func
        def get_texture_name_and_sampler_type(shader_node, input_socket_name):
            tex_name = None
            wrap_type = None
            filter_type = None
            if shader_node.inputs.get(input_socket_name):
                if shader_node.inputs.get(input_socket_name).links:
                    tex_name = shader_node.inputs.get(input_socket_name).links[0].from_node.image.name
                    # blender is ('Linear', 'Closest', 'Cubic', 'Smart') gltf is Linear, Closest
                    if shader_node.inputs.get(input_socket_name).links[0].from_node.interpolation == "Closest":
                        filter_type = GlConstants.NEAREST
                    else:
                        filter_type = GlConstants.LINEAR
                    # blender is ('REPEAT', 'EXTEND', 'CLIP') gltf is CLAMP_TO_EDGE,MIRRORED_REPEAT,REPEAT
                    if shader_node.inputs.get(input_socket_name).links[0].from_node.extension == "REPEAT":
                        wrap_type = GlConstants.REPEAT
                    else:
                        wrap_type = GlConstants.CLAMP_TO_EDGE
            return tex_name, wrap_type, filter_type

        def get_float_value(shader_node, input_socket_name):
            float_val = None
            if shader_node.inputs.get(input_socket_name):
                if shader_node.inputs.get(input_socket_name).links:
                    float_val = shader_node.inputs.get(input_socket_name).links[0].from_node.outputs[0].default_value
                else:
                    float_val = shader_node.inputs.get(input_socket_name).default_value
            return float_val

        def get_rgba_val(shader_node, input_socket_name):
            rgba_val = None
            if shader_node.inputs.get(input_socket_name):
                if shader_node.inputs.get(input_socket_name).links:
                    rgba_val = [
                        shader_node.inputs.get(input_socket_name).links[0].from_node.outputs[0].default_value[i]
                        for i in range(4)
                    ]
                else:
                    rgba_val = [shader_node.inputs.get(input_socket_name).default_value[i] for i in range(4)]
            return rgba_val

        # endregion util func

        def make_mtoon_unversioned_extension_dic(b_mat, mtoon_shader_node):
            mtoon_dic = OrderedDict()
            mtoon_dic["name"] = b_mat.name
            mtoon_dic["shader"] = "VRM/MToon"
            mtoon_dic["keywordMap"] = keyword_map = {}
            mtoon_dic["tagMap"] = tag_map = {}
            mtoon_float_dic = mtoon_dic["floatProperties"] = OrderedDict()
            mtoon_vector_dic = mtoon_dic["vectorProperties"] = OrderedDict()
            mtoon_texture_dic = mtoon_dic["textureProperties"] = OrderedDict()

            outline_width_mode = 0
            outline_color_mode = 0
            for float_key, float_prop in [
                (k, val) for k, val in vrm_types.MaterialMtoon.float_props_exchange_dic.items() if val is not None
            ]:
                float_val = get_float_value(mtoon_shader_node, float_prop)
                if float_val is not None:
                    mtoon_float_dic[float_key] = float_val
                    if float_key == "OutlineWidthMode":
                        outline_width_mode = min(max(round(float_val), 0), 2)
                        mtoon_float_dic[float_key] = int(outline_width_mode)
                    if float_key == "OutlineColorMode":
                        outline_color_mode = min(max(round(float_val), 0), 1)
                        mtoon_float_dic[float_key] = int(outline_color_mode)

            def outline_keyword_set(width_world, width_screen, color_fixed, color_mixed):
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

            vec_prop_set = set(vrm_types.MaterialMtoon.vector_props_exchange_dic.values()) - set(
                vrm_types.MaterialMtoon.texture_kind_exchange_dic.values()
            )
            for vector_key, vector_props in [
                (k, v) for k, v in vrm_types.MaterialMtoon.vector_props_exchange_dic.items() if v in vec_prop_set
            ]:
                vector_val = get_rgba_val(mtoon_shader_node, vector_props)
                if vector_val is not None:
                    mtoon_vector_dic[vector_key] = vector_val

            use_normalmap = False
            maintex = (None, None, None)
            for (texture_key, texture_prop) in vrm_types.MaterialMtoon.texture_kind_exchange_dic.items():
                tex = get_texture_name_and_sampler_type(mtoon_shader_node, texture_prop)
                if tex[0] is not None:
                    mtoon_texture_dic[texture_key] = add_texture(*tex)
                    mtoon_vector_dic[texture_key] = [0, 0, 1, 1]
                    if texture_prop == "MainTexture":
                        maintex = tex
                        uv_offset_scaling_node = None
                        try:
                            uv_offset_scaling_node = (
                                mtoon_shader_node.inputs[texture_prop].links[0].from_node.inputs[0].links[0].from_node
                            )
                        except IndexError:
                            uv_offset_scaling_node = None
                        if uv_offset_scaling_node is not None and uv_offset_scaling_node.type == "MAPPING'":
                            if bpy.app.version[1] == 80:
                                mtoon_vector_dic[texture_key] = [
                                    uv_offset_scaling_node.translation[0],
                                    uv_offset_scaling_node.translation[1],
                                    uv_offset_scaling_node.scale[0],
                                    uv_offset_scaling_node.scale[1],
                                ]
                            else:
                                mtoon_vector_dic[texture_key] = [
                                    uv_offset_scaling_node.inputs["Location"].default_value[0],
                                    uv_offset_scaling_node.inputs["Location"].default_value[1],
                                    uv_offset_scaling_node.inputs["Scale"].default_value[0],
                                    uv_offset_scaling_node.inputs["Scale"].default_value[1],
                                ]
                        else:
                            mtoon_vector_dic[texture_key] = [0, 0, 1, 1]
                    elif texture_prop == "NormalmapTexture":
                        use_normalmap = True

            def material_prop_setter(
                blend_mode, src_blend, dst_blend, z_write, alphatest, render_queue, render_type,
            ):
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
            keyword_map.update({"_ALPHABLEND_ON": b_mat.blend_method not in ("OPAQUE", "CLIP")})
            keyword_map.update({"_ALPHAPREMULTIPLY_ON": False})

            mtoon_float_dic["_MToonVersion"] = vrm_types.MaterialMtoon.version
            mtoon_float_dic["_CullMode"] = 2 if b_mat.use_backface_culling else 0  # no cull or bf cull
            mtoon_float_dic["_OutlineCullMode"] = 1  # front face cull (for invert normal outline)
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
                base_color=mtoon_vector_dic["_Color"],
                base_color_texture=maintex,
                transparent_method=transparent_method,
                transparency_cutoff=transparency_cutoff,
                doublesided=b_mat.use_backface_culling,
            )
            if self.VRM_version == "1.0":
                mtoon_ext_dic = {}
                mtoon_ext_dic["properties"] = mt_prop = {}
                mt_prop = {"version": "3.2"}
                blendmode = mtoon_float_dic.get("_BlendMode")
                if blendmode == 0:
                    blendmode = "opaque"
                elif blendmode == 1:
                    blendmode = "cutout"
                else:
                    blendmode = "transparent"
                # TODO transparentWithZWrite
                mt_prop["renderMode"] = blendmode

                mt_prop["cullMode"] = (
                    mtoon_float_dic.get("_CullMode") == "back" if b_mat.use_backface_culling else "off"
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
                mt_prop["shadowReceiveMultiplierFactor"] = mtoon_float_dic.get("_ReceiveShadowRate")
                mt_prop["shadowReceiveMultiplierMultiplyTexture"] = mtoon_texture_dic.get("_ReceiveShadowTexture")
                mt_prop["litAndShadeMixingMultiplierFactor"] = mtoon_float_dic.get("_ShadingGradeRate")
                mt_prop["litAndShadeMixingMultiplierMultiplyTexture"] = mtoon_texture_dic.get("_ShadingGradeTexture")
                mt_prop["lightColorAttenuationFactor"] = mtoon_float_dic.get("_LightColorAttenuation")
                mt_prop["giIntensityFactor"] = mtoon_float_dic.get("_IndirectLightIntensity")
                mt_prop["normalTexture"] = mtoon_texture_dic.get("_BumpMap")
                mt_prop["normalScaleFactor"] = mtoon_float_dic.get("_BumpScale")
                mt_prop["emissionFactor"] = mtoon_vector_dic.get("_EmissionColor")
                mt_prop["emissionMultiplyTexture"] = mtoon_texture_dic.get("_EmissionMap")
                mt_prop["additiveTexture"] = mtoon_texture_dic.get("_SphereAdd")
                mt_prop["rimFactor"] = mtoon_vector_dic.get("_RimColor")
                mt_prop["rimMultiplyTexture"] = mtoon_texture_dic.get("_RimTexture")
                mt_prop["rimLightingMixFactor"] = mtoon_float_dic.get("_RimLightingMix")
                mt_prop["rimFresnelPowerFactor"] = mtoon_float_dic.get("_RimFresnelPower")
                mt_prop["rimLiftFactor"] = mtoon_float_dic.get("_RimLift")
                mt_prop["outlineWidthMode"] = ["none", "worldCoordinates", "screenCoordinates"][
                    floor(mtoon_float_dic.get("_OutlineWidthMode"))
                    if mtoon_float_dic.get("_OutlineWidthMode") is not None
                    else 0
                ]
                mt_prop["outlineWidthFactor"] = mtoon_vector_dic.get("_OutlineColor")
                mt_prop["outlineWidthMultiplyTexture"] = mtoon_texture_dic.get("_OutlineWidthTexture")
                mt_prop["outlineScaledMaxDistanceFactor"] = mtoon_float_dic.get("_OutlineScaledMaxDistance")
                mt_prop["outlineColorMode"] = ["fixedColor", "mixedLighting"][
                    floor(mtoon_float_dic.get("_OutlineLightingMix"))
                    if mtoon_float_dic.get("_OutlineLightingMix") is not None
                    else 0
                ]
                mt_prop["outlineFactor"] = mtoon_float_dic.get("_OutlineWidth")
                mt_prop["outlineLightingMixFactor"] = mtoon_float_dic.get("OutlineLightingMix")

                uv_transforms = mtoon_vector_dic.get("_MainTex")
                if uv_transforms is None:
                    uv_transforms = [0, 0, 1, 1]
                mt_prop["mainTextureLeftBottomOriginOffset"] = uv_transforms[0:2]
                mt_prop["mainTextureLeftBottomOriginScale"] = uv_transforms[2:4]
                mt_prop["uvAnimationMaskTexture"] = mtoon_texture_dic.get("_UvAnimMaskTexture")
                mt_prop["uvAnimationScrollXSpeedFactor"] = mtoon_float_dic.get("_UvAnimScrollX")
                mt_prop["uvAnimationScrollYSpeedFactor"] = mtoon_float_dic.get("_UvAnimScrollY")
                mt_prop["uvAnimationRotationSpeedFactor"] = mtoon_float_dic.get("_UvAnimRotation")
                gc_list = []
                for k, v in mt_prop.items():
                    if v is None:
                        gc_list.append(k)
                for garbage in gc_list:
                    mt_prop.pop(garbage)

                pbr_dic["extensions"].update({"VRMC_materials_mtoon": mtoon_ext_dic})
            return mtoon_dic, pbr_dic

        def make_gltf_mat_dic(b_mat, gltf_shader_node):
            gltf_dic = OrderedDict()
            gltf_dic["name"] = b_mat.name
            gltf_dic["shader"] = "VRM_USE_GLTFSHADER"
            gltf_dic["keywordMap"] = {}
            gltf_dic["tagMap"] = {}
            gltf_dic["floatProperties"] = {}
            gltf_dic["vectorProperties"] = {}
            gltf_dic["textureProperties"] = {}

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
                base_color=get_rgba_val(gltf_shader_node, "base_Color"),
                metalness=get_float_value(gltf_shader_node, "metallic"),
                roughness=get_float_value(gltf_shader_node, "roughness"),
                base_color_texture=get_texture_name_and_sampler_type(gltf_shader_node, "color_texture"),
                metallic_roughness_texture=get_texture_name_and_sampler_type(
                    gltf_shader_node, "metallic_roughness_texture"
                ),
                transparent_method=transparent_method,
                transparency_cutoff=transparency_cutoff,
                unlit=True if get_float_value(gltf_shader_node, "unlit") >= 0.5 else False,
                doublesided=b_mat.use_backface_culling,
            )

            def pbr_tex_add(texture_type, socket_name):
                img = get_texture_name_and_sampler_type(gltf_shader_node, socket_name)
                if img[0] is not None:
                    pbr_dic[texture_type] = {"index": add_texture(*img), "texCoord": 0}
                else:
                    print(socket_name)

            pbr_tex_add("normalTexture", "normal")
            pbr_tex_add("emissiveTexture", "emissive_texture")
            pbr_tex_add("occlusionTexture", "occlusion_texture")
            pbr_dic["emissiveFactor"] = get_rgba_val(gltf_shader_node, "emissive_color")[0:3]

            return gltf_dic, pbr_dic

        def make_trnszw_mat_dic(b_mat, transzw_shader_node):
            zw_dic = OrderedDict()
            zw_dic["name"] = b_mat.name
            zw_dic["shader"] = "VRM/UnlitTransparentZWrite"
            zw_dic["renderQueue"] = 2600
            zw_dic["keywordMap"] = {}
            zw_dic["tagMap"] = {"RenderType": "Transparent"}
            zw_dic["floatProperties"] = {}
            zw_dic["vectorProperties"] = {}
            zw_dic["textureProperties"] = {}
            color_tex = get_texture_name_and_sampler_type(transzw_shader_node, "Main_Texture")
            if color_tex is not None:
                zw_dic["textureProperties"] = {"_MainTex": add_texture(*color_tex)}
                zw_dic["vectorProperties"] = {"_MainTex": [0, 0, 1, 1]}
            pbr_dic = pbr_fallback(base_color_texture=color_tex, transparent_method="BLEND")

            return zw_dic, pbr_dic

        # endregion function separate by shader

        for b_mat in used_material_set:

            if b_mat["vrm_shader"] == "MToon_unversioned":
                for node in b_mat.node_tree.nodes:
                    if node.type == "OUTPUT_MATERIAL":
                        mtoon_shader_node = node.inputs["Surface"].links[0].from_node
                        break
                material_properties_dic, pbr_dic = make_mtoon_unversioned_extension_dic(b_mat, mtoon_shader_node)
            elif b_mat["vrm_shader"] == "GLTF":
                for node in b_mat.node_tree.nodes:
                    if node.type == "OUTPUT_MATERIAL":
                        gltf_shader_node = node.inputs["Surface"].links[0].from_node
                        break
                material_properties_dic, pbr_dic = make_gltf_mat_dic(b_mat, gltf_shader_node)
            elif b_mat["vrm_shader"] == "TRANSPARENT_ZWRITE":
                for node in b_mat.node_tree.nodes:
                    if node.type == "OUTPUT_MATERIAL":
                        zw_shader_node = node.inputs["Surface"].links[0].from_node
                        break
                material_properties_dic, pbr_dic = make_trnszw_mat_dic(b_mat, zw_shader_node)
            else:
                print("please use vrm_shader")
                raise Exception  # ?

            glb_material_list.append(pbr_dic)
            vrm_material_props_list.append(material_properties_dic)

        apply_texture_and_sampler_to_dic()
        self.json_dic.update({"materials": glb_material_list})
        if self.VRM_version == "0.0":
            self.json_dic.update({"extensions": {"VRM": {"materialProperties": vrm_material_props_list}}})
        return

    def mesh_to_bin_and_dic(self):
        self.json_dic["meshes"] = []
        for id, mesh in enumerate([obj for obj in bpy.context.selected_objects if obj.type == "MESH"]):
            is_skin_mesh = True
            if len([m for m in mesh.modifiers if m.type == "ARMATURE"]) == 0:
                if mesh.parent is not None:
                    if mesh.parent.type == "ARMATURE":
                        if mesh.parent_bone is not None:
                            is_skin_mesh = False
            node_dic = OrderedDict(
                {
                    "name": mesh.name,
                    "translation": self.axis_blender_to_glb(mesh.location),
                    "rotation": [0, 0, 0, 1],  # このへんは規約なので
                    "scale": [1, 1, 1],  # このへんは規約なので
                    "mesh": id,
                }
            )
            if is_skin_mesh:
                node_dic["translation"] = [0, 0, 0]  # skinnedmeshはtransformを無視される
                mesh.data.transform(bMatrix.Translation(mesh.location), shape_keys=True)  # 前に続きmeshを動かす(後で戻す
                node_dic["skin"] = 0  # TODO: 決め打ちってどうよ:一体のモデルなのだから2つもあっては困る(から決め打ち(やめろ(やだ))
            self.json_dic["nodes"].append(node_dic)

            mesh_node_id = len(self.json_dic["nodes"]) - 1

            if is_skin_mesh:
                self.json_dic["scenes"][0]["nodes"].append(mesh_node_id)
            else:
                parent_node = [node for node in self.json_dic["nodes"] if node["name"] == mesh.parent_bone][0]
                if "children" in parent_node.keys():
                    parent_node["children"].append(mesh_node_id)
                else:
                    parent_node["children"] = [mesh_node_id]
                relate_pos = [
                    mesh.location[i] - self.armature.data.bones[mesh.parent_bone].head_local[i] for i in range(3)
                ]
                self.json_dic["nodes"][mesh_node_id]["translation"] = self.axis_blender_to_glb(relate_pos)

            # region hell
            bpy.ops.object.mode_set(mode="OBJECT")
            mesh.hide_viewport = False
            mesh.hide_select = False
            bpy.context.view_layer.objects.active = mesh
            bpy.ops.object.mode_set(mode="EDIT")
            bm = bmesh.from_edit_mesh(mesh.data)

            # region temporary used
            mat_id_dic = {mat["name"]: i for i, mat in enumerate(self.json_dic["materials"])}
            material_slot_dic = {i: mat.name for i, mat in enumerate(mesh.material_slots)}
            node_id_dic = {node["name"]: i for i, node in enumerate(self.json_dic["nodes"])}

            def joint_id_from_node_name_solver(node_name):
                try:
                    node_id = node_id_dic[node_name]
                    joint_id = self.json_dic["skins"][0]["joints"].index(node_id)
                except (ValueError, KeyError):
                    joint_id = -1  # 存在しないボーンを指してる場合は-1を返す
                    print(f"{node_name} bone may be not exist")
                return joint_id

            v_group_name_dic = {i: vg.name for i, vg in enumerate(mesh.vertex_groups)}
            fmin, fmax = -float_info.max, float_info.max  # .minはfloatで一番細かい正の数を示す。
            unique_vertex_id = 0
            unique_vertex_dic = {}  # {(uv...,vertex_index):unique_vertex_id} (uvと頂点番号が同じ頂点は同じものとして省くようにする)
            uvlayers_dic = {i: uvlayer.name for i, uvlayer in enumerate(mesh.data.uv_layers)}

            def fetch_morph_vertex_normal_difference():
                morph_normal_diff_dic = {}
                vert_base_normal_dic = OrderedDict()
                for kb in mesh.data.shape_keys.key_blocks:
                    vert_base_normal_dic.update({kb.name: kb.normals_vertex_get()})
                for k, v in vert_base_normal_dic.items():
                    if k == "Basis":
                        continue
                    values = []
                    for vert_morph_normal, vert_base_normal in zip(
                        zip(*[iter(v)] * 3), zip(*[iter(vert_base_normal_dic["Basis"])] * 3),
                    ):
                        values.append([vert_morph_normal[i] - vert_base_normal[i] for i in range(3)])
                    morph_normal_diff_dic.update({k: values})
                return morph_normal_diff_dic

            # endregion  temporary_used
            primitive_index_bin_dic = OrderedDict({mat_id_dic[mat.name]: b"" for mat in mesh.material_slots})
            primitive_index_vertex_count = OrderedDict({mat_id_dic[mat.name]: 0 for mat in mesh.material_slots})
            if mesh.data.shape_keys is None:
                shape_pos_bin_dic = {}
                shape_normal_bin_dic = {}
                shape_min_max_dic = {}
                morph_normal_diff_dic = {}
            else:
                shape_pos_bin_dic = OrderedDict(
                    {shape.name: b"" for shape in mesh.data.shape_keys.key_blocks[1:]}
                )  # 0番目Basisは省く
                shape_normal_bin_dic = OrderedDict({shape.name: b"" for shape in mesh.data.shape_keys.key_blocks[1:]})
                shape_min_max_dic = OrderedDict(
                    {
                        shape.name: [[fmax, fmax, fmax], [fmin, fmin, fmin]]
                        for shape in mesh.data.shape_keys.key_blocks[1:]
                    }
                )
                morph_normal_diff_dic = (
                    fetch_morph_vertex_normal_difference() if self.VRM_version == "0.0" else {}
                )  # {morphname:{vertexid:[diff_X,diff_y,diff_z]}}
            position_bin = b""
            position_min_max = [[fmax, fmax, fmax], [fmin, fmin, fmin]]
            normal_bin = b""
            joints_bin = b""
            weights_bin = b""
            texcoord_bins = {id: b"" for id in uvlayers_dic.keys()}
            f_vec4_packer = struct.Struct("<ffff").pack
            f_vec3_packer = struct.Struct("<fff").pack
            f_pair_packer = struct.Struct("<ff").pack
            i_scalar_packer = struct.Struct("<I").pack
            h_vec4_packer = struct.Struct("<HHHH").pack

            def min_max(minmax, position):
                for i in range(3):
                    minmax[0][i] = position[i] if position[i] < minmax[0][i] else minmax[0][i]
                    minmax[1][i] = position[i] if position[i] > minmax[1][i] else minmax[1][i]
                return

            if mesh.data.has_custom_normals:
                mesh.data.calc_loop_triangles()
                mesh.data.calc_normals_split()

            for face in bm.faces:
                for loop in face.loops:
                    uv_list = []
                    for uvlayer_name in uvlayers_dic.values():
                        uv_layer = bm.loops.layers.uv[uvlayer_name]
                        uv_list += [loop[uv_layer].uv[0], loop[uv_layer].uv[1]]

                    vert_normal = [0, 0, 0]
                    if mesh.data.has_custom_normals:
                        tri = mesh.data.loop_triangles[face.index]
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
                    cached_vert_id = unique_vertex_dic.get(vertex_key)  # keyがなければNoneを返す
                    if cached_vert_id is not None:
                        primitive_index_bin_dic[mat_id_dic[material_slot_dic[face.material_index]]] += i_scalar_packer(
                            cached_vert_id
                        )
                        primitive_index_vertex_count[mat_id_dic[material_slot_dic[face.material_index]]] += 1
                        continue
                    else:
                        unique_vertex_dic[vertex_key] = unique_vertex_id
                    for uvlayer_id, uvlayer_name in uvlayers_dic.items():
                        uv_layer = bm.loops.layers.uv[uvlayer_name]
                        uv = loop[uv_layer].uv
                        texcoord_bins[uvlayer_id] += f_pair_packer(uv[0], 1 - uv[1])  # blenderとglbのuvは上下逆
                    for shape_name in shape_pos_bin_dic.keys():
                        shape_layer = bm.verts.layers.shape[shape_name]
                        morph_pos = self.axis_blender_to_glb(
                            [loop.vert[shape_layer][i] - loop.vert.co[i] for i in range(3)]
                        )
                        shape_pos_bin_dic[shape_name] += f_vec3_packer(*morph_pos)
                        if self.VRM_version == "0.0":
                            shape_normal_bin_dic[shape_name] += f_vec3_packer(
                                *self.axis_blender_to_glb(morph_normal_diff_dic[shape_name][loop.vert.index])
                            )
                        min_max(shape_min_max_dic[shape_name], morph_pos)
                    if is_skin_mesh:
                        magic = 0
                        joints = [magic, magic, magic, magic]
                        weights = [0.0, 0.0, 0.0, 0.0]
                        weight_count = 0
                        for v_group in mesh.data.vertices[loop.vert.index].groups:
                            joint_id = joint_id_from_node_name_solver(v_group_name_dic[v_group.group])
                            if joint_id == -1:  # 存在しないボーンを指してる場合は-1を返されてるので、その場合は飛ばす
                                continue
                            weight_count += 1
                            weights.pop(3)
                            weights.insert(0, v_group.weight)
                            joints.pop(3)
                            joints.insert(0, joint_id)
                            if weight_count >= 4:
                                break
                        normalize_fact = sum(weights)
                        if normalize_fact != 0:
                            normalize_fact = 1 / normalize_fact
                        try:
                            weights = [weights[i] * normalize_fact for i in range(4)]
                        except ZeroDivisionError:  # validationではじけてるはず…
                            print(f"No weight on vertex id:{loop.vert.index} in: {mesh.name}")
                            raise ZeroDivisionError
                        if sum(weights) < 1:
                            weights[0] += 1 - sum(weights)
                        joints_bin += h_vec4_packer(*joints)
                        weights_bin += f_vec4_packer(*weights)

                    vert_location = self.axis_blender_to_glb(loop.vert.co)
                    position_bin += f_vec3_packer(*vert_location)
                    min_max(position_min_max, vert_location)
                    normal_bin += f_vec3_packer(*self.axis_blender_to_glb(vert_normal))
                    primitive_index_bin_dic[mat_id_dic[material_slot_dic[face.material_index]]] += i_scalar_packer(
                        unique_vertex_id
                    )
                    primitive_index_vertex_count[mat_id_dic[material_slot_dic[face.material_index]]] += 1
                    unique_vertex_id += 1

            # DONE :index position, uv, normal, position morph,JOINT WEIGHT
            # TODO: morph_normal, v_color...?
            primitive_glbs_dic = OrderedDict(
                {
                    mat_id: GlbBin(
                        index_bin,
                        "SCALAR",
                        GlConstants.UNSIGNED_INT,
                        primitive_index_vertex_count[mat_id],
                        None,
                        self.glb_bin_collector,
                    )
                    for mat_id, index_bin in primitive_index_bin_dic.items()
                    if index_bin != b""
                }
            )
            pos_glb = GlbBin(
                position_bin, "VEC3", GlConstants.FLOAT, unique_vertex_id, position_min_max, self.glb_bin_collector,
            )
            nor_glb = GlbBin(normal_bin, "VEC3", GlConstants.FLOAT, unique_vertex_id, None, self.glb_bin_collector)
            uv_glbs = [
                GlbBin(texcoord_bin, "VEC2", GlConstants.FLOAT, unique_vertex_id, None, self.glb_bin_collector)
                for texcoord_bin in texcoord_bins.values()
            ]
            if is_skin_mesh:
                joints_glb = GlbBin(
                    joints_bin, "VEC4", GlConstants.UNSIGNED_SHORT, unique_vertex_id, None, self.glb_bin_collector,
                )
                weights_glb = GlbBin(
                    weights_bin, "VEC4", GlConstants.FLOAT, unique_vertex_id, None, self.glb_bin_collector,
                )
            if len(shape_pos_bin_dic.keys()) != 0:
                morph_pos_glbs = [
                    GlbBin(
                        morph_pos_bin,
                        "VEC3",
                        GlConstants.FLOAT,
                        unique_vertex_id,
                        morph_minmax,
                        self.glb_bin_collector,
                    )
                    for morph_pos_bin, morph_minmax in zip(shape_pos_bin_dic.values(), shape_min_max_dic.values())
                ]
                if self.VRM_version == "0.0":
                    morph_normal_glbs = [
                        GlbBin(
                            morph_normal_bin, "VEC3", GlConstants.FLOAT, unique_vertex_id, None, self.glb_bin_collector,
                        )
                        for morph_normal_bin in shape_normal_bin_dic.values()
                    ]
            primitive_list = []
            for primitive_id, index_glb in primitive_glbs_dic.items():
                primitive = OrderedDict({"mode": 4})
                primitive["material"] = primitive_id
                primitive["indices"] = index_glb.accessor_id
                primitive["attributes"] = {
                    "POSITION": pos_glb.accessor_id,
                    "NORMAL": nor_glb.accessor_id,
                }
                if is_skin_mesh:
                    primitive["attributes"].update(
                        {"JOINTS_0": joints_glb.accessor_id, "WEIGHTS_0": weights_glb.accessor_id}
                    )
                primitive["attributes"].update(
                    {"TEXCOORD_{}".format(i): uv_glb.accessor_id for i, uv_glb in enumerate(uv_glbs)}
                )
                if len(shape_pos_bin_dic.keys()) != 0:
                    if self.VRM_version == "0.0":
                        primitive["targets"] = [
                            {"POSITION": morph_pos_glb.accessor_id, "NORMAL": morph_normal_glb.accessor_id}
                            for morph_pos_glb, morph_normal_glb in zip(morph_pos_glbs, morph_normal_glbs)
                        ]
                    else:
                        primitive["targets"] = [
                            {"POSITION": morph_pos_glb.accessor_id} for morph_pos_glb in morph_pos_glbs
                        ]
                    primitive["extras"] = {"targetNames": [shape_name for shape_name in shape_pos_bin_dic.keys()]}
                primitive_list.append(primitive)
            self.json_dic["meshes"].append(OrderedDict({"name": mesh.name, "primitives": primitive_list}))
            # endregion hell
            # skinnedmeshなら最初にずらした位置を戻す
            bpy.ops.object.mode_set(mode="OBJECT")
            if is_skin_mesh:
                mesh.data.transform(
                    bMatrix.Translation([n * m for n, m in zip(mesh.location, [-1, -1, -1])]), shape_keys=True,
                )
        bpy.ops.object.mode_set(mode="OBJECT")
        return

    exporter_name = "saturday06_blender_vrm_exporter_experimental_" + ".".join(map(str, addon_version))

    def gltf_meta_to_dic(self):
        gltf_meta_dic = {
            "extensionsUsed": ["VRM", "KHR_materials_unlit", "VRMC_materials_mtoon"],
            "asset": {"generator": self.exporter_name, "version": "2.0"},  # GLTF version
        }

        self.json_dic.update(gltf_meta_dic)
        return

    def vrm_meta_to_dic(self):
        # materialProperties は material_to_dic()で処理する
        # region vrm_extension
        vrm_extension_dic = OrderedDict()
        if self.VRM_version == "0.0":
            vrm_extension_dic["exporterVersion"] = self.exporter_name
        vrm_extension_dic["specVersion"] = self.VRM_version
        # region meta
        vrm_extension_dic["meta"] = vrm_meta_dic = {}
        # 安全側に寄せておく
        if self.VRM_version == "0.0":
            required_vrm_metas = {
                "allowedUserName": "OnlyAuthor",
                "violentUssageName": "Disallow",
                "sexualUssageName": "Disallow",
                "commercialUssageName": "Disallow",
                "licenseName": "Redistribution_Prohibited",
            }
            vrm_metas = [
                "version",  # model version (not VRMspec etc)
                "author",
                "contactInformation",
                "reference",
                "title",
                "otherPermissionUrl",
                "otherLicenseUrl",
            ]
        else:
            required_vrm_metas = {
                "allowedUser": "OnlyAuthor",
                "violentUsage": "Disallow",
                "sexualUsage": "Disallow",
                "commercialUsage": "Disallow",
                "license": "Redistribution_Prohibited",
            }
            vrm_metas = [
                "version",  # model version (not VRMspec etc)
                "author",
                "contactInformation",
                "reference",
                "title",
                "otherPermissionUrl",
                "otherLicenseUrl",
            ]
        for k, v in required_vrm_metas.items():
            vrm_meta_dic[k] = self.armature[k] if k in self.armature.keys() else v
        for key in vrm_metas:
            vrm_meta_dic[key] = self.armature[key] if key in self.armature.keys() else ""

        if "texture" in self.armature.keys():
            thumbnail_index_list = [
                i for i, img in enumerate(self.glb_bin_collector.image_bins) if img.name == self.armature["texture"]
            ]
            if len(thumbnail_index_list) > 0:
                self.json_dic["samplers"].append({"magFilter": 9729, "minFilter": 9729, "wrapS": 10497, "wrapT": 10497})
                self.json_dic["textures"].append(
                    {"sampler": len(self.json_dic["samplers"]) - 1, "source": thumbnail_index_list[0]},
                )
                vrm_meta_dic["texture"] = len(self.json_dic["textures"]) - 1
        # endregion meta
        # region humanoid
        if self.VRM_version == "0.0":
            vrm_extension_dic["humanoid"] = vrm_humanoid_dic = {"humanBones": []}
            node_name_id_dic = {node["name"]: i for i, node in enumerate(self.json_dic["nodes"])}
            for humanbone in vrm_types.HumanBones.requires + vrm_types.HumanBones.defines:
                if humanbone in self.armature.data.keys() and self.armature.data[humanbone] != "":
                    vrm_humanoid_dic["humanBones"].append(
                        {
                            "bone": humanbone,
                            "node": node_name_id_dic[self.armature.data[humanbone]],
                            # TODO min,max,center,axisLength : useDef(ry):Trueなら不要な気がするのでほっとく
                            "useDefaultValues": True,
                        }
                    )
            vrm_humanoid_dic.update(
                json.loads(
                    self.textblock2str(bpy.data.texts[self.armature["humanoid_params"]]), object_pairs_hook=OrderedDict,
                )
            )
        else:
            vrm_extension_dic["humanoid"] = vrm_humanoid_dic = {"humanBones": {}}
            node_name_id_dic = {node["name"]: i for i, node in enumerate(self.json_dic["nodes"])}
            for humanbone in vrm_types.HumanBones.requires + vrm_types.HumanBones.defines:
                if humanbone in self.armature.data.keys() and self.armature.data[humanbone] != "":
                    vrm_humanoid_dic["humanBones"].update(
                        {humanbone: {"node": node_name_id_dic[self.armature.data[humanbone]]}}
                    )

        # endregion humanoid
        # region firstPerson
        vrm_extension_dic["firstPerson"] = vrm_fp_dic = {}
        vrm_fp_dic.update(
            json.loads(
                self.textblock2str(bpy.data.texts[self.armature["firstPerson_params"]]), object_pairs_hook=OrderedDict,
            )
        )
        if "firstPersonBone" in vrm_fp_dic.keys():
            if vrm_fp_dic["firstPersonBone"] != -1:
                vrm_fp_dic["firstPersonBone"] = node_name_id_dic[vrm_fp_dic["firstPersonBone"]]
        if "meshAnnotations" in vrm_fp_dic.keys():
            for mesh_annotation in vrm_fp_dic["meshAnnotations"]:
                mesh_annotation["mesh"] = [
                    i for i, mesh in enumerate(self.json_dic["meshes"]) if mesh["name"] == mesh_annotation["mesh"]
                ][0]
                # TODO VRM1.0 is using node index that has mesh
        # TODO
        if self.VRM_version == "1.0":
            vrm_extension_dic["lookAt"] = vrm_la_dic = {}
            vrm_la_dic.update(
                json.loads(
                    self.textblock2str(bpy.data.texts[self.armature["lookat_params"]]), object_pairs_hook=OrderedDict,
                )
            )

        # endregion firstPerson
        # region blendShapeMaster
        blendshape_group_name = "blendShapeMaster" if self.VRM_version == "0.0" else "blendShape"
        vrm_extension_dic[blendshape_group_name] = vrm_bsm_dic = {}
        bsm_list = json.loads(
            self.textblock2str(bpy.data.texts[self.armature["blendshape_group"]]), object_pairs_hook=OrderedDict,
        )

        # meshを名前からid
        # weightを0-1から0-100に
        # shape_indexを名前からindexに
        def clamp(min, val, max):
            if max >= val:
                if val >= min:
                    return val
                else:
                    print("blendshapeGroup weight is between 0 and 1, value is {}".format(val))
                    return min
            else:
                print("blendshapeGroup weight is between 0 and 1, value is {}".format(val))
                return max

        for bsm in bsm_list:
            for bind in bsm["binds"]:
                # TODO VRM1.0 is using node index that has mesh
                bind["mesh"] = [i for i, mesh in enumerate(self.json_dic["meshes"]) if mesh["name"] == bind["mesh"]][0]
                bind["index"] = self.json_dic["meshes"][bind["mesh"]]["primitives"][0]["extras"]["targetNames"].index(
                    bind["index"]
                )
                bind["weight"] = (
                    clamp(0, bind["weight"] * 100, 100) if self.VRM_version == "0.0" else clamp(0, bind["weight"], 1)
                )
            if self.VRM_version != "0.0":
                for matval in bsm["materialValues"]:
                    matval["material"] = [
                        i for i, mat in enumerate(self.json_dic["materials"]) if mat["name"] == matval["material"]
                    ][0]
        # TODO isBinary handle : 0 or 1 にするフラグ
        vrm_bsm_dic["blendShapeGroups"] = bsm_list
        # endregion blendShapeMaster

        # region secondaryAnimation
        springbone_name = "springBone" if self.VRM_version == "1.0" else "secondaryAnimation"
        vrm_extension_dic[springbone_name] = {"boneGroups": [], "colliderGroups": []}

        # region colliderGroups
        # armatureの子emptyを変換する
        collider_group_list = []
        empty_dic = {node_name_id_dic[ch.parent_bone]: [] for ch in self.armature.children if ch.type == "EMPTY"}
        for child_empty in [ch for ch in self.armature.children if ch.type == "EMPTY"]:
            empty_dic[node_name_id_dic[child_empty.parent_bone]].append(child_empty)
        for node_id, empty_objs in empty_dic.items():
            collider_group = {"node": node_id, "colliders": []}
            colliders = collider_group["colliders"]
            for empty in empty_objs:
                collider = {}
                empty_offset_pos = [
                    empty.matrix_world.to_translation()[i]
                    - self.armature.location[i]
                    - self.armature.data.bones[empty.parent_bone].head_local[i]
                    for i in range(3)
                ]
                if self.VRM_version == "0.0":
                    collider["radius"] = empty.empty_display_size
                    collider["offset"] = OrderedDict(
                        {axis: o_s for axis, o_s in zip(("x", "y", "z"), self.axis_blender_to_glb(empty_offset_pos))}
                    )
                    collider["offset"]["z"] = collider["offset"]["z"] * -1
                else:
                    collider["size"] = [empty.empty_display_size]
                    collider["offset"] = self.axis_blender_to_glb(empty_offset_pos)
                    collider["shapeType"] = "sphere"
                colliders.append(collider)
            collider_group_list.append(collider_group)

        vrm_extension_dic[springbone_name]["colliderGroups"] = collider_group_list
        # endregion colliderGroups

        # region boneGroup
        # ボーン名からnode_idに
        # collider_groupも名前からcolliderGroupのindexに直す
        collider_node_id_list = [c_g["node"] for c_g in collider_group_list]
        bg_list = json.loads(
            self.textblock2str(bpy.data.texts[self.armature["spring_bone"]]), object_pairs_hook=OrderedDict,
        )
        for bone_group in bg_list:
            bone_group["bones"] = [node_name_id_dic[name] for name in bone_group["bones"]]
            bone_group["colliderGroups"] = [
                collider_node_id_list.index(node_name_id_dic[name]) for name in bone_group["colliderGroups"]
            ]
        vrm_extension_dic[springbone_name]["boneGroups"] = bg_list
        # endregion boneGroup
        # endregion secondaryAnimation
        extension_name = "VRM" if self.VRM_version == "0.0" else "VRMC_vrm"
        self.json_dic["extensions"][extension_name].update(vrm_extension_dic)
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
        return

    def finalize(self):
        bin_json, self.bin = self.glb_bin_collector.pack_all()
        self.json_dic.update(bin_json)
        magic = b"glTF" + struct.pack("<I", 2)
        json_str = json.dumps(self.json_dic).encode("utf-8")
        if len(json_str) % 4 != 0:
            for i in range(4 - len(json_str) % 4):
                json_str += b"\x20"
        json_size = struct.pack("<I", len(json_str))
        if len(self.bin) % 4 != 0:
            for i in range(4 - len(self.bin) % 4):
                self.bin += b"\x00"
        bin_size = struct.pack("<I", len(self.bin))
        total_size = struct.pack("<I", len(json_str) + len(self.bin) + 28)  # include header size
        self.result = magic + total_size + json_size + b"JSON" + json_str + bin_size + b"BIN\x00" + self.bin
        return
