# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import json
from typing import Optional, Union

import bpy
from bpy.types import (
    Bone,
    CopyRotationConstraint,
    DampedTrackConstraint,
    EditBone,
    Image,
    Mesh,
    Object,
    PoseBone,
)
from mathutils import Matrix, Vector

from ..common import convert, ops, shader
from ..common.convert import Json
from ..common.logger import get_logger
from ..common.preferences import get_preferences
from ..common.progress import PartialProgress
from ..common.version import get_addon_version
from ..common.vrm1 import human_bone as vrm1_human_bone
from ..common.vrm1.human_bone import HumanBoneName, HumanBoneSpecifications
from ..editor import make_armature, migration
from ..editor.extension import (
    VrmAddonBoneExtensionPropertyGroup as BoneExtension,
)
from ..editor.extension import (
    get_armature_extension,
    get_bone_extension,
    get_material_extension,
    get_object_extension,
)
from ..editor.make_armature import (
    connect_parent_tail_and_child_head_if_very_close_position,
)
from ..editor.mtoon1.property_group import (
    Mtoon1KhrTextureTransformPropertyGroup,
    Mtoon1SamplerPropertyGroup,
    Mtoon1TextureInfoPropertyGroup,
    Mtoon1TexturePropertyGroup,
)
from ..editor.spring_bone1.property_group import (
    SpringBone1ColliderPropertyGroup,
    SpringBone1SpringBonePropertyGroup,
)
from ..editor.vrm1.property_group import (
    Vrm1ExpressionPropertyGroup,
    Vrm1ExpressionsPropertyGroup,
    Vrm1FirstPersonPropertyGroup,
    Vrm1HumanBonesPropertyGroup,
    Vrm1HumanoidPropertyGroup,
    Vrm1LookAtPropertyGroup,
    Vrm1MaterialColorBindPropertyGroup,
    Vrm1MetaPropertyGroup,
)
from .abstract_base_vrm_importer import AbstractBaseVrmImporter

logger = get_logger(__name__)


class Vrm1Importer(AbstractBaseVrmImporter):
    @staticmethod
    def assign_texture_colorspace(image: Image, preferred_colorspace: str) -> None:
        colorspaces = [preferred_colorspace]
        if preferred_colorspace == "Non-Color":
            # https://github.com/saturday06/VRM-Addon-for-Blender/issues/336#issuecomment-1760729404
            colorspaces.extend(["Linear", "Generic Data"])

        colorspace_settings = image.colorspace_settings
        exceptions: list[Exception] = []
        for colorspace in colorspaces:
            # The values that can be set in colorspace_settings.name vary
            # depending on the Blender setup. For example, bpy 3.6.0 from pypi
            # can only choose Linear or sRGB.
            # To detect this, we would ideally want to reference
            # colorspace_settings.bl_rna.properties.get("name").enum_items
            # etc., but it cannot be used because it crashes in Blender 2.93 etc.
            # So we catch exceptions and try until assignment succeeds.
            try:
                colorspace_settings.name = colorspace
            except TypeError as e:
                exceptions.append(e)
            else:
                return

        logger.error(
            "image.colorspace_settings.name doesn't support %s:\n%s",
            colorspaces,
            "\n".join(map(str, exceptions)),
        )

    def assign_texture(
        self,
        texture: Mtoon1TexturePropertyGroup,
        texture_dict: dict[str, Json],
    ) -> None:
        source = texture_dict.get("source")
        if isinstance(source, int):
            image = self.images.get(source)
            if image:
                texture.source = image
                self.assign_texture_colorspace(image, texture.colorspace)

        sampler = texture_dict.get("sampler")
        samplers = self.parse_result.json_dict.get("samplers")
        if not isinstance(sampler, int) or not isinstance(samplers, list):
            return
        if not 0 <= sampler < len(samplers):
            return

        sampler_dict = samplers[sampler]
        if not isinstance(sampler_dict, dict):
            return

        mag_filter = sampler_dict.get("magFilter")
        if isinstance(mag_filter, int):
            texture.sampler.mag_filter = (
                Mtoon1SamplerPropertyGroup.mag_filter_enum.value_to_identifier(
                    mag_filter, Mtoon1SamplerPropertyGroup.MAG_FILTER_DEFAULT.identifier
                )
            )

        min_filter = sampler_dict.get("minFilter")
        if isinstance(min_filter, int):
            texture.sampler.min_filter = (
                Mtoon1SamplerPropertyGroup.min_filter_enum.value_to_identifier(
                    min_filter, Mtoon1SamplerPropertyGroup.MIN_FILTER_DEFAULT.identifier
                )
            )

        wrap_s = sampler_dict.get("wrapS")
        if isinstance(wrap_s, int):
            texture.sampler.wrap_s = (
                Mtoon1SamplerPropertyGroup.wrap_enum.value_to_identifier(
                    wrap_s, Mtoon1SamplerPropertyGroup.WRAP_DEFAULT.identifier
                )
            )

        wrap_t = sampler_dict.get("wrapT")
        if isinstance(wrap_t, int):
            texture.sampler.wrap_t = (
                Mtoon1SamplerPropertyGroup.wrap_enum.value_to_identifier(
                    wrap_t, Mtoon1SamplerPropertyGroup.WRAP_DEFAULT.identifier
                )
            )

    def assign_khr_texture_transform(
        self,
        khr_texture_transform: Mtoon1KhrTextureTransformPropertyGroup,
        khr_texture_transform_dict: dict[str, Json],
    ) -> None:
        offset = convert.float2_or_none(khr_texture_transform_dict.get("offset"))
        if offset:
            khr_texture_transform.offset = offset

        scale = convert.float2_or_none(khr_texture_transform_dict.get("scale"))
        if scale:
            khr_texture_transform.scale = scale

    def assign_texture_info(
        self,
        texture_info: Mtoon1TextureInfoPropertyGroup,
        texture_info_dict: dict[str, Json],
    ) -> None:
        index = texture_info_dict.get("index")
        if isinstance(index, int):
            texture_dicts = self.parse_result.json_dict.get("textures")
            if isinstance(texture_dicts, list) and 0 <= index < len(texture_dicts):
                texture_dict = texture_dicts[index]
                if isinstance(texture_dict, dict):
                    self.assign_texture(texture_info.index, texture_dict)

        extensions_dict = texture_info_dict.get("extensions")
        if not isinstance(extensions_dict, dict):
            return

        khr_texture_transform_dict = extensions_dict.get("KHR_texture_transform")
        if not isinstance(khr_texture_transform_dict, dict):
            return

        self.assign_khr_texture_transform(
            texture_info.extensions.khr_texture_transform,
            khr_texture_transform_dict,
        )

    def make_mtoon1_material(
        self, material_index: int, gltf_dict: dict[str, Json]
    ) -> None:
        extensions_dict = gltf_dict.get("extensions")
        if not isinstance(extensions_dict, dict):
            return

        mtoon_dict = extensions_dict.get("VRMC_materials_mtoon")
        if not isinstance(mtoon_dict, dict):
            return

        material = self.materials.get(material_index)
        if not material:
            name = gltf_dict.get("name")
            if not isinstance(name, str):
                name = "Material"
            material = self.context.blend_data.materials.new(name)
        self.reset_material(material)
        material.use_backface_culling = True

        gltf = get_material_extension(material).mtoon1
        gltf.addon_version = get_addon_version()
        gltf.enabled = True
        mtoon = gltf.extensions.vrmc_materials_mtoon

        pbr_metallic_roughness_dict = gltf_dict.get("pbrMetallicRoughness")
        if isinstance(pbr_metallic_roughness_dict, dict):
            base_color_factor = shader.rgba_or_none(
                pbr_metallic_roughness_dict.get("baseColorFactor")
            )
            if base_color_factor:
                gltf.pbr_metallic_roughness.base_color_factor = base_color_factor

            base_color_texture_dict = pbr_metallic_roughness_dict.get(
                "baseColorTexture"
            )
            if isinstance(base_color_texture_dict, dict):
                self.assign_texture_info(
                    gltf.pbr_metallic_roughness.base_color_texture,
                    base_color_texture_dict,
                )

        alpha_mode = gltf_dict.get("alphaMode")
        if (
            isinstance(alpha_mode, str)
            and alpha_mode in gltf.alpha_mode_enum.identifiers()
        ):
            gltf.alpha_mode = alpha_mode

        alpha_cutoff = gltf_dict.get("alphaCutoff")
        if isinstance(alpha_cutoff, (float, int)):
            gltf.alpha_cutoff = float(alpha_cutoff)

        double_sided = gltf_dict.get("doubleSided")
        if isinstance(double_sided, bool):
            gltf.double_sided = double_sided

        normal_texture_dict = gltf_dict.get("normalTexture")
        if isinstance(normal_texture_dict, dict):
            self.assign_texture_info(
                gltf.normal_texture,
                normal_texture_dict,
            )
            normal_texture_scale = normal_texture_dict.get("scale")
            if isinstance(normal_texture_scale, (float, int)):
                gltf.normal_texture.scale = float(normal_texture_scale)

        emissive_factor = shader.rgb_or_none(gltf_dict.get("emissiveFactor"))
        if emissive_factor:
            gltf.emissive_factor = emissive_factor

        emissive_texture_dict = gltf_dict.get("emissiveTexture")
        if isinstance(emissive_texture_dict, dict):
            self.assign_texture_info(
                gltf.emissive_texture,
                emissive_texture_dict,
            )

        emissive_strength_dict = extensions_dict.get("KHR_materials_emissive_strength")
        if isinstance(emissive_strength_dict, dict):
            emissive_strength = convert.float_or_none(
                emissive_strength_dict.get("emissiveStrength")
            )
            if emissive_strength is not None:
                gltf.extensions.khr_materials_emissive_strength.emissive_strength = (
                    emissive_strength
                )

        shade_color_factor = shader.rgb_or_none(mtoon_dict.get("shadeColorFactor"))
        if shade_color_factor:
            mtoon.shade_color_factor = shade_color_factor

        shade_multiply_texture_dict = mtoon_dict.get("shadeMultiplyTexture")
        if isinstance(shade_multiply_texture_dict, dict):
            self.assign_texture_info(
                mtoon.shade_multiply_texture,
                shade_multiply_texture_dict,
            )

        transparent_with_z_write = mtoon_dict.get("transparentWithZWrite")
        if isinstance(transparent_with_z_write, bool):
            mtoon.transparent_with_z_write = transparent_with_z_write

        render_queue_offset_number = mtoon_dict.get("renderQueueOffsetNumber")
        if isinstance(render_queue_offset_number, (float, int)):
            mtoon.render_queue_offset_number = max(
                -9, min(9, int(render_queue_offset_number))
            )

        shading_shift_factor = mtoon_dict.get("shadingShiftFactor")
        if isinstance(shading_shift_factor, (float, int)):
            mtoon.shading_shift_factor = float(shading_shift_factor)

        shading_shift_texture_dict = mtoon_dict.get("shadingShiftTexture")
        if isinstance(shading_shift_texture_dict, dict):
            self.assign_texture_info(
                mtoon.shading_shift_texture,
                shading_shift_texture_dict,
            )
            shading_shift_texture_scale = shading_shift_texture_dict.get("scale")
            if isinstance(shading_shift_texture_scale, (float, int)):
                mtoon.shading_shift_texture.scale = float(shading_shift_texture_scale)

        shading_toony_factor = mtoon_dict.get("shadingToonyFactor")
        if isinstance(shading_toony_factor, (float, int)):
            mtoon.shading_toony_factor = float(shading_toony_factor)

        gi_equalization_factor = mtoon_dict.get("giEqualizationFactor")
        if isinstance(gi_equalization_factor, (float, int)):
            mtoon.gi_equalization_factor = float(gi_equalization_factor)

        matcap_factor = shader.rgb_or_none(mtoon_dict.get("matcapFactor"))
        if matcap_factor:
            mtoon.matcap_factor = matcap_factor

        matcap_texture_dict = mtoon_dict.get("matcapTexture")
        if isinstance(matcap_texture_dict, dict):
            self.assign_texture_info(
                mtoon.matcap_texture,
                matcap_texture_dict,
            )

        parametric_rim_color_factor = shader.rgb_or_none(
            mtoon_dict.get("parametricRimColorFactor")
        )
        if parametric_rim_color_factor:
            mtoon.parametric_rim_color_factor = parametric_rim_color_factor

        parametric_rim_fresnel_power_factor = mtoon_dict.get(
            "parametricRimFresnelPowerFactor"
        )
        if isinstance(parametric_rim_fresnel_power_factor, (float, int)):
            mtoon.parametric_rim_fresnel_power_factor = float(
                parametric_rim_fresnel_power_factor
            )

        parametric_rim_lift_factor = mtoon_dict.get("parametricRimLiftFactor")
        if isinstance(parametric_rim_lift_factor, (float, int)):
            mtoon.parametric_rim_lift_factor = float(parametric_rim_lift_factor)

        rim_multiply_texture_dict = mtoon_dict.get("rimMultiplyTexture")
        if isinstance(rim_multiply_texture_dict, dict):
            self.assign_texture_info(
                mtoon.rim_multiply_texture,
                rim_multiply_texture_dict,
            )

        rim_lighting_mix_factor = mtoon_dict.get("rimLightingMixFactor")
        if isinstance(rim_lighting_mix_factor, (float, int)):
            mtoon.rim_lighting_mix_factor = float(rim_lighting_mix_factor)

        mtoon.enable_outline_preview = get_preferences(
            self.context
        ).enable_mtoon_outline_preview

        outline_width_mode = mtoon_dict.get("outlineWidthMode")
        if outline_width_mode in mtoon.outline_width_mode_enum.identifiers():
            mtoon.outline_width_mode = outline_width_mode

        outline_width_factor = mtoon_dict.get("outlineWidthFactor")
        if isinstance(outline_width_factor, (float, int)):
            mtoon.outline_width_factor = float(outline_width_factor)

        outline_width_multiply_texture_dict = mtoon_dict.get(
            "outlineWidthMultiplyTexture"
        )
        if isinstance(outline_width_multiply_texture_dict, dict):
            self.assign_texture_info(
                mtoon.outline_width_multiply_texture,
                outline_width_multiply_texture_dict,
            )

        outline_color_factor = shader.rgb_or_none(mtoon_dict.get("outlineColorFactor"))
        if outline_color_factor:
            mtoon.outline_color_factor = outline_color_factor

        outline_lighting_mix_factor = mtoon_dict.get("outlineLightingMixFactor")
        if isinstance(outline_lighting_mix_factor, (float, int)):
            mtoon.outline_lighting_mix_factor = float(outline_lighting_mix_factor)

        uv_animation_mask_texture_dict = mtoon_dict.get("uvAnimationMaskTexture")
        if isinstance(uv_animation_mask_texture_dict, dict):
            self.assign_texture_info(
                mtoon.uv_animation_mask_texture,
                uv_animation_mask_texture_dict,
            )

        uv_animation_rotation_speed_factor = mtoon_dict.get(
            "uvAnimationRotationSpeedFactor"
        )
        if isinstance(uv_animation_rotation_speed_factor, (float, int)):
            mtoon.uv_animation_rotation_speed_factor = float(
                uv_animation_rotation_speed_factor
            )

        uv_animation_scroll_x_speed_factor = mtoon_dict.get(
            "uvAnimationScrollXSpeedFactor"
        )
        if isinstance(uv_animation_scroll_x_speed_factor, (float, int)):
            mtoon.uv_animation_scroll_x_speed_factor = float(
                uv_animation_scroll_x_speed_factor
            )

        uv_animation_scroll_y_speed_factor = mtoon_dict.get(
            "uvAnimationScrollYSpeedFactor"
        )
        if isinstance(uv_animation_scroll_y_speed_factor, (float, int)):
            mtoon.uv_animation_scroll_y_speed_factor = float(
                uv_animation_scroll_y_speed_factor
            )

    def load_materials(self, progress: PartialProgress) -> None:
        material_dicts = self.parse_result.json_dict.get("materials")
        if not isinstance(material_dicts, list):
            progress.update(1)
            return
        for index, material_dict in enumerate(material_dicts):
            if isinstance(material_dict, dict):
                self.make_mtoon1_material(index, material_dict)
            progress.update(float(index) / len(material_dicts))
        progress.update(1)

    def find_vrm1_bone_node_indices(self) -> list[int]:
        result: list[int] = []

        vrm1_dict = self.parse_result.vrm1_extension_dict
        if not isinstance(vrm1_dict, dict):
            return result

        humanoid_dict = vrm1_dict.get("humanoid")
        if not isinstance(humanoid_dict, dict):
            return result

        human_bones_dict = humanoid_dict.get("humanBones")
        if not isinstance(human_bones_dict, dict):
            return result

        for human_bone_dict in human_bones_dict.values():
            if not isinstance(human_bone_dict, dict):
                continue
            node_index = human_bone_dict.get("node")
            if isinstance(node_index, int):
                result.append(node_index)

        return list(dict.fromkeys(result))  # Remove duplicates

    def find_spring_bone1_bone_node_indices(self) -> list[int]:
        result: list[int] = []

        extensions_dict = self.parse_result.json_dict.get("extensions")
        if not isinstance(extensions_dict, dict):
            return result

        spring_bone1_dict = extensions_dict.get("VRMC_springBone")
        if not isinstance(spring_bone1_dict, dict):
            return result

        collider_dicts = spring_bone1_dict.get("colliders")
        if isinstance(collider_dicts, list):
            for collider_dict in collider_dicts:
                if not isinstance(collider_dict, dict):
                    continue

                node_index = collider_dict.get("node")
                if isinstance(node_index, int):
                    result.append(node_index)

        spring_dicts = spring_bone1_dict.get("springs")
        if isinstance(spring_dicts, list):
            for spring_dict in spring_dicts:
                if not isinstance(spring_dict, dict):
                    continue

                center_index = spring_dict.get("center")
                if isinstance(center_index, int):
                    result.append(center_index)

                joint_dicts = spring_dict.get("joints")
                if not isinstance(joint_dicts, list):
                    continue

                for joint_dict in joint_dicts:
                    if not isinstance(joint_dict, dict):
                        continue
                    node_index = joint_dict.get("node")
                    if isinstance(node_index, int):
                        result.append(node_index)

        return list(dict.fromkeys(result))  # Remove duplicates

    def find_vrm_bone_node_indices(self) -> list[int]:
        # TODO: SkinnedMeshRenderer root <=> skin.skeleton???
        return list(
            dict.fromkeys(  # Remove duplicates
                self.find_vrm1_bone_node_indices()
                + self.find_spring_bone1_bone_node_indices()
            )
        )

    def setup_vrm1_humanoid_bones(self) -> None:
        armature = self.armature
        if not armature:
            return
        addon_extension = get_armature_extension(self.armature_data)

        Vrm1HumanBonesPropertyGroup.update_all_node_candidates(
            self.context, self.armature_data.name, force=True
        )

        human_bones = addon_extension.vrm1.humanoid.human_bones
        for name, human_bone in human_bones.human_bone_name_to_human_bone().items():
            if (
                human_bone.node.bone_name
                and human_bone.node.bone_name not in human_bone.node_candidates
            ):
                # Invalid bone structure
                return

            spec = HumanBoneSpecifications.get(name)
            if spec.requirement and not human_bone.node.bone_name:
                # Missing required bones
                return

        with self.save_bone_child_object_transforms(
            self.context, armature
        ) as armature_data:
            bone_name_to_human_bone_name: dict[str, HumanBoneName] = {}
            for (
                human_bone_name,
                human_bone,
            ) in human_bones.human_bone_name_to_human_bone().items():
                if not human_bone.node.bone_name:
                    continue
                bone_name_to_human_bone_name[human_bone.node.bone_name] = (
                    human_bone_name
                )

            # When a bone has multiple children
            # Create a dict to pick the child bone name to point the tail to
            # from that bone name
            bone_name_to_main_child_bone_name: dict[str, str] = {}
            for (
                bone_name,
                human_bone_name,
            ) in bone_name_to_human_bone_name.items():
                # The current algorithm cannot handle
                #
                #   head ---- node ---- leftEye
                #                   \
                #                    -- rightEye
                #
                # well, so we don't process leftEye and rightEye
                if human_bone_name in [HumanBoneName.RIGHT_EYE, HumanBoneName.LEFT_EYE]:
                    continue

                bone = armature_data.edit_bones.get(bone_name)
                if not bone:
                    continue
                last_human_bone_name = human_bone_name
                while True:
                    parent = bone.parent
                    if not parent:
                        break
                    parent_human_bone_name = bone_name_to_human_bone_name.get(
                        parent.name
                    )

                    if parent_human_bone_name in [
                        HumanBoneName.RIGHT_HAND,
                        HumanBoneName.LEFT_HAND,
                    ]:
                        break

                    if (
                        parent_human_bone_name == HumanBoneName.UPPER_CHEST
                        and last_human_bone_name
                        not in [HumanBoneName.HEAD, HumanBoneName.NECK]
                    ):
                        break

                    if (
                        parent_human_bone_name == HumanBoneName.CHEST
                        and last_human_bone_name
                        not in [
                            HumanBoneName.HEAD,
                            HumanBoneName.NECK,
                            HumanBoneName.UPPER_CHEST,
                        ]
                    ):
                        break

                    if (
                        parent_human_bone_name == HumanBoneName.SPINE
                        and last_human_bone_name
                        not in [
                            HumanBoneName.HEAD,
                            HumanBoneName.NECK,
                            HumanBoneName.UPPER_CHEST,
                            HumanBoneName.CHEST,
                        ]
                    ):
                        break

                    if (
                        parent_human_bone_name == HumanBoneName.HIPS
                        and last_human_bone_name != HumanBoneName.SPINE
                    ):
                        break

                    if parent_human_bone_name:
                        last_human_bone_name = parent_human_bone_name

                    bone_name_to_main_child_bone_name[parent.name] = bone.name
                    bone = parent

            # Get human bones and their ancestor bones
            human_bone_tree_bone_names: set[str] = set()
            for bone_name in bone_name_to_human_bone_name:
                bone = armature_data.edit_bones.get(bone_name)
                while bone:
                    human_bone_tree_bone_names.add(bone.name)
                    bone = bone.parent

            bone_name_to_axis_translation: dict[str, str] = {}

            human_bone_tree_bones: list[EditBone] = []
            non_human_bone_tree_bones: list[EditBone] = []
            constraint_node_index_to_source_index: dict[int, int] = {}
            constraint_node_index_groups: list[set[int]] = []
            nodes = self.parse_result.json_dict.get("nodes")
            if not isinstance(nodes, list):
                nodes = []
            for node_index, node_dict in enumerate(nodes):
                if not isinstance(node_dict, dict):
                    continue

                node_extensions_dict = node_dict.get("extensions")
                if not isinstance(node_extensions_dict, dict):
                    continue

                vrmc_node_constraint_dict = node_extensions_dict.get(
                    "VRMC_node_constraint"
                )
                if not isinstance(vrmc_node_constraint_dict, dict):
                    continue

                constraint_dict = vrmc_node_constraint_dict.get("constraint")
                if not isinstance(constraint_dict, dict):
                    continue

                object_or_bone = self.get_object_or_bone_by_node_index(node_index)
                if not object_or_bone:
                    continue

                roll_dict = constraint_dict.get("roll")
                if isinstance(roll_dict, dict):
                    source = roll_dict.get("source")
                    if isinstance(source, int):
                        constraint_node_index_to_source_index[node_index] = source
                        continue

                aim_dict = constraint_dict.get("aim")
                if isinstance(aim_dict, dict):
                    source = aim_dict.get("source")
                    if isinstance(source, int):
                        constraint_node_index_to_source_index[node_index] = source
                        continue

                rotation_dict = constraint_dict.get("rotation")
                if isinstance(rotation_dict, dict):
                    source = rotation_dict.get("source")
                    if isinstance(source, int):
                        constraint_node_index_to_source_index[node_index] = source
                        continue

            node_indices = list(constraint_node_index_to_source_index.keys())
            while node_indices:
                node_index = node_indices.pop()
                source_index = constraint_node_index_to_source_index.get(node_index)
                if not isinstance(source_index, int):
                    continue
                node_indices.append(source_index)
                found = False
                for constraint_node_index_group in constraint_node_index_groups:
                    if node_index in constraint_node_index_group:
                        constraint_node_index_group.add(source_index)
                        found = True
                        break
                    if source_index in constraint_node_index_group:
                        constraint_node_index_group.add(node_index)
                        found = True
                        break

                if not found:
                    constraint_node_index_groups.append({node_index, source_index})

            # When constraints are attached during axis conversion, we want to
            # prioritize human bones and their ancestor bones, so we process
            # them first in depth-first order, then process other bones in
            # depth-first order
            unsorted_bones = [
                bone for bone in armature_data.edit_bones if not bone.parent
            ]
            while unsorted_bones:
                bone = unsorted_bones.pop()
                unsorted_bones.extend(bone.children)
                if bone.name in human_bone_tree_bone_names:
                    human_bone_tree_bones.append(bone)
                else:
                    non_human_bone_tree_bones.append(bone)

            for bone in human_bone_tree_bones + non_human_bone_tree_bones:
                bone_index = next(
                    (i for i, n in self.bone_names.items() if n == bone.name), None
                )
                if isinstance(bone_index, int):
                    group_axis_translation: Optional[str] = None
                    for node_index in next(
                        (g for g in constraint_node_index_groups if bone_index in g),
                        set[int](),
                    ):
                        object_or_bone = self.get_object_or_bone_by_node_index(
                            node_index
                        )
                        if isinstance(object_or_bone, PoseBone):
                            group_axis_translation = bone_name_to_axis_translation.get(
                                object_or_bone.name
                            )
                            if group_axis_translation is not None:
                                break
                    if group_axis_translation is not None:
                        bone.matrix = BoneExtension.translate_axis(
                            bone.matrix,
                            group_axis_translation,
                        )
                        if bone.parent and not bone.children:
                            bone.length = max(
                                bone.parent.length / 2, make_armature.MIN_BONE_LENGTH
                            )
                        bone_name_to_axis_translation[bone.name] = (
                            group_axis_translation
                        )
                        continue

                main_child_bone_name = bone_name_to_main_child_bone_name.get(bone.name)
                target_vector: Optional[Vector] = None
                if main_child_bone_name:
                    main_child = next(
                        bone
                        for bone in bone.children
                        if bone.name == main_child_bone_name
                    )
                    target_translation = (
                        armature.matrix_world @ Matrix.Translation(main_child.head)
                    ).to_translation()
                    base_translation = (
                        armature.matrix_world @ Matrix.Translation(bone.head)
                    ).to_translation()
                    target_vector = target_translation - base_translation
                elif bone.children:
                    target_translation = Vector((0.0, 0.0, 0.0))
                    for child in bone.children:
                        child_translation = (
                            armature.matrix_world @ Matrix.Translation(child.head)
                        ).to_translation()
                        target_translation += child_translation
                    target_translation /= len(bone.children)
                    base_translation = (
                        armature.matrix_world @ Matrix.Translation(bone.head)
                    ).to_translation()
                    target_vector = target_translation - base_translation
                elif not bone.parent:
                    bone_name_to_axis_translation[bone.name] = (
                        BoneExtension.AXIS_TRANSLATION_NONE.identifier
                    )
                    continue
                elif bone_name_to_human_bone_name.get(bone.name) in [
                    HumanBoneName.RIGHT_EYE,
                    HumanBoneName.LEFT_EYE,
                    HumanBoneName.RIGHT_FOOT,
                    HumanBoneName.LEFT_FOOT,
                ]:
                    target_vector = Vector((0, -1, 0))
                else:
                    target_translation = (
                        armature.matrix_world @ Matrix.Translation(bone.head)
                    ).to_translation()
                    base_translation = (
                        armature.matrix_world @ Matrix.Translation(bone.parent.head)
                    ).to_translation()
                    target_vector = target_translation - base_translation

                base_rotation = (armature.matrix_world @ bone.matrix).to_quaternion()

                x_vector = Vector((1, 0, 0))
                x_vector.rotate(base_rotation)
                x_negated_vector = x_vector.copy()
                x_negated_vector.negate()
                y_vector = Vector((0, 1, 0))
                y_vector.rotate(base_rotation)
                y_negated_vector = y_vector.copy()
                y_negated_vector.negate()
                z_vector = Vector((0, 0, 1))
                z_vector.rotate(base_rotation)
                z_negated_vector = z_vector.copy()
                z_negated_vector.negate()

                bone_length_and_axis_translations: list[tuple[float, str]] = [
                    (
                        target_vector.dot(x_vector),
                        BoneExtension.AXIS_TRANSLATION_X_TO_Y.identifier,
                    ),
                    (
                        target_vector.dot(y_vector),
                        BoneExtension.AXIS_TRANSLATION_NONE.identifier,
                    ),
                    (
                        target_vector.dot(z_vector),
                        BoneExtension.AXIS_TRANSLATION_Z_TO_Y.identifier,
                    ),
                    (
                        target_vector.dot(x_negated_vector),
                        BoneExtension.AXIS_TRANSLATION_MINUS_X_TO_Y.identifier,
                    ),
                    (
                        target_vector.dot(y_negated_vector),
                        BoneExtension.AXIS_TRANSLATION_MINUS_Y_TO_Y_AROUND_Z.identifier,
                    ),
                    (
                        target_vector.dot(z_negated_vector),
                        BoneExtension.AXIS_TRANSLATION_MINUS_Z_TO_Y.identifier,
                    ),
                ]
                bone_length, axis_translation = sorted(
                    bone_length_and_axis_translations, reverse=True, key=lambda x: x[0]
                )[0]
                bone.matrix = BoneExtension.translate_axis(
                    bone.matrix,
                    axis_translation,
                )
                if bone.children:
                    bone.length = max(bone_length, make_armature.MIN_BONE_LENGTH)
                elif bone.parent:
                    bone.length = max(
                        bone.parent.length / 2, make_armature.MIN_BONE_LENGTH
                    )
                bone_name_to_axis_translation[bone.name] = axis_translation

            connect_parent_tail_and_child_head_if_very_close_position(armature_data)

            bpy.ops.object.mode_set(mode="OBJECT")
            for bone_name, axis_translation in bone_name_to_axis_translation.items():
                data_bone = armature_data.bones.get(bone_name)
                if not data_bone:
                    continue
                get_bone_extension(
                    data_bone
                ).axis_translation = BoneExtension.reverse_axis_translation(
                    axis_translation
                )

            for node_index in set(constraint_node_index_to_source_index.keys()) | set(
                constraint_node_index_to_source_index.values()
            ):
                object_or_bone = self.get_object_or_bone_by_node_index(node_index)
                if not isinstance(object_or_bone, Object):
                    continue
                for group_node_index in next(
                    (g for g in constraint_node_index_groups if node_index in g),
                    set[int](),
                ):
                    group_object_or_bone = self.get_object_or_bone_by_node_index(
                        group_node_index
                    )
                    if isinstance(group_object_or_bone, PoseBone):
                        self.translate_object_axis(
                            object_or_bone,
                            BoneExtension.reverse_axis_translation(
                                get_bone_extension(
                                    group_object_or_bone.bone
                                ).axis_translation
                            ),
                        )
                        break

    def translate_object_axis(self, obj: Object, axis_translation: str) -> None:
        if axis_translation != BoneExtension.AXIS_TRANSLATION_AUTO.identifier:
            return
        matrix = BoneExtension.translate_axis(obj.matrix_world, axis_translation)
        location, rotation, _ = matrix.decompose()
        matrix = Matrix.Translation(location) @ rotation.to_matrix().to_4x4()
        bpy.ops.object.select_all(action="DESELECT")
        self.context.scene.cursor.matrix = matrix
        obj.select_set(True)
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")

        get_object_extension(
            obj
        ).axis_translation = BoneExtension.reverse_axis_translation(axis_translation)

    def load_gltf_extensions(self) -> None:
        armature = self.armature
        if not armature:
            return
        addon_extension = get_armature_extension(self.armature_data)
        vrm1 = addon_extension.vrm1

        addon_extension.spec_version = addon_extension.SPEC_VERSION_VRM1
        vrm1_extension_dict = self.parse_result.vrm1_extension_dict

        addon_extension.addon_version = get_addon_version()

        textblock = self.context.blend_data.texts.new(name="vrm.json")
        textblock.write(json.dumps(self.parse_result.json_dict, indent=4))

        self.load_vrm1_meta(vrm1.meta, vrm1_extension_dict.get("meta"))
        self.load_vrm1_humanoid(vrm1.humanoid, vrm1_extension_dict.get("humanoid"))
        self.setup_vrm1_humanoid_bones()
        self.load_vrm1_first_person(
            vrm1.first_person, vrm1_extension_dict.get("firstPerson")
        )
        self.load_vrm1_look_at(vrm1.look_at, vrm1_extension_dict.get("lookAt"))
        self.load_vrm1_expressions(
            vrm1.expressions, vrm1_extension_dict.get("expressions")
        )

        extensions_dict = self.parse_result.json_dict.get("extensions")
        if isinstance(extensions_dict, dict):
            self.load_spring_bone1(
                addon_extension.spring_bone1, extensions_dict.get("VRMC_springBone")
            )

        self.load_node_constraint1()
        migration.migrate(self.context, armature.name)

    def load_vrm1_meta(self, meta: Vrm1MetaPropertyGroup, meta_dict: Json) -> None:
        if not isinstance(meta_dict, dict):
            return

        name = meta_dict.get("name")
        if name is not None:
            meta.vrm_name = str(name)

        version = meta_dict.get("version")
        if version is not None:
            meta.version = str(version)

        authors = meta_dict.get("authors")
        if isinstance(authors, list):
            for author in authors:
                if author is not None:
                    meta.authors.add().value = str(author)

        copyright_information = meta_dict.get("copyrightInformation")
        if copyright_information is not None:
            meta.copyright_information = str(copyright_information)

        contact_information = meta_dict.get("contactInformation")
        if contact_information is not None:
            meta.contact_information = str(contact_information)

        references = meta_dict.get("references")
        if isinstance(references, list):
            for reference in references:
                if reference is not None:
                    meta.references.add().value = str(reference)

        third_party_licenses = meta_dict.get("thirdPartyLicenses")
        if third_party_licenses is not None:
            meta.third_party_licenses = str(third_party_licenses)

        thumbnail_image_index = meta_dict.get("thumbnailImage")
        if isinstance(thumbnail_image_index, int):
            thumbnail_image = self.images.get(thumbnail_image_index)
            if thumbnail_image:
                meta.thumbnail_image = thumbnail_image

        avatar_permission = meta_dict.get("avatarPermission")
        if (
            isinstance(avatar_permission, str)
            and avatar_permission
            in Vrm1MetaPropertyGroup.avatar_permission_enum.identifiers()
        ):
            meta.avatar_permission = avatar_permission

        meta.allow_excessively_violent_usage = bool(
            meta_dict.get("allowExcessivelyViolentUsage")
        )

        meta.allow_excessively_sexual_usage = bool(
            meta_dict.get("allowExcessivelySexualUsage")
        )

        commercial_usage = meta_dict.get("commercialUsage")
        if (
            isinstance(commercial_usage, str)
            and commercial_usage
            in Vrm1MetaPropertyGroup.commercial_usage_enum.identifiers()
        ):
            meta.commercial_usage = commercial_usage

        meta.allow_political_or_religious_usage = bool(
            meta_dict.get("allowPoliticalOrReligiousUsage")
        )

        meta.allow_antisocial_or_hate_usage = bool(
            meta_dict.get("allowAntisocialOrHateUsage")
        )

        credit_notation = meta_dict.get("creditNotation")
        if (
            isinstance(credit_notation, str)
            and credit_notation
            in Vrm1MetaPropertyGroup.credit_notation_enum.identifiers()
        ):
            meta.credit_notation = credit_notation

        meta.allow_redistribution = bool(meta_dict.get("allowRedistribution"))

        modification = meta_dict.get("modification")
        if (
            isinstance(modification, str)
            and modification in Vrm1MetaPropertyGroup.modification_enum.identifiers()
        ):
            meta.modification = modification

        other_license_url = meta_dict.get("otherLicenseUrl")
        if other_license_url is not None:
            meta.other_license_url = str(other_license_url)

    def load_vrm1_humanoid(
        self, humanoid: Vrm1HumanoidPropertyGroup, humanoid_dict: Json
    ) -> None:
        if not isinstance(humanoid_dict, dict):
            return

        human_bones_dict = humanoid_dict.get("humanBones")
        if not isinstance(human_bones_dict, dict):
            return

        human_bone_name_to_human_bone = (
            humanoid.human_bones.human_bone_name_to_human_bone()
        )

        assigned_bone_names: list[str] = []
        for human_bone_name in [
            human_bone.name
            for human_bone in vrm1_human_bone.HumanBoneSpecifications.all_human_bones
        ]:
            human_bone_dict = human_bones_dict.get(human_bone_name.value)
            if not isinstance(human_bone_dict, dict):
                continue
            node_index = human_bone_dict.get("node")
            if not isinstance(node_index, int):
                continue
            bone_name = self.bone_names.get(node_index)
            if not isinstance(bone_name, str) or bone_name in assigned_bone_names:
                continue
            human_bone_name_to_human_bone[human_bone_name].node.bone_name = bone_name
            assigned_bone_names.append(bone_name)

    def load_vrm1_first_person(
        self,
        first_person: Vrm1FirstPersonPropertyGroup,
        first_person_dict: Json,
    ) -> None:
        if not isinstance(first_person_dict, dict):
            return

        mesh_annotation_dicts = first_person_dict.get("meshAnnotations")
        if not isinstance(mesh_annotation_dicts, list):
            mesh_annotation_dicts = []

        for mesh_annotation_dict in mesh_annotation_dicts:
            mesh_annotation = first_person.mesh_annotations.add()
            if not isinstance(mesh_annotation_dict, dict):
                continue

            node = mesh_annotation_dict.get("node")
            if isinstance(node, int):
                mesh_object_name = self.mesh_object_names.get(node)
                if isinstance(mesh_object_name, str):
                    mesh_annotation.node.mesh_object_name = mesh_object_name

            type_ = mesh_annotation_dict.get("type")
            if type_ in mesh_annotation.type_enum.identifiers():
                mesh_annotation.type = type_

    def load_vrm1_look_at(
        self,
        look_at: Vrm1LookAtPropertyGroup,
        look_at_dict: Json,
    ) -> None:
        if not isinstance(look_at_dict, dict):
            return
        armature = self.armature
        if armature is None:
            return
        offset_from_head_bone = Vector(
            convert.vrm_json_array_to_float_vector(
                look_at_dict.get("offsetFromHeadBone"), [0, 0, 0]
            )
        )

        humanoid = get_armature_extension(self.armature_data).vrm1.humanoid
        head_bone_name = humanoid.human_bones.head.node.bone_name
        head_bone = self.armature_data.bones.get(head_bone_name)
        if head_bone:
            offset_from_head_bone = (
                offset_from_head_bone
                @ BoneExtension.translate_axis(
                    Matrix(),
                    BoneExtension.reverse_axis_translation(
                        get_bone_extension(head_bone).axis_translation
                    ),
                )
            )

        look_at.offset_from_head_bone = offset_from_head_bone
        type_ = look_at_dict.get("type")
        if type_ in look_at.type_enum.identifiers():
            look_at.type = type_

        for range_map, range_map_dict in [
            (
                look_at.range_map_horizontal_inner,
                look_at_dict.get("rangeMapHorizontalInner"),
            ),
            (
                look_at.range_map_horizontal_outer,
                look_at_dict.get("rangeMapHorizontalOuter"),
            ),
            (
                look_at.range_map_vertical_down,
                look_at_dict.get("rangeMapVerticalDown"),
            ),
            (
                look_at.range_map_vertical_up,
                look_at_dict.get("rangeMapVerticalUp"),
            ),
        ]:
            if not isinstance(range_map_dict, dict):
                continue

            input_max_value = range_map_dict.get("inputMaxValue")
            if isinstance(input_max_value, (float, int)):
                range_map.input_max_value = float(input_max_value)

            output_scale = range_map_dict.get("outputScale")
            if isinstance(output_scale, (float, int)):
                range_map.output_scale = float(output_scale)

    def load_vrm1_expression(
        self,
        expression: Vrm1ExpressionPropertyGroup,
        expression_dict: Json,
    ) -> None:
        if not isinstance(expression_dict, dict):
            return

        morph_target_bind_dicts = expression_dict.get("morphTargetBinds")
        if not isinstance(morph_target_bind_dicts, list):
            morph_target_bind_dicts = []

        for morph_target_bind_dict in morph_target_bind_dicts:
            if not isinstance(morph_target_bind_dict, dict):
                continue

            morph_target_bind = expression.morph_target_binds.add()

            weight = convert.float_or(morph_target_bind_dict.get("weight"), 0.0)

            morph_target_bind.weight = weight

            node_index = morph_target_bind_dict.get("node")
            if not isinstance(node_index, int):
                continue
            node_dicts = self.parse_result.json_dict.get("nodes")
            if not isinstance(node_dicts, list) or not (
                0 <= node_index < len(node_dicts)
            ):
                continue
            node_dict = node_dicts[node_index]
            if not isinstance(node_dict, dict):
                continue
            mesh_index = node_dict.get("mesh")
            if not isinstance(mesh_index, int):
                continue
            mesh_obj = self.meshes.get(mesh_index)
            if not mesh_obj:
                continue

            morph_target_bind.node.mesh_object_name = mesh_obj.name
            index = morph_target_bind_dict.get("index")
            if not isinstance(index, int):
                continue
            mesh_data = mesh_obj.data
            if not isinstance(mesh_data, Mesh):
                continue
            shape_keys = mesh_data.shape_keys
            if not shape_keys:
                continue
            key_blocks = shape_keys.key_blocks
            if 1 <= (index + 1) < len(key_blocks):
                morph_target_bind.index = key_blocks[index + 1].name

        material_color_bind_dicts = expression_dict.get("materialColorBinds")
        if not isinstance(material_color_bind_dicts, list):
            material_color_bind_dicts = []

        for material_color_bind_dict in material_color_bind_dicts:
            material_color_bind = expression.material_color_binds.add()

            if not isinstance(material_color_bind_dict, dict):
                continue

            material_index = material_color_bind_dict.get("material")
            if isinstance(material_index, int):
                material = self.materials.get(material_index)
                if material:
                    material_color_bind.material = material

            type_ = material_color_bind_dict.get("type")
            if type_ in Vrm1MaterialColorBindPropertyGroup.type_enum.identifiers():
                material_color_bind.type = type_

            target_value = material_color_bind_dict.get("targetValue")
            if not isinstance(target_value, list):
                target_value = []
            target_value = [
                float(v) if isinstance(v, (float, int)) else 0.0 for v in target_value
            ]
            while len(target_value) < 4:
                target_value.append(0.0)
            material_color_bind.target_value = target_value[:4]

        texture_transform_bind_dicts = expression_dict.get("textureTransformBinds")
        if not isinstance(texture_transform_bind_dicts, list):
            texture_transform_bind_dicts = []
        for texture_transform_bind_dict in texture_transform_bind_dicts:
            texture_transform_bind = expression.texture_transform_binds.add()

            if not isinstance(texture_transform_bind_dict, dict):
                continue

            material_index = texture_transform_bind_dict.get("material")
            if isinstance(material_index, int):
                material = self.materials.get(material_index)
                if material:
                    texture_transform_bind.material = material

            texture_transform_bind.scale = convert.vrm_json_array_to_float_vector(
                texture_transform_bind_dict.get("scale"), [1, 1]
            )

            texture_transform_bind.offset = convert.vrm_json_array_to_float_vector(
                texture_transform_bind_dict.get("offset"), [0, 0]
            )

        is_binary = expression_dict.get("isBinary")
        if isinstance(is_binary, bool):
            expression.is_binary = is_binary

        override_blink = expression_dict.get("overrideBlink")
        if (
            isinstance(override_blink, str)
            and override_blink
            in Vrm1ExpressionPropertyGroup.expression_override_type_enum.identifiers()
        ):
            expression.override_blink = override_blink

        override_look_at = expression_dict.get("overrideLookAt")
        if (
            isinstance(override_look_at, str)
            and override_look_at
            in Vrm1ExpressionPropertyGroup.expression_override_type_enum.identifiers()
        ):
            expression.override_look_at = override_look_at

        override_mouth = expression_dict.get("overrideMouth")
        if (
            isinstance(override_mouth, str)
            and override_mouth
            in Vrm1ExpressionPropertyGroup.expression_override_type_enum.identifiers()
        ):
            expression.override_mouth = override_mouth

    def load_vrm1_expressions(
        self,
        expressions: Vrm1ExpressionsPropertyGroup,
        expressions_dict: Json,
    ) -> None:
        if not isinstance(expressions_dict, dict):
            return

        preset_dict = expressions_dict.get("preset")
        if isinstance(preset_dict, dict):
            for (
                preset_name,
                expression,
            ) in expressions.preset.name_to_expression_dict().items():
                self.load_vrm1_expression(expression, preset_dict.get(preset_name))

        custom_dict = expressions_dict.get("custom")
        if isinstance(custom_dict, dict):
            for custom_name, expression_dict in custom_dict.items():
                expression = expressions.custom.add()
                expression.custom_name = custom_name
                self.load_vrm1_expression(expression, expression_dict)

    def load_spring_bone1_collider(
        self,
        collider: SpringBone1ColliderPropertyGroup,
        collider_dict: dict[str, Json],
    ) -> None:
        bone: Optional[Bone] = None
        node_index = collider_dict.get("node")
        if isinstance(node_index, int):
            bone_name = self.bone_names.get(node_index)
            if isinstance(bone_name, str):
                collider.node.bone_name = bone_name
                collider_bpy_object = collider.bpy_object
                if collider_bpy_object:
                    collider_bpy_object.name = f"{bone_name} Collider"
                bone = self.armature_data.bones.get(collider.node.bone_name)

        shape_dict = collider_dict.get("shape")
        if not isinstance(shape_dict, dict):
            collider.shape.sphere.radius = 0.0001
            collider.shape.sphere.offset = (0, 0, -10000)
            return

        shape = collider.shape

        sphere_dict = shape_dict.get("sphere")
        capsule_dict = shape_dict.get("capsule")
        if isinstance(sphere_dict, dict):
            collider.shape_type = collider.SHAPE_TYPE_SPHERE.identifier
            offset = Vector(
                convert.vrm_json_array_to_float_vector(
                    sphere_dict.get("offset"), [0, 0, 0]
                )
            )
            if bone:
                axis_translation = get_bone_extension(bone).axis_translation
                offset = Vector(offset) @ BoneExtension.translate_axis(
                    Matrix(),
                    BoneExtension.reverse_axis_translation(axis_translation),
                )
            shape.sphere.offset = offset
            radius = sphere_dict.get("radius")
            if isinstance(radius, (float, int)):
                shape.sphere.radius = float(radius)
        elif isinstance(capsule_dict, dict):
            collider.shape_type = collider.SHAPE_TYPE_CAPSULE.identifier

            offset = Vector(
                convert.vrm_json_array_to_float_vector(
                    capsule_dict.get("offset"), [0, 0, 0]
                )
            )
            if bone:
                axis_translation = get_bone_extension(bone).axis_translation
                offset = Vector(offset) @ BoneExtension.translate_axis(
                    Matrix(),
                    BoneExtension.reverse_axis_translation(axis_translation),
                )
            shape.capsule.offset = offset

            radius = capsule_dict.get("radius")
            if isinstance(radius, (float, int)):
                shape.capsule.radius = float(radius)

            tail = Vector(
                convert.vrm_json_array_to_float_vector(
                    capsule_dict.get("tail"), [0, 0, 0]
                )
            )
            if bone:
                axis_translation = get_bone_extension(bone).axis_translation
                tail = Vector(tail) @ BoneExtension.translate_axis(
                    Matrix(),
                    BoneExtension.reverse_axis_translation(axis_translation),
                )
            shape.capsule.tail = tail

        extensions_dict = collider_dict.get("extensions")
        if not isinstance(extensions_dict, dict):
            return
        extended_collider_dict = extensions_dict.get(
            "VRMC_springBone_extended_collider"
        )
        if not isinstance(extended_collider_dict, dict):
            return
        extended_shape_dict = extended_collider_dict.get("shape")
        if not isinstance(extended_shape_dict, dict):
            return

        extended_collider = collider.extensions.vrmc_spring_bone_extended_collider
        extended_shape = extended_collider.shape
        extended_sphere_dict = extended_shape_dict.get("sphere")
        extended_capsule_dict = extended_shape_dict.get("capsule")
        extended_plane_dict = extended_shape_dict.get("plane")
        if isinstance(extended_sphere_dict, dict):
            extended_collider.shape_type = (
                extended_collider.SHAPE_TYPE_EXTENDED_SPHERE.identifier
            )
            offset = Vector(
                convert.vrm_json_array_to_float_vector(
                    extended_sphere_dict.get("offset"), [0, 0, 0]
                )
            )
            if bone:
                axis_translation = get_bone_extension(bone).axis_translation
                offset = Vector(offset) @ BoneExtension.translate_axis(
                    Matrix(),
                    BoneExtension.reverse_axis_translation(axis_translation),
                )
            extended_shape.sphere.offset = offset
            radius = extended_sphere_dict.get("radius")
            if isinstance(radius, (float, int)):
                extended_shape.sphere.radius = float(radius)

            inside = extended_sphere_dict.get("inside")
            if isinstance(inside, bool):
                extended_shape.sphere.inside = inside

        elif isinstance(extended_capsule_dict, dict):
            extended_collider.shape_type = (
                extended_collider.SHAPE_TYPE_EXTENDED_CAPSULE.identifier
            )
            offset = Vector(
                convert.vrm_json_array_to_float_vector(
                    extended_capsule_dict.get("offset"), [0, 0, 0]
                )
            )
            if bone:
                axis_translation = get_bone_extension(bone).axis_translation
                offset = Vector(offset) @ BoneExtension.translate_axis(
                    Matrix(),
                    BoneExtension.reverse_axis_translation(axis_translation),
                )
            extended_shape.capsule.offset = offset

            radius = extended_capsule_dict.get("radius")
            if isinstance(radius, (float, int)):
                extended_shape.capsule.radius = float(radius)

            tail = Vector(
                convert.vrm_json_array_to_float_vector(
                    extended_capsule_dict.get("tail"), [0, 0, 0]
                )
            )
            if bone:
                axis_translation = get_bone_extension(bone).axis_translation
                tail = Vector(tail) @ BoneExtension.translate_axis(
                    Matrix(),
                    BoneExtension.reverse_axis_translation(axis_translation),
                )
            extended_shape.capsule.tail = tail

            inside = extended_capsule_dict.get("inside")
            if isinstance(inside, bool):
                extended_shape.capsule.inside = inside

        elif isinstance(extended_plane_dict, dict):
            extended_collider.shape_type = (
                extended_collider.SHAPE_TYPE_EXTENDED_PLANE.identifier
            )

            offset = Vector(
                convert.vrm_json_array_to_float_vector(
                    extended_plane_dict.get("offset"), [0, 0, 0]
                )
            )
            if bone:
                axis_translation = get_bone_extension(bone).axis_translation
                offset = Vector(offset) @ BoneExtension.translate_axis(
                    Matrix(),
                    BoneExtension.reverse_axis_translation(axis_translation),
                )
            extended_shape.plane.offset = offset

            normal = Vector(
                convert.vrm_json_array_to_float_vector(
                    extended_plane_dict.get("normal"), [0, 0, 0]
                )
            )
            if bone:
                axis_translation = get_bone_extension(bone).axis_translation
                normal = Vector(normal) @ BoneExtension.translate_axis(
                    Matrix(),
                    BoneExtension.reverse_axis_translation(axis_translation),
                )
            extended_shape.plane.normal = normal

            collider_bpy_object = collider.bpy_object
            if collider_bpy_object:
                # Override the fallback collider values with fixed values when loading
                collider_bpy_object.empty_display_size = 0.125

        else:
            return

        extended_collider.enabled = True
        extended_collider.automatic_fallback_generation = False

    def load_spring_bone1_colliders(
        self,
        spring_bone: SpringBone1SpringBonePropertyGroup,
        spring_bone_dict: dict[str, Json],
        armature: Object,
    ) -> None:
        collider_dicts = spring_bone_dict.get("colliders")
        if not isinstance(collider_dicts, list):
            collider_dicts = []

        for collider_dict in collider_dicts:
            # Since the reference from ColliderGroup to Collider is by index,
            # create empty data even if the contents of collider_dict are invalid
            if ops.vrm.add_spring_bone1_collider(
                armature_object_name=armature.name
            ) != {"FINISHED"}:
                message = f'Failed to add spring bone 1.0 collider to "{armature.name}"'
                raise ValueError(message)

            collider = spring_bone.colliders[-1]

            if not isinstance(collider_dict, dict):
                collider.shape.sphere.radius = 0.0001
                collider.shape.sphere.offset = (0, 0, -10000)
                continue

            self.load_spring_bone1_collider(collider, collider_dict)

        for collider in spring_bone.colliders:
            collider.reset_bpy_object(self.context, armature)

        collider_object_names: list[str] = []
        if spring_bone.colliders:
            colliders_collection = self.context.blend_data.collections.new("Colliders")
            self.context.scene.collection.children.link(colliders_collection)
            for collider in spring_bone.colliders:
                collider_bpy_object = collider.bpy_object
                if not collider_bpy_object:
                    continue
                colliders_collection.objects.link(collider_bpy_object)
                collider_object_names.append(collider_bpy_object.name)
                if collider_bpy_object.name in self.context.scene.collection.objects:
                    self.context.scene.collection.objects.unlink(collider_bpy_object)
                for child in collider_bpy_object.children:
                    collider_object_names.append(child.name)
                    colliders_collection.objects.link(child)
                    if child.name in self.context.scene.collection.objects:
                        self.context.scene.collection.objects.unlink(child)

        spring_bone.active_collider_index = 0

        if collider_object_names:
            imported_object_names = self.imported_object_names
            if imported_object_names is None:
                imported_object_names = []
                self.imported_object_names = imported_object_names
            imported_object_names.extend(collider_object_names)

    def load_spring_bone1_collider_groups(
        self,
        spring_bone: SpringBone1SpringBonePropertyGroup,
        spring_bone_dict: dict[str, Json],
        armature_object_name: str,
    ) -> None:
        collider_group_dicts = spring_bone_dict.get("colliderGroups")
        if not isinstance(collider_group_dicts, list):
            collider_group_dicts = []

        for collider_group_index, collider_group_dict in enumerate(
            collider_group_dicts
        ):
            # Since the reference from Spring to ColliderGroup is by index,
            # create empty data even if the contents of collider_group_dict are invalid
            if ops.vrm.add_spring_bone1_collider_group(
                armature_object_name=armature_object_name
            ) != {"FINISHED"}:
                message = (
                    "Failed to add spring bone 1.0 collider group"
                    + f" to {armature_object_name}"
                )
                raise ValueError(message)

            if not isinstance(collider_group_dict, dict):
                continue

            collider_group = spring_bone.collider_groups[-1]

            name = collider_group_dict.get("name")
            if isinstance(name, str):
                collider_group.vrm_name = name

            collider_indices = collider_group_dict.get("colliders")
            if not isinstance(collider_indices, list):
                continue

            for collider_index in collider_indices:
                if ops.vrm.add_spring_bone1_collider_group_collider(
                    armature_object_name=armature_object_name,
                    collider_group_index=collider_group_index,
                ) != {"FINISHED"}:
                    raise ValueError(
                        "Failed to assign spring bone 1.0 collider to collider group "
                        + f"{collider_group_index} in {armature_object_name}"
                    )
                if not isinstance(collider_index, int):
                    continue
                if not 0 <= collider_index < len(spring_bone.colliders):
                    continue
                collider = spring_bone.colliders[collider_index]
                if not collider:
                    continue
                collider_reference = collider_group.colliders[-1]
                collider_reference.collider_name = collider.name
            collider_group.active_collider_index = 0
        spring_bone.active_collider_group_index = 0

    def load_spring_bone1_springs(
        self,
        spring_bone: SpringBone1SpringBonePropertyGroup,
        spring_bone_dict: dict[str, Json],
        armature_object_name: str,
    ) -> None:
        spring_dicts = spring_bone_dict.get("springs")
        if not isinstance(spring_dicts, list):
            spring_dicts = []

        for spring_dict in spring_dicts:
            if ops.vrm.add_spring_bone1_spring(
                armature_object_name=armature_object_name
            ) != {"FINISHED"} or not isinstance(spring_dict, dict):
                continue

            spring = spring_bone.springs[-1]

            name = spring_dict.get("name")
            if isinstance(name, str):
                spring.vrm_name = name

            center_index = spring_dict.get("center")
            if isinstance(center_index, int):
                bone_name = self.bone_names.get(center_index)
                if bone_name:
                    spring.center.bone_name = bone_name

            joint_dicts = spring_dict.get("joints")
            if not isinstance(joint_dicts, list):
                joint_dicts = []
            for joint_dict in joint_dicts:
                if ops.vrm.add_spring_bone1_spring_joint(
                    armature_object_name=armature_object_name,
                    spring_index=len(spring_bone.springs) - 1,
                ) != {"FINISHED"}:
                    continue
                if not isinstance(joint_dict, dict):
                    continue

                joint = spring.joints[-1]

                node_index = joint_dict.get("node")
                if isinstance(node_index, int):
                    bone_name = self.bone_names.get(node_index)
                    if bone_name:
                        joint.node.bone_name = bone_name

                hit_radius = convert.float_or_none(joint_dict.get("hitRadius"))
                if hit_radius is not None:
                    joint.hit_radius = hit_radius

                stiffness = convert.float_or_none(joint_dict.get("stiffness"))
                if stiffness is not None:
                    joint.stiffness = stiffness

                gravity_power = convert.float_or_none(joint_dict.get("gravityPower"))
                if gravity_power is not None:
                    joint.gravity_power = gravity_power

                gltf_axis_gravity_dir = convert.vrm_json_array_to_float_vector(
                    joint_dict.get("gravityDir"),
                    [0.0, -1.0, 0.0],
                )
                joint.gravity_dir = [
                    gltf_axis_gravity_dir[0],
                    -gltf_axis_gravity_dir[2],
                    gltf_axis_gravity_dir[1],
                ]

                drag_force = convert.float_or_none(joint_dict.get("dragForce"))
                if drag_force is not None:
                    joint.drag_force = drag_force
            spring.active_joint_index = 0

            collider_group_indices = spring_dict.get("colliderGroups")
            if not isinstance(collider_group_indices, list):
                collider_group_indices = []
            for collider_group_index in collider_group_indices:
                if ops.vrm.add_spring_bone1_spring_collider_group(
                    armature_object_name=armature_object_name,
                    spring_index=len(spring_bone.springs) - 1,
                ) != {"FINISHED"}:
                    continue
                if not isinstance(collider_group_index, int):
                    continue
                if not 0 <= collider_group_index < len(spring_bone.collider_groups):
                    continue
                collider_group = spring_bone.collider_groups[collider_group_index]
                if not collider_group:
                    continue
                collider_group_reference = spring.collider_groups[-1]
                collider_group_reference.collider_group_name = collider_group.name
            spring.active_collider_group_index = 0
        spring_bone.active_spring_index = 0

    def load_spring_bone1(
        self,
        spring_bone: SpringBone1SpringBonePropertyGroup,
        spring_bone_dict: Json,
    ) -> None:
        if not isinstance(spring_bone_dict, dict):
            return
        armature = self.armature
        if armature is None:
            message = "armature is None"
            raise ValueError(message)

        self.load_spring_bone1_colliders(spring_bone, spring_bone_dict, armature)

        self.load_spring_bone1_collider_groups(
            spring_bone,
            spring_bone_dict,
            armature.name,
        )

        self.load_spring_bone1_springs(
            spring_bone,
            spring_bone_dict,
            armature.name,
        )

    def get_object_or_bone_by_node_index(
        self, node_index: int
    ) -> Union[Object, PoseBone, None]:
        object_name = self.object_names.get(node_index)
        bone_name = self.bone_names.get(node_index)
        if object_name is not None:
            return self.context.blend_data.objects.get(object_name)
        if self.armature and bone_name is not None:
            return self.armature.pose.bones.get(bone_name)
        return None

    def load_node_constraint1(
        self,
    ) -> None:
        armature = self.armature
        if not armature:
            return

        nodes = self.parse_result.json_dict.get("nodes")
        if not isinstance(nodes, list):
            nodes = []
        for node_index, node_dict in enumerate(nodes):
            if not isinstance(node_dict, dict):
                continue

            node_extensions_dict = node_dict.get("extensions")
            if not isinstance(node_extensions_dict, dict):
                continue

            vrmc_node_constraint = node_extensions_dict.get("VRMC_node_constraint")
            if not isinstance(vrmc_node_constraint, dict):
                continue

            constraint_dict = vrmc_node_constraint.get("constraint")
            if not isinstance(constraint_dict, dict):
                continue

            roll_dict = constraint_dict.get("roll")
            aim_dict = constraint_dict.get("aim")
            rotation_dict = constraint_dict.get("rotation")

            object_or_bone = self.get_object_or_bone_by_node_index(node_index)
            if not object_or_bone:
                continue

            axis_translation = BoneExtension.reverse_axis_translation(
                get_bone_extension(object_or_bone.bone).axis_translation
                if isinstance(object_or_bone, PoseBone)
                else get_object_extension(object_or_bone).axis_translation
            )

            if isinstance(roll_dict, dict):
                constraint = object_or_bone.constraints.new(type="COPY_ROTATION")
                if not isinstance(constraint, CopyRotationConstraint):
                    logger.error("%s is not a CopyRotationConstraint", type(constraint))
                    continue
                constraint.mix_mode = "ADD"
                constraint.owner_space = "LOCAL"
                constraint.target_space = "LOCAL"
                roll_axis = roll_dict.get("rollAxis")
                if isinstance(object_or_bone, PoseBone) and isinstance(roll_axis, str):
                    roll_axis = BoneExtension.node_constraint_roll_axis_translation(
                        axis_translation,
                        roll_axis,
                    )
                constraint.use_x = False
                constraint.use_y = False
                constraint.use_z = False
                if roll_axis == "X":
                    constraint.use_x = True
                elif roll_axis == "Y":
                    constraint.use_y = True
                elif roll_axis == "Z":
                    constraint.use_z = True
                weight = convert.float_or_none(roll_dict.get("weight"))
                if weight is not None:
                    constraint.influence = weight
                source_index = roll_dict.get("source")
            elif isinstance(aim_dict, dict):
                constraint = object_or_bone.constraints.new(type="DAMPED_TRACK")
                if not isinstance(constraint, DampedTrackConstraint):
                    logger.error("%s is not a CopyRotationConstraint", type(constraint))
                    continue
                aim_axis = aim_dict.get("aimAxis")
                if isinstance(aim_axis, str) and isinstance(object_or_bone, PoseBone):
                    aim_axis = BoneExtension.node_constraint_aim_axis_translation(
                        axis_translation,
                        aim_axis,
                    )
                if isinstance(aim_axis, str):
                    track_axis = convert.VRM_AIM_AXIS_TO_BPY_TRACK_AXIS.get(aim_axis)
                    if track_axis:
                        constraint.track_axis = track_axis
                weight = convert.float_or_none(aim_dict.get("weight"))
                if weight is not None:
                    constraint.influence = weight
                source_index = aim_dict.get("source")
            elif isinstance(rotation_dict, dict):
                constraint = object_or_bone.constraints.new(type="COPY_ROTATION")
                if not isinstance(constraint, CopyRotationConstraint):
                    logger.error("%s is not a CopyRotationConstraint", type(constraint))
                    continue
                constraint.mix_mode = "ADD"
                constraint.owner_space = "LOCAL"
                constraint.target_space = "LOCAL"
                constraint.use_x = True
                constraint.use_y = True
                constraint.use_z = True
                weight = convert.float_or_none(rotation_dict.get("weight"))
                if weight is not None:
                    constraint.influence = weight
                source_index = rotation_dict.get("source")
            else:
                continue

            # TODO: Remove this when mypy becomes smarter
            if not isinstance(  # pyright: ignore [reportUnnecessaryIsInstance]
                constraint,
                (CopyRotationConstraint, DampedTrackConstraint),
            ):
                continue

            if isinstance(source_index, int):
                source = self.get_object_or_bone_by_node_index(source_index)
                if isinstance(source, Object):
                    constraint.target = source
                elif isinstance(source, PoseBone):
                    constraint.target = armature
                    constraint.subtarget = source.name
