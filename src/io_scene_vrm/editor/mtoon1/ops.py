# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import math
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from pathlib import Path
from sys import float_info
from typing import TYPE_CHECKING, Optional

import bpy
from bpy.app.translations import pgettext
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import (
    Context,
    Event,
    Material,
    Mesh,
    Node,
    NodesModifier,
    Object,
    Operator,
    ShaderNodeMapping,
)
from bpy_extras.io_utils import ImportHelper
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper

from ...common import convert, shader
from ...common.logger import get_logger
from ...common.preferences import get_preferences
from .. import search
from ..extension import get_material_extension
from .property_group import (
    Mtoon0ReceiveShadowTexturePropertyGroup,
    Mtoon0ShadingGradeTexturePropertyGroup,
    Mtoon1BaseColorTexturePropertyGroup,
    Mtoon1EmissiveTexturePropertyGroup,
    Mtoon1MatcapTexturePropertyGroup,
    Mtoon1MaterialPropertyGroup,
    Mtoon1NormalTexturePropertyGroup,
    Mtoon1OutlineWidthMultiplyTexturePropertyGroup,
    Mtoon1RimMultiplyTexturePropertyGroup,
    Mtoon1SamplerPropertyGroup,
    Mtoon1ShadeMultiplyTexturePropertyGroup,
    Mtoon1ShadingShiftTexturePropertyGroup,
    Mtoon1TextureInfoPropertyGroup,
    Mtoon1UvAnimationMaskTexturePropertyGroup,
    reset_shader_node_group,
)

logger = get_logger(__name__)


class VRM_OT_convert_material_to_mtoon1(Operator):
    bl_idname = "vrm.convert_material_to_mtoon1"
    bl_label = "Convert Material to MToon 1.0"
    bl_description = "Convert Material to MToon 1.0"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    material_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )

    def execute(self, context: Context) -> set[str]:
        material = context.blend_data.materials.get(self.material_name)
        if not isinstance(material, Material):
            return {"CANCELLED"}
        self.convert_material_to_mtoon1(context, material)
        return {"FINISHED"}

    @staticmethod
    def assign_mtoon_unversioned_image(
        context: Context,
        texture_info: Mtoon1TextureInfoPropertyGroup,
        image_name_and_sampler_type: Optional[tuple[str, int, int]],
        uv_offset: tuple[float, float],
        uv_scale: tuple[float, float],
    ) -> None:
        texture_info.extensions.khr_texture_transform.offset = uv_offset
        texture_info.extensions.khr_texture_transform.scale = uv_scale

        if image_name_and_sampler_type is None:
            return

        image_name, wrap_number, filter_number = image_name_and_sampler_type
        image = context.blend_data.images.get(image_name)
        if not image:
            return

        texture_info.index.source = image

        texture_info.index.sampler.mag_filter = (
            Mtoon1SamplerPropertyGroup.mag_filter_enum.value_to_identifier(
                filter_number, Mtoon1SamplerPropertyGroup.MAG_FILTER_DEFAULT.identifier
            )
        )

        texture_info.index.sampler.min_filter = (
            Mtoon1SamplerPropertyGroup.min_filter_enum.value_to_identifier(
                filter_number, Mtoon1SamplerPropertyGroup.MIN_FILTER_DEFAULT.identifier
            )
        )

        wrap = Mtoon1SamplerPropertyGroup.wrap_enum.value_to_identifier(
            wrap_number, Mtoon1SamplerPropertyGroup.WRAP_DEFAULT.identifier
        )
        texture_info.index.sampler.wrap_s = wrap
        texture_info.index.sampler.wrap_t = wrap

    def convert_material_to_mtoon1(self, context: Context, material: Material) -> None:
        node, legacy_shader_name = search.legacy_shader_node(material)
        if isinstance(node, Node) and legacy_shader_name == "MToon_unversioned":
            self.convert_mtoon_unversioned_to_mtoon1(context, material, node)
            return

        principled_bsdf = PrincipledBSDFWrapper(material)
        if not principled_bsdf.node_principled_bsdf:
            reset_shader_node_group(
                context,
                material,
                reset_material_node_tree=True,
                reset_node_groups=False,
            )
            return

        base_color_factor = (
            principled_bsdf.base_color[0],
            principled_bsdf.base_color[1],
            principled_bsdf.base_color[2],
            principled_bsdf.alpha,
        )
        base_color_texture_node = principled_bsdf.base_color_texture
        if base_color_texture_node:
            base_color_texture_image = base_color_texture_node.image
        else:
            base_color_texture_image = None

        emissive_factor = principled_bsdf.emission_color
        emission_color_texture_node = principled_bsdf.emission_color_texture
        if emission_color_texture_node:
            emissive_texture_image = emission_color_texture_node.image
        else:
            emissive_texture_image = None
        emissive_strength = principled_bsdf.emission_strength

        normalmap_texture_node = principled_bsdf.normalmap_texture
        if normalmap_texture_node:
            normal_texture_image = normalmap_texture_node.image
            normal_texture_scale = principled_bsdf.normalmap_strength
        else:
            normal_texture_image = None
            normal_texture_scale = None

        reset_shader_node_group(
            context,
            material,
            reset_material_node_tree=True,
            reset_node_groups=False,
        )

        gltf = get_material_extension(material).mtoon1
        gltf.pbr_metallic_roughness.base_color_factor = base_color_factor
        if base_color_texture_image:
            gltf.pbr_metallic_roughness.base_color_texture.index.source = (
                base_color_texture_image
            )

        gltf.emissive_factor = emissive_factor
        gltf.extensions.khr_materials_emissive_strength.emissive_strength = (
            emissive_strength
        )
        if emissive_texture_image:
            gltf.emissive_texture.index.source = emissive_texture_image

        if normal_texture_image:
            gltf.normal_texture.index.source = normal_texture_image
        if normal_texture_scale is not None:
            gltf.normal_texture.scale = normal_texture_scale

    def convert_mtoon_unversioned_to_mtoon1(
        self,
        context: Context,
        material: Material,
        node: Node,
    ) -> None:
        transparent_with_z_write = False
        alpha_cutoff: Optional[float] = 0.5
        if material.blend_method == "OPAQUE":
            alpha_mode = Mtoon1MaterialPropertyGroup.ALPHA_MODE_OPAQUE.identifier
        elif material.blend_method == "CLIP":
            alpha_cutoff = shader.get_float_value(node, "CutoffRate", 0, float_info.max)
            if alpha_cutoff is None:
                alpha_cutoff = 0.5
            alpha_mode = Mtoon1MaterialPropertyGroup.ALPHA_MODE_MASK.identifier
        else:
            alpha_mode = Mtoon1MaterialPropertyGroup.ALPHA_MODE_BLEND.identifier
            transparent_with_z_write_float = shader.get_float_value(
                node, "TransparentWithZWrite"
            )
            transparent_with_z_write = (
                transparent_with_z_write_float is not None
                and math.fabs(transparent_with_z_write_float) >= float_info.epsilon
            )

        base_color_factor = shader.get_rgba_value(node, "DiffuseColor", 0.0, 1.0) or (
            0,
            0,
            0,
            1,
        )
        base_color_texture = shader.get_image_name_and_sampler_type(
            node,
            "MainTexture",
        )

        uv_offset = (0.0, 0.0)
        uv_scale = (1.0, 1.0)

        main_texture_socket = node.inputs.get("MainTexture")
        if (
            main_texture_socket
            and main_texture_socket.links
            and main_texture_socket.links[0]
            and main_texture_socket.links[0].from_node
            and main_texture_socket.links[0].from_node.inputs
            and main_texture_socket.links[0].from_node.inputs[0]
            and main_texture_socket.links[0].from_node.inputs[0].links
            and main_texture_socket.links[0].from_node.inputs[0].links[0]
            and main_texture_socket.links[0].from_node.inputs[0].links[0].from_node
        ):
            mapping_node = (
                main_texture_socket.links[0].from_node.inputs[0].links[0].from_node
            )
            if isinstance(mapping_node, ShaderNodeMapping):
                location_socket = mapping_node.inputs.get("Location")
                if location_socket and isinstance(
                    location_socket, shader.VECTOR_SOCKET_CLASSES
                ):
                    uv_offset = (
                        float(location_socket.default_value[0]),
                        float(location_socket.default_value[1]),
                    )

                scale_socket = mapping_node.inputs.get("Scale")
                if scale_socket and isinstance(
                    scale_socket, shader.VECTOR_SOCKET_CLASSES
                ):
                    uv_scale = (
                        float(scale_socket.default_value[0]),
                        float(scale_socket.default_value[1]),
                    )

        shade_color_factor = shader.get_rgb_value(node, "ShadeColor", 0.0, 1.0) or (
            0,
            0,
            0,
        )
        shade_multiply_texture = shader.get_image_name_and_sampler_type(
            node,
            "ShadeTexture",
        )
        normal_texture = shader.get_image_name_and_sampler_type(
            node,
            "NormalmapTexture",
        )
        if not normal_texture:
            normal_texture = shader.get_image_name_and_sampler_type(
                node,
                "NomalmapTexture",
            )
        normal_texture_scale = shader.get_float_value(node, "BumpScale")

        shading_shift_0x = shader.get_float_value(node, "ShadeShift")
        if shading_shift_0x is None:
            shading_shift_0x = 0.0

        shading_toony_0x = shader.get_float_value(node, "ShadeToony")
        if shading_toony_0x is None:
            shading_toony_0x = 0.0

        shading_shift_factor = convert.mtoon_shading_shift_0_to_1(
            shading_toony_0x, shading_shift_0x
        )

        shading_toony_factor = convert.mtoon_shading_toony_0_to_1(
            shading_toony_0x, shading_shift_0x
        )

        gi_equalization_0x = shader.get_float_value(node, "IndirectLightIntensity")
        gi_equalization_factor = None
        if gi_equalization_0x is not None:
            gi_equalization_factor = convert.mtoon_intensity_to_gi_equalization(
                gi_equalization_0x
            )

        emissive_factor = shader.get_rgb_value(node, "EmissionColor", 0.0, 1.0) or (
            0,
            0,
            0,
        )
        emissive_texture = shader.get_image_name_and_sampler_type(
            node,
            "Emission_Texture",
        )
        matcap_texture = shader.get_image_name_and_sampler_type(
            node,
            "SphereAddTexture",
        )

        parametric_rim_color_factor = shader.get_rgb_value(node, "RimColor", 0.0, 1.0)
        parametric_rim_fresnel_power_factor = shader.get_float_value(
            node, "RimFresnelPower", 0.0, float_info.max
        )
        parametric_rim_lift_factor = shader.get_float_value(node, "RimLift")

        rim_multiply_texture = shader.get_image_name_and_sampler_type(
            node,
            "RimTexture",
        )

        centimeter_to_meter = 0.01
        one_hundredth = 0.01

        outline_width_mode_float = shader.get_float_value(node, "OutlineWidthMode")
        outline_width = shader.get_float_value(node, "OutlineWidth")
        if outline_width is None:
            outline_width = 0.0
        outline_width_multiply_texture = shader.get_image_name_and_sampler_type(
            node,
            "OutlineWidthTexture",
        )

        outline_color_factor = shader.get_rgb_value(node, "OutlineColor", 0.0, 1.0) or (
            0,
            0,
            0,
        )

        outline_color_mode = shader.get_float_value(node, "OutlineColorMode")
        if outline_color_mode is not None:
            outline_color_mode = int(round(outline_color_mode))
        else:
            outline_color_mode = 0

        outline_lighting_mix_factor = 0.0
        if outline_color_mode == 1:
            outline_lighting_mix_factor = (
                shader.get_float_value(node, "OutlineLightingMix") or 1.0
            )

        uv_animation_mask_texture = shader.get_image_name_and_sampler_type(
            node,
            "UV_Animation_Mask_Texture",
        )
        uv_animation_rotation_speed_factor = shader.get_float_value(
            node, "UV_Scroll_Rotation"
        )
        uv_animation_scroll_x_speed_factor = shader.get_float_value(node, "UV_Scroll_X")
        uv_animation_scroll_y_speed_factor = shader.get_float_value(node, "UV_Scroll_Y")
        if isinstance(uv_animation_scroll_y_speed_factor, float):
            uv_animation_scroll_y_speed_factor *= -1

        shader.load_mtoon1_shader(context, material, reset_node_groups=True)

        gltf = get_material_extension(material).mtoon1
        mtoon = gltf.extensions.vrmc_materials_mtoon

        gltf.alpha_mode = alpha_mode
        gltf.alpha_cutoff = alpha_cutoff
        mtoon.transparent_with_z_write = transparent_with_z_write
        gltf.pbr_metallic_roughness.base_color_factor = base_color_factor
        self.assign_mtoon_unversioned_image(
            context,
            gltf.pbr_metallic_roughness.base_color_texture,
            base_color_texture,
            uv_offset,
            uv_scale,
        )
        mtoon.shade_color_factor = shade_color_factor
        self.assign_mtoon_unversioned_image(
            context,
            mtoon.shade_multiply_texture,
            shade_multiply_texture,
            uv_offset,
            uv_scale,
        )
        self.assign_mtoon_unversioned_image(
            context,
            gltf.normal_texture,
            normal_texture,
            uv_offset,
            uv_scale,
        )
        if normal_texture_scale is not None:
            gltf.normal_texture.scale = normal_texture_scale

        mtoon.shading_shift_factor = shading_shift_factor
        mtoon.shading_toony_factor = shading_toony_factor

        if gi_equalization_factor is not None:
            mtoon.gi_equalization_factor = gi_equalization_factor

        gltf.emissive_factor = emissive_factor
        self.assign_mtoon_unversioned_image(
            context,
            gltf.emissive_texture,
            emissive_texture,
            uv_offset,
            uv_scale,
        )
        self.assign_mtoon_unversioned_image(
            context,
            mtoon.matcap_texture,
            matcap_texture,
            (0, 0),
            (1, 1),
        )

        if parametric_rim_color_factor is not None:
            mtoon.parametric_rim_color_factor = parametric_rim_color_factor
        if parametric_rim_fresnel_power_factor is not None:
            mtoon.parametric_rim_fresnel_power_factor = (
                parametric_rim_fresnel_power_factor
            )
        if parametric_rim_lift_factor is not None:
            mtoon.parametric_rim_lift_factor = parametric_rim_lift_factor

        self.assign_mtoon_unversioned_image(
            context,
            mtoon.rim_multiply_texture,
            rim_multiply_texture,
            uv_offset,
            uv_scale,
        )

        # https://github.com/vrm-c/UniVRM/blob/7c9919ef47a25c04100a2dcbe6a75dff49ef4857/Assets/VRM10/Runtime/Migration/Materials/MigrationMToonMaterial.cs#L287-L290
        mtoon.rim_lighting_mix_factor = 1.0

        centimeter_to_meter = 0.01
        one_hundredth = 0.01

        mtoon.enable_outline_preview = get_preferences(
            context
        ).enable_mtoon_outline_preview

        if outline_width_mode_float is not None:
            outline_width_mode = int(round(outline_width_mode_float))
        else:
            outline_width_mode = 0

        if outline_width_mode == 1:
            mtoon.outline_width_mode = (
                mtoon.OUTLINE_WIDTH_MODE_WORLD_COORDINATES.identifier
            )
            mtoon.outline_width_factor = max(0.0, outline_width * centimeter_to_meter)
        elif outline_width_mode == 2:
            mtoon.outline_width_mode = (
                mtoon.OUTLINE_WIDTH_MODE_SCREEN_COORDINATES.identifier
            )
            mtoon.outline_width_factor = max(0.0, outline_width * one_hundredth * 0.5)
        else:
            mtoon.outline_width_mode = mtoon.OUTLINE_WIDTH_MODE_NONE.identifier

        self.assign_mtoon_unversioned_image(
            context,
            mtoon.outline_width_multiply_texture,
            outline_width_multiply_texture,
            uv_offset,
            uv_scale,
        )

        mtoon.outline_color_factor = outline_color_factor
        mtoon.outline_lighting_mix_factor = 0.0
        if outline_color_mode == 1:
            mtoon.outline_lighting_mix_factor = outline_lighting_mix_factor

        self.assign_mtoon_unversioned_image(
            context,
            mtoon.uv_animation_mask_texture,
            uv_animation_mask_texture,
            uv_offset,
            uv_scale,
        )

        if uv_animation_rotation_speed_factor is not None:
            mtoon.uv_animation_rotation_speed_factor = (
                uv_animation_rotation_speed_factor
            )
        if uv_animation_scroll_x_speed_factor is not None:
            mtoon.uv_animation_scroll_x_speed_factor = (
                uv_animation_scroll_x_speed_factor
            )
        if uv_animation_scroll_y_speed_factor is not None:
            mtoon.uv_animation_scroll_y_speed_factor = (
                uv_animation_scroll_y_speed_factor
            )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        material_name: str  # type: ignore[no-redef]


class VRM_OT_convert_mtoon1_to_bsdf_principled(Operator):
    bl_idname = "vrm.convert_mtoon1_to_bsdf_principled"
    bl_label = "Convert MToon 1.0 to Principled BSDF"
    bl_description = "Convert MToon 1.0 to Principled BSDF"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    material_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )

    def execute(self, context: Context) -> set[str]:
        material = context.blend_data.materials.get(self.material_name)
        if not isinstance(material, Material):
            return {"CANCELLED"}
        self.convert_mtoon1_to_bsdf_principled(material)
        return {"FINISHED"}

    def convert_mtoon1_to_bsdf_principled(self, material: Material) -> None:
        if not material.use_nodes:
            material.use_nodes = True
        shader.clear_node_tree(material.node_tree, clear_inputs_outputs=True)
        if not material.node_tree:
            logger.error("%s's node tree is None", material.name)
            return

        principled_bsdf = PrincipledBSDFWrapper(material, is_readonly=False)
        gltf = get_material_extension(material).mtoon1

        principled_bsdf.base_color = gltf.pbr_metallic_roughness.base_color_factor[:3]
        base_color_texture_image = (
            gltf.pbr_metallic_roughness.base_color_texture.index.source
        )
        if base_color_texture_image:
            base_color_texture_node = principled_bsdf.base_color_texture
            if base_color_texture_node:
                base_color_texture_node.image = base_color_texture_image

        principled_bsdf.alpha = gltf.pbr_metallic_roughness.base_color_factor[3]

        principled_bsdf.emission_color = list(gltf.emissive_factor)
        principled_bsdf.emission_strength = (
            gltf.extensions.khr_materials_emissive_strength.emissive_strength
        )
        emissive_texture_image = gltf.emissive_texture.index.source
        if emissive_texture_image:
            emission_color_texture_node = principled_bsdf.emission_color_texture
            if emission_color_texture_node:
                emission_color_texture_node.image = emissive_texture_image

        normal_texture_image = gltf.normal_texture.index.source
        if normal_texture_image:
            normalmap_texture_node = principled_bsdf.normalmap_texture
            if normalmap_texture_node:
                normalmap_texture_node.image = normal_texture_image
        normal_scale = gltf.normal_texture.scale
        if abs(normal_scale - 1) >= float_info.epsilon:
            principled_bsdf.normalmap_strength = gltf.normal_texture.scale

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        material_name: str  # type: ignore[no-redef]


class VRM_OT_reset_mtoon1_material_shader_node_tree(Operator):
    bl_idname = "vrm.reset_mtoon1_material_shader_node_group"
    bl_label = "Reset Shader Nodes"
    bl_description = "Reset MToon 1.0 Material Shader Node Tree"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    material_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )

    def execute(self, context: Context) -> set[str]:
        material = context.blend_data.materials.get(self.material_name)
        if not isinstance(material, Material):
            return {"CANCELLED"}
        reset_shader_node_group(
            context, material, reset_material_node_tree=True, reset_node_groups=True
        )
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        material_name: str  # type: ignore[no-redef]


class VRM_OT_import_mtoon1_texture_image_file(Operator, ImportHelper):
    bl_idname = "vrm.import_mtoon1_texture_image_file"
    bl_label = "Open"
    bl_description = "Import Texture Image File"
    bl_options: AbstractSet[str] = {"REGISTER", "UNDO"}

    filepath: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        default="",
    )

    filter_glob: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        # https://docs.blender.org/api/2.83/Image.html#Image.file_format
        default=(
            "*.bmp"
            ";*.sgi"
            ";*.bw"
            ";*.rgb"
            ";*.rgba"
            ";*.png"
            ";*.jpg"
            ";*.jpeg"
            ";*.jp2"
            ";*.tga"
            ";*.cin"
            ";*.dpx"
            ";*.exr"
            ";*.hdr"
            ";*.tif"
            ";*.tiff"
        ),
    )

    material_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
    )

    target_texture_items = (
        (Mtoon1BaseColorTexturePropertyGroup.__name__, "", "", "NONE", 0),
        (Mtoon1ShadeMultiplyTexturePropertyGroup.__name__, "", "", "NONE", 1),
        (Mtoon1NormalTexturePropertyGroup.__name__, "", "", "NONE", 2),
        (Mtoon1ShadingShiftTexturePropertyGroup.__name__, "", "", "NONE", 3),
        (Mtoon1EmissiveTexturePropertyGroup.__name__, "", "", "NONE", 4),
        (Mtoon1RimMultiplyTexturePropertyGroup.__name__, "", "", "NONE", 5),
        (Mtoon1MatcapTexturePropertyGroup.__name__, "", "", "NONE", 6),
        (
            Mtoon1OutlineWidthMultiplyTexturePropertyGroup.__name__,
            "",
            "",
            "NONE",
            7,
        ),
        (Mtoon1UvAnimationMaskTexturePropertyGroup.__name__, "", "", "NONE", 8),
        (Mtoon0ReceiveShadowTexturePropertyGroup.__name__, "", "", "NONE", 9),
        (Mtoon0ShadingGradeTexturePropertyGroup.__name__, "", "", "NONE", 10),
    )

    target_texture: EnumProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        items=target_texture_items,
        name="Target Texture",
    )

    def execute(self, context: Context) -> set[str]:
        filepath = self.filepath
        if not filepath or not Path(filepath).exists():
            return {"CANCELLED"}

        last_images_len = len(context.blend_data.images)
        image = context.blend_data.images.load(filepath, check_existing=True)
        created = last_images_len < len(context.blend_data.images)

        material = context.blend_data.materials.get(self.material_name)
        if not isinstance(material, Material):
            return {"FINISHED"}

        gltf = get_material_extension(material).mtoon1
        mtoon = gltf.extensions.vrmc_materials_mtoon

        for texture in [
            gltf.pbr_metallic_roughness.base_color_texture.index,
            mtoon.shade_multiply_texture.index,
            gltf.normal_texture.index,
            mtoon.shading_shift_texture.index,
            gltf.emissive_texture.index,
            mtoon.rim_multiply_texture.index,
            mtoon.matcap_texture.index,
            mtoon.outline_width_multiply_texture.index,
            mtoon.uv_animation_mask_texture.index,
            gltf.mtoon0_receive_shadow_texture,
            gltf.mtoon0_shading_grade_texture,
        ]:
            if self.target_texture != type(texture).__name__:
                continue
            texture.source = image
            if created:
                image.colorspace_settings.name = type(texture).colorspace
            return {"FINISHED"}

        return {"CANCELLED"}

    def invoke(self, context: Context, event: Event) -> set[str]:
        self.filepath = ""
        return ImportHelper.invoke(self, context, event)

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        filepath: str  # type: ignore[no-redef]
        filter_glob: str  # type: ignore[no-redef]
        material_name: str  # type: ignore[no-redef]
        target_texture: str  # type: ignore[no-redef]


@dataclass(frozen=True)
class NodesModifierInputKey:
    geometry_key: str
    material_key: str
    outline_material_key: str
    outline_width_mode_key: str
    outline_width_factor_key: str
    outline_width_multiply_texture_key: str
    outline_width_multiply_texture_exists_key: str
    outline_width_multiply_texture_uv_key: str
    outline_width_multiply_texture_uv_offset_x_key: str
    outline_width_multiply_texture_uv_offset_y_key: str
    outline_width_multiply_texture_uv_scale_x_key: str
    outline_width_multiply_texture_uv_scale_y_key: str
    extrude_mesh_individual_key: str
    object_key: str
    enabled_key: str

    @staticmethod
    def keys_len() -> int:
        return 15

    def outline_width_multiply_texture_uv_use_attribute_key(self) -> str:
        return self.outline_width_multiply_texture_uv_key + "_use_attribute"

    def outline_width_multiply_texture_uv_attribute_name_key(self) -> str:
        return self.outline_width_multiply_texture_uv_key + "_attribute_name"


def get_nodes_modifier_input_key(
    modifier: NodesModifier,
) -> Optional[NodesModifierInputKey]:
    node_group = modifier.node_group
    if not node_group:
        return None
    if bpy.app.version < (4, 0):
        keys = [i.identifier for i in node_group.inputs]
    else:
        from bpy.types import NodeTreeInterfaceSocket

        keys = [
            item.identifier
            for item in node_group.interface.items_tree
            if item.item_type == "SOCKET"
            and isinstance(item, NodeTreeInterfaceSocket)
            and item.in_out == "INPUT"
        ]
    keys_len = NodesModifierInputKey.keys_len()
    if len(keys) < keys_len:
        return None
    return NodesModifierInputKey(*keys[:keys_len])


class VRM_OT_refresh_mtoon1_outline(Operator):
    bl_idname = "vrm.refresh_mtoon1_outline"
    bl_label = "Refresh MToon 1.0 Outline Width Mode"
    bl_description = "Import Texture Image File"
    bl_options: AbstractSet[str] = {"UNDO"}

    material_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    create_modifier: BoolProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )

    @staticmethod
    def assign(
        context: Context,
        material: Material,
        obj: Object,
        *,
        create_modifier: bool,
    ) -> None:
        shader.load_mtoon1_outline_geometry_node_group(context, reset_node_groups=False)
        node_group = context.blend_data.node_groups.get(
            shader.OUTLINE_GEOMETRY_GROUP_NAME
        )
        if not node_group:
            return
        mtoon = get_material_extension(material).mtoon1.extensions.vrmc_materials_mtoon
        outline_width_mode_value = mtoon.outline_width_mode_enum.identifier_to_value(
            mtoon.outline_width_mode,
            mtoon.OUTLINE_WIDTH_MODE_NONE.value,
        )
        no_outline = (
            not mtoon.enable_outline_preview
            or outline_width_mode_value == mtoon.OUTLINE_WIDTH_MODE_NONE.value
            or mtoon.outline_width_factor < float_info.epsilon
        )
        cleanup = no_outline
        modifier = None

        for search_modifier_name in list(obj.modifiers.keys()):
            search_modifier = obj.modifiers.get(search_modifier_name)
            if not search_modifier:
                continue
            if search_modifier.type != "NODES":
                continue
            if not isinstance(search_modifier, NodesModifier):
                continue
            if not search_modifier.node_group:
                continue
            if search_modifier.node_group.name != shader.OUTLINE_GEOMETRY_GROUP_NAME:
                continue
            input_key = get_nodes_modifier_input_key(search_modifier)
            if input_key is None:
                continue
            search_material = search_modifier.get(input_key.material_key)
            if not isinstance(search_material, Material):
                continue
            if search_material.name != material.name:
                continue
            if cleanup:
                obj.modifiers.remove(search_modifier)
                continue
            modifier = search_modifier
            cleanup = True

        if no_outline:
            return

        if not modifier and not create_modifier:
            mtoon.outline_width_mode = mtoon.OUTLINE_WIDTH_MODE_NONE.identifier
            return

        outline_material_name = f"MToon Outline ({material.name})"
        modifier_name = f"MToon Outline ({material.name})"

        outline_material = get_material_extension(material).mtoon1.outline_material
        reset_outline_material = not outline_material
        if reset_outline_material:
            outline_material = context.blend_data.materials.new(
                name=outline_material_name
            )
            if not outline_material.use_nodes:
                outline_material.use_nodes = True
            if outline_material.diffuse_color[3] != 0.25:
                outline_material.diffuse_color[3] = 0.25
            if outline_material.roughness != 0:
                outline_material.roughness = 0
            shader.load_mtoon1_shader(
                context, outline_material, reset_node_groups=False
            )
            get_material_extension(outline_material).mtoon1.is_outline_material = True
            get_material_extension(material).mtoon1.outline_material = outline_material
        if outline_material.name != outline_material_name:
            outline_material.name = outline_material_name
        if not outline_material.use_nodes:
            outline_material.use_nodes = True
        if not get_material_extension(outline_material).mtoon1.is_outline_material:
            get_material_extension(outline_material).mtoon1.is_outline_material = True
        if (
            get_material_extension(outline_material).mtoon1.alpha_cutoff
            != get_material_extension(material).mtoon1.alpha_cutoff
        ):
            get_material_extension(
                outline_material
            ).mtoon1.alpha_cutoff = get_material_extension(material).mtoon1.alpha_cutoff
        if (
            get_material_extension(outline_material).mtoon1.alpha_mode
            != get_material_extension(material).mtoon1.alpha_mode
        ):
            get_material_extension(
                outline_material
            ).mtoon1.alpha_mode = get_material_extension(material).mtoon1.alpha_mode
        if bpy.app.version < (4, 3) and outline_material.shadow_method != "NONE":
            outline_material.shadow_method = "NONE"
        if not outline_material.use_backface_culling:
            outline_material.use_backface_culling = True
        if outline_material.show_transparent_back:
            outline_material.show_transparent_back = False

        if not modifier:
            new_modifier = obj.modifiers.new(modifier_name, "NODES")
            if not isinstance(new_modifier, NodesModifier):
                message = f"{type(new_modifier)} is not a NodesModifier"
                raise AssertionError(message)
            modifier = new_modifier
            modifier.show_expanded = False
            modifier.show_in_editmode = False

        if modifier.name != modifier_name:
            modifier.name = modifier_name
        if modifier.node_group != node_group:
            modifier.node_group = node_group

        input_key = get_nodes_modifier_input_key(modifier)
        if input_key is None:
            return

        modifier_input_changed = False

        (
            outline_width_multiply_texture_uv_offset_x,
            outline_width_multiply_texture_uv_offset_y,
        ) = mtoon.outline_width_multiply_texture.extensions.khr_texture_transform.offset
        (
            outline_width_multiply_texture_uv_scale_x,
            outline_width_multiply_texture_uv_scale_y,
        ) = mtoon.outline_width_multiply_texture.extensions.khr_texture_transform.scale

        uv_layer_name = None
        if isinstance(obj.data, Mesh):
            uv_layer_name = next(
                (
                    uv_layer.name
                    for uv_layer in obj.data.uv_layers
                    if uv_layer and uv_layer.active_render
                ),
                None,
            )
        if uv_layer_name is None:
            uv_layer_name = "UVMap"

        has_auto_smooth = tuple(bpy.app.version) < (4, 1)
        for k, v in [
            (input_key.material_key, material),
            (input_key.outline_material_key, outline_material),
            (input_key.outline_width_mode_key, outline_width_mode_value),
            (input_key.outline_width_factor_key, mtoon.outline_width_factor),
            (
                input_key.outline_width_multiply_texture_key,
                mtoon.outline_width_multiply_texture.index.source,
            ),
            (
                input_key.outline_width_multiply_texture_exists_key,
                bool(mtoon.outline_width_multiply_texture.index.source),
            ),
            (input_key.outline_width_multiply_texture_uv_use_attribute_key(), 1),
            (
                input_key.outline_width_multiply_texture_uv_attribute_name_key(),
                uv_layer_name,
            ),
            (
                input_key.outline_width_multiply_texture_uv_offset_x_key,
                outline_width_multiply_texture_uv_offset_x,
            ),
            (
                input_key.outline_width_multiply_texture_uv_offset_y_key,
                outline_width_multiply_texture_uv_offset_y,
            ),
            (
                input_key.outline_width_multiply_texture_uv_scale_x_key,
                outline_width_multiply_texture_uv_scale_x,
            ),
            (
                input_key.outline_width_multiply_texture_uv_scale_y_key,
                outline_width_multiply_texture_uv_scale_y,
            ),
            (
                input_key.extrude_mesh_individual_key,
                (
                    obj.type == "MESH"
                    and isinstance(obj.data, Mesh)
                    and not (has_auto_smooth and obj.data.use_auto_smooth)
                    and not any(polygon.use_smooth for polygon in obj.data.polygons)
                ),
            ),
            (input_key.object_key, obj),
            (
                input_key.enabled_key,
                obj.mode
                not in ["VERTEX_PAINT", "TEXTURE_PAINT", "WEIGHT_PAINT", "SCULPT"],
            ),
        ]:
            if modifier.get(k) != v:
                modifier[k] = v
                modifier_input_changed = True

        # Apply input values
        if modifier_input_changed:
            modifier.show_viewport = not modifier.show_viewport
            modifier.show_viewport = not modifier.show_viewport

        if reset_outline_material:
            reset_shader_node_group(
                context,
                material,
                reset_material_node_tree=False,
                reset_node_groups=False,
            )

    @staticmethod
    def refresh_object(context: Context, obj: Object) -> None:
        if bpy.app.version < (3, 3):
            return
        for material_slot in obj.material_slots:
            material_ref = material_slot.material
            if not material_ref:
                continue

            material = context.blend_data.materials.get(material_ref.name)
            if not material:
                continue

            mtoon1 = get_material_extension(material).mtoon1
            if not mtoon1.enabled or mtoon1.is_outline_material:
                continue

            VRM_OT_refresh_mtoon1_outline.assign(
                context, material, obj, create_modifier=False
            )

    @staticmethod
    def refresh(
        context: Context,
        material_name: Optional[str] = None,
        *,
        create_modifier: bool,
    ) -> None:
        if bpy.app.version < (3, 3):
            return
        for obj in context.blend_data.objects:
            if obj.type != "MESH":
                continue
            outline_material_names: list[str] = []
            for material_slot in obj.material_slots:
                material_ref = material_slot.material
                if not material_ref:
                    continue

                if material_name is not None and material_name != material_ref.name:
                    continue

                material = context.blend_data.materials.get(material_ref.name)
                if not material:
                    continue

                mtoon1 = get_material_extension(material).mtoon1
                if not mtoon1.enabled or mtoon1.is_outline_material:
                    continue

                VRM_OT_refresh_mtoon1_outline.assign(
                    context, material, obj, create_modifier=create_modifier
                )
                outline_material_names.append(material.name)
            if material_name is not None:
                continue

            # Remove unnecessary outline modifiers if no material name is specified.
            for search_modifier_name in list(obj.modifiers.keys()):
                search_modifier = obj.modifiers.get(search_modifier_name)
                if not search_modifier:
                    continue
                if search_modifier.type != "NODES":
                    continue
                if not isinstance(search_modifier, NodesModifier):
                    continue
                node_group = search_modifier.node_group
                if not node_group:
                    continue
                if node_group.name != shader.OUTLINE_GEOMETRY_GROUP_NAME:
                    continue
                input_key = get_nodes_modifier_input_key(search_modifier)
                if input_key is None:
                    continue
                search_material = search_modifier.get(input_key.material_key)
                if (
                    isinstance(search_material, Material)
                    and search_material.name in outline_material_names
                ):
                    continue
                obj.modifiers.remove(search_modifier)

    def execute(self, context: Context) -> set[str]:
        material_name: Optional[str] = self.material_name
        if not material_name:
            material_name = None
        self.refresh(context, material_name, create_modifier=self.create_modifier)
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        material_name: str  # type: ignore[no-redef]
        create_modifier: bool  # type: ignore[no-redef]


class VRM_OT_show_material_blender_4_2_warning(Operator):
    bl_idname = "vrm.show_material_blender_4_2_warning"
    bl_label = "Blender 4.2 Material Upgrade Warning"
    bl_description = "Show Material Blender 4.2 Warning"
    bl_options: AbstractSet[str] = {"REGISTER"}

    material_name_lines: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )

    def execute(self, _context: Context) -> set[str]:
        return {"FINISHED"}

    def invoke(self, context: Context, _event: Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self, width=750)

    def draw(self, _context: Context) -> None:
        column = self.layout.row(align=True).column()
        text = pgettext(
            'Updating to Blender 4.2 may unintentionally change the "{alpha_mode}"'
            + ' of some MToon materials to "{transparent}".\n'
            + 'This was previously implemented using the material\'s "{blend_mode}"'
            + " but since that setting was removed in Blender 4.2.\n"
            + 'In the current VRM add-on, the "{alpha_mode}" function has been'
            + " re-implemented using a different method. However, it\n"
            + "was not possible"
            + " to implement automatic migration of old settings values because those"
            + " values could no longer be read.\n"
            + 'Please check the "{alpha_mode}" settings for materials that have'
            + " MToon enabled.\n"
            + "Materials that may be affected are as follows:"
        ).format(
            blend_mode=pgettext("Blend Mode"),
            alpha_mode=pgettext("Alpha Mode"),
            transparent=pgettext("Transparent"),
        )
        description_outer_column = column.column()
        description_outer_column.emboss = "NONE"
        description_column = description_outer_column.box().column(align=True)
        for i, line in enumerate(text.splitlines()):
            icon = "ERROR" if i == 0 else "NONE"
            description_column.label(text=line, translate=False, icon=icon)
        material_column = column.box().column(align=True)
        for line in self.material_name_lines.splitlines():
            material_column.label(text=line, translate=False, icon="MATERIAL")
        column.separator()

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        material_name_lines: str  # type: ignore[no-redef]
