# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
# SPDX-FileCopyrightText: 2018 iCyP

import json
import math
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Optional, Union

from bpy.types import (
    Armature,
    Context,
    Material,
    Mesh,
    Object,
)
from mathutils import Matrix, Vector

from ..common import convert, shader
from ..common.convert import Json
from ..common.logger import get_logger
from ..common.preferences import get_preferences
from ..common.progress import PartialProgress
from ..common.version import get_addon_version
from ..common.vrm0.human_bone import HumanBoneName, HumanBoneSpecifications
from ..editor import make_armature, migration
from ..editor.extension import get_armature_extension, get_material_extension
from ..editor.make_armature import (
    connect_parent_tail_and_child_head_if_very_close_position,
)
from ..editor.mtoon1.property_group import (
    Mtoon0TexturePropertyGroup,
    Mtoon1MaterialPropertyGroup,
    Mtoon1SamplerPropertyGroup,
    Mtoon1TextureInfoPropertyGroup,
    Mtoon1TexturePropertyGroup,
)
from ..editor.vrm0.property_group import (
    Vrm0BlendShapeMasterPropertyGroup,
    Vrm0FirstPersonPropertyGroup,
    Vrm0HumanoidBonePropertyGroup,
    Vrm0HumanoidPropertyGroup,
    Vrm0MetaPropertyGroup,
    Vrm0SecondaryAnimationPropertyGroup,
)
from .abstract_base_vrm_importer import AbstractBaseVrmImporter

logger = get_logger(__name__)


@dataclass(frozen=True)
class MaterialProperty:
    name: str
    shader: str
    render_queue: Optional[int]
    keyword_map: Mapping[str, bool]
    tag_map: Mapping[str, str]
    float_properties: Mapping[str, float]
    vector_properties: Mapping[str, Sequence[float]]
    texture_properties: Mapping[str, int]

    @staticmethod
    def create(json_dict: Mapping[str, Json], i: int) -> "MaterialProperty":
        fallback = MaterialProperty(
            name="Undefined",
            shader="VRM_USE_GLTFSHADER",
            render_queue=None,
            keyword_map={},
            tag_map={},
            float_properties={},
            vector_properties={},
            texture_properties={},
        )

        extensions_dict = json_dict.get("extensions")
        if not isinstance(extensions_dict, dict):
            return fallback

        vrm_dict = extensions_dict.get("VRM")
        if not isinstance(vrm_dict, dict):
            return fallback

        material_property_dicts = vrm_dict.get("materialProperties")
        if not isinstance(material_property_dicts, list):
            return fallback

        if not 0 <= i < len(material_property_dicts):
            return fallback

        material_property_dict = material_property_dicts[i]
        if not isinstance(material_property_dict, dict):
            return fallback

        name = material_property_dict.get("name")
        if not isinstance(name, str):
            name = fallback.name

        shader = material_property_dict.get("shader")
        if not isinstance(shader, str):
            shader = fallback.shader

        render_queue = material_property_dict.get("renderQueue")
        if not isinstance(render_queue, int):
            render_queue = fallback.render_queue

        raw_keyword_map = material_property_dict.get("keywordMap")
        if isinstance(raw_keyword_map, dict):
            keyword_map: Mapping[str, bool] = {
                k: v for k, v in raw_keyword_map.items() if isinstance(v, bool)
            }
        else:
            keyword_map = fallback.keyword_map

        raw_tag_map = material_property_dict.get("tagMap")
        if isinstance(raw_tag_map, dict):
            tag_map: Mapping[str, str] = {
                k: v for k, v in raw_tag_map.items() if isinstance(v, str)
            }
        else:
            tag_map = fallback.tag_map

        raw_float_properties = material_property_dict.get("floatProperties")
        if isinstance(raw_float_properties, dict):
            float_properties: Mapping[str, float] = {
                k: float(v)
                for k, v in raw_float_properties.items()
                if isinstance(v, (float, int))
            }
        else:
            float_properties = fallback.float_properties

        raw_vector_properties = material_property_dict.get("vectorProperties")
        if isinstance(raw_vector_properties, dict):
            vector_properties: Mapping[str, Sequence[float]] = {
                k: [
                    vector_element
                    for vector_element in vector
                    if isinstance(vector_element, (float, int))
                ]
                for k, vector in raw_vector_properties.items()
                if isinstance(vector, list)
            }
        else:
            vector_properties = fallback.vector_properties

        raw_texture_properties = material_property_dict.get("textureProperties")
        if isinstance(raw_texture_properties, dict):
            texture_properties: Mapping[str, int] = {
                k: v for k, v in raw_texture_properties.items() if isinstance(v, int)
            }
        else:
            texture_properties = fallback.texture_properties

        return MaterialProperty(
            name=name,
            shader=shader,
            render_queue=render_queue,
            keyword_map=keyword_map,
            tag_map=tag_map,
            float_properties=float_properties,
            vector_properties=vector_properties,
            texture_properties=texture_properties,
        )


class Vrm0Importer(AbstractBaseVrmImporter):
    def load_materials(self, progress: PartialProgress) -> None:
        shader_to_assignment_method = {
            "VRM/MToon": self.assign_mtoon0_property,
            "VRM/UnlitTransparentZWrite": self.assign_transparent_z_write_property,
        }

        material_dicts = self.parse_result.json_dict.get("materials")
        if not isinstance(material_dicts, list):
            return

        material_properties = [
            MaterialProperty.create(self.parse_result.json_dict, index)
            for index in range(len(material_dicts))
        ]

        for index, material_property in enumerate(material_properties):
            assignment_method = shader_to_assignment_method.get(
                material_property.shader
            )
            if not assignment_method:
                continue

            material = self.materials.get(index)
            if not material:
                material = self.context.blend_data.materials.new(material_property.name)
                self.materials[index] = material

            self.reset_material(material)
            assignment_method(material, material_property)
            progress.update(float(index) / len(material_properties))

        progress.update(1)

    def assign_mtoon0_texture(
        self,
        texture: Union[Mtoon0TexturePropertyGroup, Mtoon1TexturePropertyGroup],
        texture_index: Optional[int],
    ) -> bool:
        if texture_index is None:
            return False
        texture_dicts = self.parse_result.json_dict.get("textures")
        if not isinstance(texture_dicts, list):
            return False
        if not 0 <= texture_index < len(texture_dicts):
            return False
        texture_dict = texture_dicts[texture_index]
        if not isinstance(texture_dict, dict):
            return False

        source = texture_dict.get("source")
        if isinstance(source, int):
            image = self.images.get(source)
            if image:
                image.colorspace_settings.name = texture.colorspace
                texture.source = image

        sampler = texture_dict.get("sampler")
        samplers = self.parse_result.json_dict.get("samplers")
        if not isinstance(sampler, int) or not isinstance(samplers, list):
            return True
        if not 0 <= sampler < len(samplers):
            return True

        sampler_dict = samplers[sampler]
        if not isinstance(sampler_dict, dict):
            return True

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

        return True

    def assign_mtoon0_texture_info(
        self,
        texture_info: Mtoon1TextureInfoPropertyGroup,
        texture_index: Optional[int],
        uv_transform: tuple[float, float, float, float],
    ) -> None:
        if not self.assign_mtoon0_texture(texture_info.index, texture_index):
            return

        texture_info.extensions.khr_texture_transform.offset = (
            uv_transform[0],
            uv_transform[1],
        )
        texture_info.extensions.khr_texture_transform.scale = (
            uv_transform[2],
            uv_transform[3],
        )

    def assign_mtoon0_property(
        self, material: Material, material_property: MaterialProperty
    ) -> None:
        # https://github.com/saturday06/VRM-Addon-for-Blender/blob/2_15_26/io_scene_vrm/editor/mtoon1/ops.py#L98
        material.use_backface_culling = True

        gltf = get_material_extension(material).mtoon1
        gltf.addon_version = get_addon_version()
        gltf.enabled = True
        gltf.show_expanded_mtoon0 = True
        mtoon = gltf.extensions.vrmc_materials_mtoon

        gltf.alpha_mode = gltf.ALPHA_MODE_OPAQUE.identifier
        blend_mode = material_property.float_properties.get("_BlendMode")
        if blend_mode is not None:
            if math.fabs(blend_mode - 1) < 0.001:
                gltf.alpha_mode = gltf.ALPHA_MODE_MASK.identifier
            elif math.fabs(blend_mode - 2) < 0.001:
                gltf.alpha_mode = gltf.ALPHA_MODE_BLEND.identifier
            elif math.fabs(blend_mode - 3) < 0.001:
                gltf.alpha_mode = gltf.ALPHA_MODE_BLEND.identifier
                mtoon.transparent_with_z_write = True

        cutoff = material_property.float_properties.get("_Cutoff")
        if cutoff is not None:
            gltf.alpha_cutoff = cutoff

        gltf.double_sided = True
        cull_mode = material_property.float_properties.get("_CullMode")
        if cull_mode is not None:
            if math.fabs(cull_mode - 1) < 0.001:
                gltf.mtoon0_front_cull_mode = True
            elif math.fabs(cull_mode - 2) < 0.001:
                gltf.double_sided = False

        base_color_factor = shader.rgba_or_none(
            material_property.vector_properties.get("_Color")
        )
        if base_color_factor:
            gltf.pbr_metallic_roughness.base_color_factor = convert.srgb_to_linear(
                base_color_factor
            )

        raw_uv_transform = material_property.vector_properties.get("_MainTex")
        if raw_uv_transform is None or len(raw_uv_transform) != 4:
            uv_transform = (0.0, 0.0, 1.0, 1.0)
        else:
            uv_transform = (
                raw_uv_transform[0],
                raw_uv_transform[1],
                raw_uv_transform[2],
                raw_uv_transform[3],
            )

        self.assign_mtoon0_texture_info(
            gltf.pbr_metallic_roughness.base_color_texture,
            material_property.texture_properties.get("_MainTex"),
            uv_transform,
        )

        shade_color_factor = shader.rgb_or_none(
            material_property.vector_properties.get("_ShadeColor")
        )
        if shade_color_factor:
            mtoon.shade_color_factor = convert.srgb_to_linear(shade_color_factor)

        self.assign_mtoon0_texture_info(
            mtoon.shade_multiply_texture,
            material_property.texture_properties.get("_ShadeTexture"),
            uv_transform,
        )

        self.assign_mtoon0_texture_info(
            gltf.normal_texture,
            material_property.texture_properties.get("_BumpMap"),
            uv_transform,
        )
        normal_texture_scale = material_property.float_properties.get("_BumpScale")
        if isinstance(normal_texture_scale, (float, int)):
            gltf.normal_texture.scale = float(normal_texture_scale)

        shading_shift_0x = material_property.float_properties.get("_ShadeShift")
        if shading_shift_0x is None:
            shading_shift_0x = 0

        shading_toony_0x = material_property.float_properties.get("_ShadeToony")
        if shading_toony_0x is None:
            shading_toony_0x = 0

        mtoon.shading_shift_factor = convert.mtoon_shading_shift_0_to_1(
            shading_toony_0x, shading_shift_0x
        )

        mtoon.shading_toony_factor = convert.mtoon_shading_toony_0_to_1(
            shading_toony_0x, shading_shift_0x
        )

        indirect_light_intensity = material_property.float_properties.get(
            "_IndirectLightIntensity"
        )
        if indirect_light_intensity is not None:
            mtoon.gi_equalization_factor = convert.mtoon_intensity_to_gi_equalization(
                indirect_light_intensity
            )
        else:
            mtoon.gi_equalization_factor = 0.5

        raw_emissive_factor = shader.rgb_or_none(
            material_property.vector_properties.get("_EmissionColor")
        ) or (0, 0, 0)
        max_color_component_value = max(raw_emissive_factor)
        if max_color_component_value > 1:
            gltf.emissive_factor = convert.srgb_to_linear(
                Vector(raw_emissive_factor) / max_color_component_value
            )
            gltf.extensions.khr_materials_emissive_strength.emissive_strength = (
                max_color_component_value
            )
        else:
            gltf.emissive_factor = convert.srgb_to_linear(raw_emissive_factor)

        self.assign_mtoon0_texture_info(
            gltf.emissive_texture,
            material_property.texture_properties.get("_EmissionMap"),
            uv_transform,
        )

        self.assign_mtoon0_texture_info(
            mtoon.matcap_texture,
            material_property.texture_properties.get("_SphereAdd"),
            (0, 0, 1, 1),
        )

        parametric_rim_color_factor = shader.rgb_or_none(
            material_property.vector_properties.get("_RimColor")
        )
        if parametric_rim_color_factor:
            mtoon.parametric_rim_color_factor = convert.srgb_to_linear(
                parametric_rim_color_factor
            )

        parametric_rim_fresnel_power_factor = material_property.float_properties.get(
            "_RimFresnelPower"
        )
        if isinstance(parametric_rim_fresnel_power_factor, (float, int)):
            mtoon.parametric_rim_fresnel_power_factor = (
                parametric_rim_fresnel_power_factor
            )

        mtoon.parametric_rim_lift_factor = material_property.float_properties.get(
            "_RimLift", 0
        )

        self.assign_mtoon0_texture_info(
            mtoon.rim_multiply_texture,
            material_property.texture_properties.get("_RimTexture"),
            uv_transform,
        )

        # https://github.com/vrm-c/UniVRM/blob/7c9919ef47a25c04100a2dcbe6a75dff49ef4857/Assets/VRM10/Runtime/Migration/Materials/MigrationMToonMaterial.cs#L287-L290
        mtoon.rim_lighting_mix_factor = 1.0
        rim_lighting_mix = material_property.float_properties.get("_RimLightingMix")
        if rim_lighting_mix is not None:
            gltf.mtoon0_rim_lighting_mix = rim_lighting_mix

        mtoon.enable_outline_preview = get_preferences(
            self.context
        ).enable_mtoon_outline_preview

        centimeter_to_meter = 0.01
        one_hundredth = 0.01

        outline_width_mode = int(
            round(material_property.float_properties.get("_OutlineWidthMode", 0))
        )

        outline_width = material_property.float_properties.get("_OutlineWidth")
        if outline_width is None:
            outline_width = 0.0

        if outline_width_mode == 0:
            mtoon.outline_width_mode = mtoon.OUTLINE_WIDTH_MODE_NONE.identifier
        elif outline_width_mode == 1:
            mtoon.outline_width_mode = (
                mtoon.OUTLINE_WIDTH_MODE_WORLD_COORDINATES.identifier
            )
            mtoon.outline_width_factor = max(0.0, outline_width * centimeter_to_meter)
        else:
            mtoon.outline_width_mode = (
                mtoon.OUTLINE_WIDTH_MODE_SCREEN_COORDINATES.identifier
            )
            mtoon.outline_width_factor = max(0.0, outline_width * one_hundredth * 0.5)
            outline_scaled_max_distance = material_property.float_properties.get(
                "_OutlineScaledMaxDistance"
            )
            if outline_scaled_max_distance is not None:
                gltf.mtoon0_outline_scaled_max_distance = outline_scaled_max_distance

        self.assign_mtoon0_texture_info(
            mtoon.outline_width_multiply_texture,
            material_property.texture_properties.get("_OutlineWidthTexture"),
            uv_transform,
        )

        outline_color_factor = shader.rgb_or_none(
            material_property.vector_properties.get("_OutlineColor")
        )
        if outline_color_factor:
            mtoon.outline_color_factor = convert.srgb_to_linear(outline_color_factor)

        outline_color_mode = material_property.float_properties.get("_OutlineColorMode")
        if (
            outline_color_mode is not None
            and math.fabs(outline_color_mode - 1) < 0.00001
        ):
            mtoon.outline_lighting_mix_factor = (
                material_property.float_properties.get("_OutlineLightingMix") or 1
            )
        else:
            mtoon.outline_lighting_mix_factor = 0  # Fixed Color

        self.assign_mtoon0_texture_info(
            mtoon.uv_animation_mask_texture,
            material_property.texture_properties.get("_UvAnimMaskTexture"),
            uv_transform,
        )

        uv_animation_rotation_speed_factor = material_property.float_properties.get(
            "_UvAnimRotation"
        )
        if isinstance(uv_animation_rotation_speed_factor, (float, int)):
            mtoon.uv_animation_rotation_speed_factor = (
                uv_animation_rotation_speed_factor
            )

        uv_animation_scroll_x_speed_factor = material_property.float_properties.get(
            "_UvAnimScrollX"
        )
        if isinstance(uv_animation_scroll_x_speed_factor, (float, int)):
            mtoon.uv_animation_scroll_x_speed_factor = (
                uv_animation_scroll_x_speed_factor
            )

        uv_animation_scroll_y_speed_factor = material_property.float_properties.get(
            "_UvAnimScrollY"
        )
        if isinstance(uv_animation_scroll_y_speed_factor, (float, int)):
            mtoon.uv_animation_scroll_y_speed_factor = (
                -uv_animation_scroll_y_speed_factor
            )

        light_color_attenuation = material_property.float_properties.get(
            "_LightColorAttenuation"
        )
        if light_color_attenuation is not None:
            gltf.mtoon0_light_color_attenuation = light_color_attenuation

        self.assign_mtoon0_texture(
            gltf.mtoon0_receive_shadow_texture,
            material_property.texture_properties.get("_ReceiveShadowTexture"),
        )

        gltf.mtoon0_receive_shadow_rate = material_property.float_properties.get(
            "_ReceiveShadowRate", 0.5
        )

        self.assign_mtoon0_texture(
            gltf.mtoon0_shading_grade_texture,
            material_property.texture_properties.get("_ShadingGradeTexture"),
        )

        gltf.mtoon0_shading_grade_rate = material_property.float_properties.get(
            "_ShadingGradeRate", 0.5
        )

        if material_property.render_queue is not None:
            gltf.mtoon0_render_queue = material_property.render_queue

    def assign_transparent_z_write_property(
        self,
        material: Material,
        material_property: MaterialProperty,
    ) -> None:
        gltf = get_material_extension(material).mtoon1
        gltf.enabled = True
        mtoon = gltf.extensions.vrmc_materials_mtoon

        main_texture_index = material_property.texture_properties.get("_MainTex")
        main_texture_image = None
        if isinstance(main_texture_index, int):
            texture_dicts = self.parse_result.json_dict.get("textures")
            if isinstance(texture_dicts, list) and 0 <= main_texture_index < len(
                texture_dicts
            ):
                texture_dict = texture_dicts[main_texture_index]
                if isinstance(texture_dict, dict):
                    image_index = texture_dict.get("source")
                    if isinstance(image_index, int):
                        main_texture_image = self.images.get(image_index)
        if main_texture_image:
            gltf.pbr_metallic_roughness.base_color_texture.index.source = (
                main_texture_image
            )
            gltf.emissive_texture.index.source = main_texture_image
            mtoon.shade_multiply_texture.index.source = main_texture_image

        gltf.pbr_metallic_roughness.base_color_factor = (0, 0, 0, 1)
        gltf.emissive_factor = (1, 1, 1)

        gltf.alpha_mode = Mtoon1MaterialPropertyGroup.ALPHA_MODE_BLEND.identifier
        gltf.alpha_cutoff = 0.5
        gltf.double_sided = False
        mtoon.transparent_with_z_write = True
        mtoon.shade_color_factor = (0, 0, 0)
        mtoon.shading_toony_factor = 0.95
        mtoon.shading_shift_factor = -0.05
        mtoon.rim_lighting_mix_factor = 1
        mtoon.parametric_rim_fresnel_power_factor = 5
        mtoon.parametric_rim_lift_factor = 0

    def load_gltf_extensions(self) -> None:
        armature = self.armature
        if not armature:
            return
        addon_extension = get_armature_extension(self.armature_data)
        addon_extension.spec_version = addon_extension.SPEC_VERSION_VRM0
        vrm0 = addon_extension.vrm0

        if self.parse_result.spec_version_number >= (1, 0):
            return

        vrm0_extension = self.parse_result.vrm0_extension_dict

        addon_extension.addon_version = get_addon_version()

        textblock = self.context.blend_data.texts.new(name="vrm.json")
        textblock.write(json.dumps(self.parse_result.json_dict, indent=4))

        self.load_vrm0_meta(vrm0.meta, vrm0_extension.get("meta"))
        self.load_vrm0_humanoid(vrm0.humanoid, vrm0_extension.get("humanoid"))
        setup_bones(self.context, armature)
        self.load_vrm0_first_person(
            vrm0.first_person, vrm0_extension.get("firstPerson")
        )
        self.load_vrm0_blend_shape_master(
            vrm0.blend_shape_master, vrm0_extension.get("blendShapeMaster")
        )
        self.load_vrm0_secondary_animation(
            vrm0.secondary_animation, vrm0_extension.get("secondaryAnimation")
        )
        migration.migrate(self.context, armature.name)

    def load_vrm0_meta(self, meta: Vrm0MetaPropertyGroup, meta_dict: Json) -> None:
        if not isinstance(meta_dict, dict):
            return

        title = meta_dict.get("title")
        if isinstance(title, str):
            meta.title = title

        version = meta_dict.get("version")
        if isinstance(version, str):
            meta.version = version

        author = meta_dict.get("author")
        if isinstance(author, str):
            meta.author = author

        contact_information = meta_dict.get("contactInformation")
        if isinstance(contact_information, str):
            meta.contact_information = contact_information

        reference = meta_dict.get("reference")
        if isinstance(reference, str):
            meta.reference = reference

        allowed_user_name = meta_dict.get("allowedUserName")
        if (
            isinstance(allowed_user_name, str)
            and allowed_user_name in meta.allowed_user_name_enum.identifiers()
        ):
            meta.allowed_user_name = allowed_user_name

        violent_ussage_name = meta_dict.get("violentUssageName")
        if (
            isinstance(violent_ussage_name, str)
            and violent_ussage_name in meta.violent_ussage_name_enum.identifiers()
        ):
            meta.violent_ussage_name = violent_ussage_name

        sexual_ussage_name = meta_dict.get("sexualUssageName")
        if (
            isinstance(sexual_ussage_name, str)
            and sexual_ussage_name in meta.sexual_ussage_name_enum.identifiers()
        ):
            meta.sexual_ussage_name = sexual_ussage_name

        commercial_ussage_name = meta_dict.get("commercialUssageName")
        if (
            isinstance(commercial_ussage_name, str)
            and commercial_ussage_name in meta.commercial_ussage_name_enum.identifiers()
        ):
            meta.commercial_ussage_name = commercial_ussage_name

        other_permission_url = meta_dict.get("otherPermissionUrl")
        if isinstance(other_permission_url, str):
            meta.other_permission_url = other_permission_url

        license_name = meta_dict.get("licenseName")
        if (
            isinstance(license_name, str)
            and license_name in meta.license_name_enum.identifiers()
        ):
            meta.license_name = license_name

        other_license_url = meta_dict.get("otherLicenseUrl")
        if isinstance(other_license_url, str):
            meta.other_license_url = other_license_url

        texture = meta_dict.get("texture")
        texture_dicts = self.parse_result.json_dict.get("textures")
        if (
            isinstance(texture, int)
            and isinstance(texture_dicts, list)
            # extensions.VRM.meta.texture could be -1
            # https://github.com/vrm-c/UniVRM/issues/91#issuecomment-454284964
            and 0 <= texture < len(texture_dicts)
        ):
            texture_dict = texture_dicts[texture]
            if isinstance(texture_dict, dict):
                image_index = texture_dict.get("source")
                if isinstance(image_index, int) and image_index in self.images:
                    meta.texture = self.images[image_index]

    def load_vrm0_humanoid(
        self, humanoid: Vrm0HumanoidPropertyGroup, humanoid_dict: Json
    ) -> None:
        if not isinstance(humanoid_dict, dict):
            return
        human_bone_dicts = humanoid_dict.get("humanBones")
        if isinstance(human_bone_dicts, list):
            for human_bone_dict in human_bone_dicts:
                if not isinstance(human_bone_dict, dict):
                    continue

                bone = human_bone_dict.get("bone")
                if bone not in HumanBoneSpecifications.all_names:
                    continue

                node = human_bone_dict.get("node")
                if not isinstance(node, int) or node not in self.bone_names:
                    continue

                human_bone = next(
                    (
                        human_bone
                        for human_bone in humanoid.human_bones
                        if human_bone.bone == bone
                    ),
                    None,
                )
                if human_bone:
                    logger.warning('Duplicated bone: "%s"', bone)
                else:
                    human_bone = humanoid.human_bones.add()
                human_bone.bone = bone
                human_bone.node.set_bone_name(self.bone_names[node])

                use_default_values = human_bone_dict.get("useDefaultValues")
                if isinstance(use_default_values, bool):
                    human_bone.use_default_values = use_default_values

                min_ = convert.vrm_json_vector3_to_tuple(human_bone_dict.get("min"))
                if min_ is not None:
                    human_bone.min = min_

                max_ = convert.vrm_json_vector3_to_tuple(human_bone_dict.get("max"))
                if max_ is not None:
                    human_bone.max = max_

                center = convert.vrm_json_vector3_to_tuple(
                    human_bone_dict.get("center")
                )
                if center is not None:
                    human_bone.center = center

                axis_length = human_bone_dict.get("axisLength")
                if isinstance(axis_length, (int, float)):
                    human_bone.axis_length = axis_length

        arm_stretch = humanoid_dict.get("armStretch")
        if isinstance(arm_stretch, (int, float)):
            humanoid.arm_stretch = arm_stretch

        leg_stretch = humanoid_dict.get("legStretch")
        if isinstance(leg_stretch, (int, float)):
            humanoid.leg_stretch = leg_stretch

        upper_arm_twist = humanoid_dict.get("upperArmTwist")
        if isinstance(upper_arm_twist, (int, float)):
            humanoid.upper_arm_twist = upper_arm_twist

        lower_arm_twist = humanoid_dict.get("lowerArmTwist")
        if isinstance(lower_arm_twist, (int, float)):
            humanoid.lower_arm_twist = lower_arm_twist

        upper_leg_twist = humanoid_dict.get("upperLegTwist")
        if isinstance(upper_leg_twist, (int, float)):
            humanoid.upper_leg_twist = upper_leg_twist

        lower_leg_twist = humanoid_dict.get("lowerLegTwist")
        if isinstance(lower_leg_twist, (int, float)):
            humanoid.lower_leg_twist = lower_leg_twist

        feet_spacing = humanoid_dict.get("feetSpacing")
        if isinstance(feet_spacing, (int, float)):
            humanoid.feet_spacing = feet_spacing

        has_translation_dof = humanoid_dict.get("hasTranslationDoF")
        if isinstance(has_translation_dof, bool):
            humanoid.has_translation_dof = has_translation_dof

    def load_vrm0_first_person(
        self,
        first_person: Vrm0FirstPersonPropertyGroup,
        first_person_dict: Json,
    ) -> None:
        if not isinstance(first_person_dict, dict):
            return

        first_person_bone = first_person_dict.get("firstPersonBone")
        if isinstance(first_person_bone, int) and first_person_bone in self.bone_names:
            first_person.first_person_bone.set_bone_name(
                self.bone_names[first_person_bone]
            )

        first_person_bone_offset = convert.vrm_json_vector3_to_tuple(
            first_person_dict.get("firstPersonBoneOffset")
        )
        if first_person_bone_offset is not None:
            # Axis confusing
            (x, y, z) = first_person_bone_offset
            first_person.first_person_bone_offset = (x, z, y)

        mesh_annotation_dicts = first_person_dict.get("meshAnnotations")
        if isinstance(mesh_annotation_dicts, list):
            for mesh_annotation_dict in mesh_annotation_dicts:
                mesh_annotation = first_person.mesh_annotations.add()

                if not isinstance(mesh_annotation_dict, dict):
                    continue

                mesh = mesh_annotation_dict.get("mesh")
                if isinstance(mesh, int) and mesh in self.meshes:
                    mesh_annotation.mesh.mesh_object_name = self.meshes[mesh].name

                first_person_flag = mesh_annotation_dict.get("firstPersonFlag")
                if (
                    isinstance(first_person_flag, str)
                    and first_person_flag
                    in mesh_annotation.first_person_flag_enum.identifiers()
                ):
                    mesh_annotation.first_person_flag = first_person_flag

        look_at_type_name = first_person_dict.get("lookAtTypeName")
        if (
            isinstance(look_at_type_name, str)
            and look_at_type_name in first_person.look_at_type_name_enum.identifiers()
        ):
            first_person.look_at_type_name = look_at_type_name

        for look_at, look_at_dict in [
            (
                first_person.look_at_horizontal_inner,
                first_person_dict.get("lookAtHorizontalInner"),
            ),
            (
                first_person.look_at_horizontal_outer,
                first_person_dict.get("lookAtHorizontalOuter"),
            ),
            (
                first_person.look_at_vertical_down,
                first_person_dict.get("lookAtVerticalDown"),
            ),
            (
                first_person.look_at_vertical_up,
                first_person_dict.get("lookAtVerticalUp"),
            ),
        ]:
            if not isinstance(look_at_dict, dict):
                continue

            curve = convert.vrm_json_curve_to_list(look_at_dict.get("curve"))
            if curve is not None:
                look_at.curve = curve

            x_range = look_at_dict.get("xRange")
            if isinstance(x_range, (float, int)):
                look_at.x_range = x_range

            y_range = look_at_dict.get("yRange")
            if isinstance(y_range, (float, int)):
                look_at.y_range = y_range

    def load_vrm0_blend_shape_master(
        self,
        blend_shape_master: Vrm0BlendShapeMasterPropertyGroup,
        blend_shape_master_dict: Json,
    ) -> None:
        if not isinstance(blend_shape_master_dict, dict):
            return
        blend_shape_group_dicts = blend_shape_master_dict.get("blendShapeGroups")
        if not isinstance(blend_shape_group_dicts, list):
            return

        for blend_shape_group_dict in blend_shape_group_dicts:
            blend_shape_group = blend_shape_master.blend_shape_groups.add()

            if not isinstance(blend_shape_group_dict, dict):
                continue

            name = blend_shape_group_dict.get("name")
            if isinstance(name, str):
                blend_shape_group.name = name

            preset_name = blend_shape_group_dict.get("presetName")
            if (
                isinstance(preset_name, str)
                and preset_name in blend_shape_group.preset_name_enum.identifiers()
            ):
                blend_shape_group.preset_name = preset_name

            bind_dicts = blend_shape_group_dict.get("binds")
            if isinstance(bind_dicts, list):
                for bind_dict in bind_dicts:
                    if not isinstance(bind_dict, dict):
                        continue

                    mesh_index = bind_dict.get("mesh")
                    if not isinstance(mesh_index, int):
                        continue

                    mesh_object = self.meshes.get(mesh_index)
                    if not mesh_object:
                        continue

                    bind = blend_shape_group.binds.add()
                    bind.mesh.mesh_object_name = mesh_object.name
                    mesh_data = mesh_object.data
                    if isinstance(mesh_data, Mesh):
                        shape_keys = mesh_data.shape_keys
                        if shape_keys:
                            index = bind_dict.get("index")
                            if isinstance(index, int) and (
                                1 <= (index + 1) < len(shape_keys.key_blocks)
                            ):
                                bind.index = list(shape_keys.key_blocks.keys())[
                                    index + 1
                                ]
                    weight = bind_dict.get("weight")
                    if not isinstance(weight, (int, float)):
                        weight = 0
                    bind.weight = min(max(weight / 100.0, 0), 1)

            material_value_dicts = blend_shape_group_dict.get("materialValues")
            if isinstance(material_value_dicts, list):
                for material_value_dict in material_value_dicts:
                    material_value = blend_shape_group.material_values.add()

                    if not isinstance(material_value_dict, dict):
                        continue

                    material_name = material_value_dict.get("materialName")
                    if (
                        isinstance(material_name, str)
                        and material_name in self.context.blend_data.materials
                    ):
                        material_value.material = self.context.blend_data.materials[
                            material_name
                        ]

                    property_name = material_value_dict.get("propertyName")
                    if isinstance(property_name, str):
                        material_value.property_name = property_name

                    target_value_vector = material_value_dict.get("targetValue")
                    if isinstance(target_value_vector, list):
                        for v in target_value_vector:
                            material_value.target_value.add().value = (
                                v if isinstance(v, (int, float)) else 0
                            )

            is_binary = blend_shape_group_dict.get("isBinary")
            if isinstance(is_binary, bool):
                blend_shape_group.is_binary = is_binary

    def load_vrm0_secondary_animation(
        self,
        secondary_animation: Vrm0SecondaryAnimationPropertyGroup,
        secondary_animation_dict: Json,
    ) -> None:
        if not isinstance(secondary_animation_dict, dict):
            return
        armature = self.armature
        if armature is None:
            message = "armature is None"
            raise ValueError(message)

        collider_group_dicts = secondary_animation_dict.get("colliderGroups")
        if not isinstance(collider_group_dicts, list):
            collider_group_dicts = []

        self.context.view_layer.depsgraph.update()
        self.context.scene.view_layers.update()
        collider_objs: list[Object] = []
        for collider_group_dict in collider_group_dicts:
            collider_group = secondary_animation.collider_groups.add()
            collider_group.uuid = uuid.uuid4().hex
            collider_group.refresh(armature)

            if not isinstance(collider_group_dict, dict):
                continue

            node = collider_group_dict.get("node")
            if not isinstance(node, int) or node not in self.bone_names:
                continue

            bone_name = self.bone_names[node]
            collider_group.node.set_bone_name(bone_name)
            collider_dicts = collider_group_dict.get("colliders")
            if not isinstance(collider_dicts, list):
                continue

            for collider_index, collider_dict in enumerate(collider_dicts):
                collider = collider_group.colliders.add()

                if not isinstance(collider_dict, dict):
                    continue

                offset = convert.vrm_json_vector3_to_tuple(collider_dict.get("offset"))
                if offset is None:
                    offset = (0, 0, 0)

                radius = collider_dict.get("radius")
                if not isinstance(radius, (int, float)):
                    radius = 0

                collider_name = f"{bone_name}_collider_{collider_index}"
                obj = self.context.blend_data.objects.new(
                    name=collider_name, object_data=None
                )
                collider.bpy_object = obj
                obj.parent = self.armature
                obj.parent_type = "BONE"
                obj.parent_bone = bone_name
                fixed_offset = [
                    offset[axis] * inv for axis, inv in zip([0, 2, 1], [-1, -1, 1])
                ]  # TODO: Y軸反転はUniVRMのシリアライズに合わせてる

                # boneのtail側にparentされるので、根元からのpositionに動かしなおす
                obj.matrix_world = Matrix.Translation(
                    [
                        armature.matrix_world.to_translation()[i]
                        + self.armature_data.bones[
                            bone_name
                        ].matrix_local.to_translation()[i]
                        + fixed_offset[i]
                        for i in range(3)
                    ]
                )

                obj.empty_display_size = radius
                obj.empty_display_type = "SPHERE"
                collider_objs.append(obj)
        if collider_objs:
            colliders_collection = self.context.blend_data.collections.new("Colliders")
            self.context.scene.collection.children.link(colliders_collection)
            for collider_obj in collider_objs:
                colliders_collection.objects.link(collider_obj)

        for collider_group in secondary_animation.collider_groups:
            collider_group.refresh(armature)

        bone_group_dicts = secondary_animation_dict.get("boneGroups")
        if not isinstance(bone_group_dicts, list):
            bone_group_dicts = []

        for bone_group_dict in bone_group_dicts:
            bone_group = secondary_animation.bone_groups.add()

            if not isinstance(bone_group_dict, dict):
                bone_group.refresh(armature)
                continue

            comment = bone_group_dict.get("comment")
            if isinstance(comment, str):
                bone_group.comment = comment

            stiffiness = bone_group_dict.get("stiffiness")
            if isinstance(stiffiness, (int, float)):
                bone_group.stiffiness = stiffiness

            gravity_power = bone_group_dict.get("gravityPower")
            if isinstance(gravity_power, (int, float)):
                bone_group.gravity_power = gravity_power

            gravity_dir = convert.vrm_json_vector3_to_tuple(
                bone_group_dict.get("gravityDir")
            )
            if gravity_dir is not None:
                # Axis confusing
                (x, y, z) = gravity_dir
                bone_group.gravity_dir = (x, z, y)

            drag_force = bone_group_dict.get("dragForce")
            if isinstance(drag_force, (int, float)):
                bone_group.drag_force = drag_force

            center = bone_group_dict.get("center")
            if isinstance(center, int) and center in self.bone_names:
                bone_group.center.set_bone_name(self.bone_names[center])

            hit_radius = bone_group_dict.get("hitRadius")
            if isinstance(hit_radius, (int, float)):
                bone_group.hit_radius = hit_radius

            bones = bone_group_dict.get("bones")
            if isinstance(bones, list):
                for bone in bones:
                    bone_prop = bone_group.bones.add()
                    if not isinstance(bone, int) or bone not in self.bone_names:
                        continue

                    bone_prop.set_bone_name(self.bone_names[bone])

            collider_group_dicts = bone_group_dict.get("colliderGroups")
            if isinstance(collider_group_dicts, list):
                for collider_group in collider_group_dicts:
                    if not isinstance(collider_group, int) or not (
                        0 <= collider_group < len(secondary_animation.collider_groups)
                    ):
                        continue
                    collider_group_uuid = bone_group.collider_groups.add()
                    collider_group_uuid.value = secondary_animation.collider_groups[
                        collider_group
                    ].uuid

        for bone_group in secondary_animation.bone_groups:
            bone_group.refresh(armature)

        collider_object_names = [
            collider.bpy_object.name
            for collider_group in secondary_animation.collider_groups
            for collider in collider_group.colliders
            if collider.bpy_object is not None
        ]
        if collider_object_names:
            imported_object_names = self.imported_object_names
            if imported_object_names is None:
                imported_object_names = []
                self.imported_object_names = imported_object_names
            imported_object_names.extend(collider_object_names)

    def find_vrm0_bone_node_indices(self) -> list[int]:
        result: list[int] = []
        vrm0_dict = self.parse_result.vrm0_extension_dict

        first_person_dict = vrm0_dict.get("firstPerson")
        if isinstance(first_person_dict, dict):
            first_person_bone_index = first_person_dict.get("firstPersonBone")
            if isinstance(first_person_bone_index, int):
                result.append(first_person_bone_index)

        humanoid_dict = vrm0_dict.get("humanoid")
        if isinstance(humanoid_dict, dict):
            human_bone_dicts = humanoid_dict.get("humanBones")
            if isinstance(human_bone_dicts, list):
                for human_bone_dict in human_bone_dicts:
                    if not isinstance(human_bone_dict, dict):
                        continue
                    node_index = human_bone_dict.get("node")
                    if isinstance(node_index, int):
                        result.append(node_index)

        secondary_animation_dict = vrm0_dict.get("secondaryAnimation")
        if isinstance(secondary_animation_dict, dict):
            collider_group_dicts = secondary_animation_dict.get("colliderGroups")
            if isinstance(collider_group_dicts, list):
                for collider_group_dict in collider_group_dicts:
                    if not isinstance(collider_group_dict, dict):
                        continue
                    node_index = collider_group_dict.get("node")
                    if isinstance(node_index, int):
                        result.append(node_index)

            bone_group_dicts = secondary_animation_dict.get("boneGroups")
            if isinstance(bone_group_dicts, list):
                for bone_group_dict in bone_group_dicts:
                    if not isinstance(bone_group_dict, dict):
                        continue
                    center_index = bone_group_dict.get("center")
                    if isinstance(center_index, int):
                        result.append(center_index)
                    bone_indices = bone_group_dict.get("bones")
                    if isinstance(bone_indices, list):
                        result.extend(
                            bone_index
                            for bone_index in bone_indices
                            if isinstance(bone_index, int)
                        )
        return list(dict.fromkeys(result))  # Remove duplicates

    def find_vrm_bone_node_indices(self) -> list[int]:
        # TODO: SkinnedMeshRenderer root <=> skin.skeleton???
        return list(
            dict.fromkeys(  # Remove duplicates
                self.find_vrm0_bone_node_indices()
            )
        )


def setup_bones(context: Context, armature: Object) -> None:
    """Human Boneの方向と長さを設定する.

    VRM0はボーンの方向と長さを持たないため、現在はインポート時にFORTUNEによる方向と長さ決めを行っている。
    ただ、FORTUNEは人体の構造を考慮しないため、不自然なボーンになることがある。そのため、人体の構造を考慮した
    ヒューリスティックな方式で方向と長さを決める。

    いつかやりたいこと:
        Headの角度を、親の角度から30度以内に制限
        ToesやFootが接地していない場合は仰角をつける。
    """
    if not isinstance(armature.data, Armature):
        return
    addon_extension = get_armature_extension(armature.data)

    Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
    Vrm0HumanoidPropertyGroup.update_all_node_candidates(
        context,
        armature.data.name,
        force=True,
    )

    human_bones = addon_extension.vrm0.humanoid.human_bones
    for human_bone in human_bones:
        if (
            human_bone.node.bone_name
            and human_bone.node.bone_name not in human_bone.node_candidates
        ):
            # has error
            return

    for humanoid_name in HumanBoneSpecifications.required_names:
        if not any(
            human_bone.bone == humanoid_name and human_bone.node.bone_name
            for human_bone in human_bones
        ):
            # has error
            return

    with AbstractBaseVrmImporter.save_bone_child_object_transforms(
        context, armature
    ) as armature_data:
        bone_name_to_human_bone_name: dict[str, HumanBoneName] = {}
        for human_bone in human_bones:
            if not human_bone.node.bone_name:
                continue
            name = HumanBoneName.from_str(human_bone.bone)
            if not name:
                continue
            bone_name_to_human_bone_name[human_bone.node.bone_name] = name

        for bone_name in bone_name_to_human_bone_name:
            bone = armature_data.edit_bones.get(bone_name)
            while bone:
                bone.roll = 0.0
                bone = bone.parent

        for (
            bone_name,
            human_bone_name,
        ) in bone_name_to_human_bone_name.items():
            # 現在のアルゴリズムでは
            #
            #   head ---- node ---- leftEye
            #                   \
            #                    -- rightEye
            #
            # を上手く扱えないので、leftEyeとrightEyeは処理しない
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
                parent_human_bone_name = bone_name_to_human_bone_name.get(parent.name)

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

                if (parent.head - bone.head).length >= make_armature.MIN_BONE_LENGTH:
                    parent.tail = bone.head

                bone = parent

        human_bone_name_to_human_bone: dict[
            HumanBoneName, Vrm0HumanoidBonePropertyGroup
        ] = {}
        for human_bone in human_bones:
            n = HumanBoneName.from_str(human_bone.bone)
            if not n:
                continue
            human_bone_name_to_human_bone[n] = human_bone

        # 目と頭のボーン以外のVRM Humanoidの先端のボーンに子が複数存在する場合
        # 親と同じ方向に向ける。これでデフォルトよりも自然な方向になる。
        # VRM制作者による方向指定かもしれないので、子が一つの場合は何もしない。
        for tip_bone_name in [
            HumanBoneName.JAW,
            HumanBoneName.LEFT_THUMB_DISTAL,
            HumanBoneName.LEFT_INDEX_DISTAL,
            HumanBoneName.LEFT_MIDDLE_DISTAL,
            HumanBoneName.LEFT_RING_DISTAL,
            HumanBoneName.LEFT_LITTLE_DISTAL,
            HumanBoneName.RIGHT_THUMB_DISTAL,
            HumanBoneName.RIGHT_INDEX_DISTAL,
            HumanBoneName.RIGHT_MIDDLE_DISTAL,
            HumanBoneName.RIGHT_RING_DISTAL,
            HumanBoneName.RIGHT_LITTLE_DISTAL,
            HumanBoneName.LEFT_TOES,
            HumanBoneName.RIGHT_TOES,
        ]:
            bone = None
            searching_tip_bone_name: Optional[HumanBoneName] = tip_bone_name
            while searching_tip_bone_name:
                # 該当するボーンがあったらbreak
                human_bone = human_bone_name_to_human_bone.get(searching_tip_bone_name)
                if human_bone:
                    bone = armature_data.edit_bones.get(human_bone.node.bone_name)
                    if bone:
                        break

                # 該当するボーンが無く、必須ボーンだった場合はデータのエラーのため中断
                specification = HumanBoneSpecifications.get(searching_tip_bone_name)
                if specification.requirement:
                    break
                parent_specification = specification.parent()
                if not parent_specification:
                    logger.error(
                        'logic error: "%s" has no parent', searching_tip_bone_name
                    )
                    break

                # 親の子孫に割り当て済みのボーンがある場合は何もしない
                assigned_parent_descendant_found = False
                for parent_descendant in parent_specification.descendants():
                    parent_descendant_human_bone = human_bone_name_to_human_bone.get(
                        parent_descendant.name
                    )
                    if not parent_descendant_human_bone:
                        continue
                    if (
                        parent_descendant_human_bone.node.bone_name
                        in armature_data.edit_bones
                    ):
                        assigned_parent_descendant_found = True
                        break
                if assigned_parent_descendant_found:
                    break

                searching_tip_bone_name = specification.parent_name
            if not bone:
                continue
            if len(bone.children) <= 1:
                continue

            parent_bone = bone.parent
            if not parent_bone:
                continue

            bone.roll = parent_bone.roll
            bone.tail = bone.head + parent_bone.vector / 2

        # 目のボーンに子が無いか複数存在する場合、正面に向ける。
        # これでデフォルトよりも自然な方向になる。
        # VRM制作者による方向指定かもしれないので、子が一つの場合は何もしない。
        for eye_human_bone in [
            human_bone_name_to_human_bone.get(HumanBoneName.LEFT_EYE),
            human_bone_name_to_human_bone.get(HumanBoneName.RIGHT_EYE),
        ]:
            if not eye_human_bone or not eye_human_bone.node.bone_name:
                continue

            bone = armature_data.edit_bones.get(eye_human_bone.node.bone_name)
            if not bone:
                continue
            if len(bone.children) == 1:
                continue

            world_head = (
                armature.matrix_world @ Matrix.Translation(bone.head)
            ).to_translation()

            world_tail = list(world_head)
            world_tail[1] -= 0.03125

            world_inv = armature.matrix_world.inverted()
            if not world_inv:
                continue
            bone.tail = (Matrix.Translation(world_tail) @ world_inv).to_translation()

        # 頭のボーンに子が無いか複数存在する場合、上に向ける。
        # これでデフォルトよりも自然な方向になる。
        # VRM制作者による方向指定かもしれないので、子が一つの場合は何もしない。
        for head_human_bone in [human_bone_name_to_human_bone.get(HumanBoneName.HEAD)]:
            if not head_human_bone or not head_human_bone.node.bone_name:
                continue

            bone = armature_data.edit_bones.get(head_human_bone.node.bone_name)
            if not bone:
                continue
            if len(bone.children) == 1:
                continue

            world_head = (
                armature.matrix_world @ Matrix.Translation(bone.head)
            ).to_translation()

            world_tail = list(world_head)

            parent_bone = bone.parent
            world_tail[2] += parent_bone.length if parent_bone else 0.2

            world_inv = armature.matrix_world.inverted()
            if not world_inv:
                continue

            parent_bone = bone.parent
            if parent_bone:
                bone.roll = parent_bone.roll
            bone.tail = (Matrix.Translation(world_tail) @ world_inv).to_translation()

        connect_parent_tail_and_child_head_if_very_close_position(armature_data)
