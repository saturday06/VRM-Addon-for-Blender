# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import functools
from dataclasses import dataclass
from typing import Final, Optional

import bpy
from bpy.types import (
    Context,
    Image,
    Material,
    NodeReroute,
    ShaderNodeGroup,
    ShaderNodeTexImage,
)
from idprop.types import IDPropertyGroup

from ...common import convert, ops, shader, version
from ...common.gl import GL_LINEAR, GL_NEAREST
from ...common.logger import get_logger
from ...common.progress import create_progress
from .. import search
from ..extension import get_material_extension
from .property_group import (
    GL_LINEAR_IMAGE_INTERPOLATIONS,
    IMAGE_INTERPOLATION_CLOSEST,
    IMAGE_INTERPOLATION_LINEAR,
    Mtoon1MaterialPropertyGroup,
    Mtoon1SamplerPropertyGroup,
    Mtoon1TextureInfoPropertyGroup,
    Mtoon1VrmcMaterialsMtoonPropertyGroup,
    reset_shader_node_group,
)

TextureInfoBackup = Mtoon1TextureInfoPropertyGroup.TextureInfoBackup

logger = get_logger(__name__)


@dataclass
class State:
    material_blender_4_2_warning_shown: bool = False


state: Final = State()


def show_material_blender_4_2_warning_delay(material_name_lines: str) -> None:
    ops.vrm.show_material_blender_4_2_warning(
        "INVOKE_DEFAULT",
        material_name_lines=material_name_lines,
    )


def migrate(context: Context, *, show_progress: bool = False) -> None:
    blender_4_2_migrated_material_names: list[str] = []

    with create_progress(context, show_progress=show_progress) as progress:
        for material_index, material in enumerate(context.blend_data.materials):
            if not material:
                continue
            migrate_material(context, material, blender_4_2_migrated_material_names)
            progress.update(float(material_index) / len(context.blend_data.materials))
        progress.update(1)

    if (
        blender_4_2_migrated_material_names
        and tuple(context.blend_data.version) < (4, 2)
        and bpy.app.version >= (4, 2)
    ):
        logger.warning(
            "Migrating Materials from blender version data=%s app=%s",
            context.blend_data.version,
            bpy.app.version,
        )

        if not state.material_blender_4_2_warning_shown:
            state.material_blender_4_2_warning_shown = True
            # Blender 4.2.0ではtimerで実行しないとダイアログが自動で消える
            bpy.app.timers.register(
                functools.partial(
                    show_material_blender_4_2_warning_delay,
                    "\n".join(blender_4_2_migrated_material_names),
                ),
                first_interval=0.1,
            )


def migrate_material(
    context: Context,
    material: Material,
    blender_4_2_migrated_material_names: list[str],
) -> None:
    _, legacy_legacy_shader_name = search.legacy_shader_node(material)
    if legacy_legacy_shader_name in search.LEGACY_SHADER_NAMES:
        # 古いシェーダーノードグループはそのままではBlender 4.2に未対応なので、
        # Blender 4.2以降へのバージョンアップ時は必ず警告する
        blender_4_2_migrated_material_names.append(material.name)
        return

    if not material.use_nodes:
        return
    node_tree = material.node_tree
    if not node_tree:
        return

    vrm_addon_extension = material.get("vrm_addon_extension")
    if not isinstance(vrm_addon_extension, IDPropertyGroup):
        return

    mtoon1 = vrm_addon_extension.get("mtoon1")
    if not isinstance(mtoon1, IDPropertyGroup):
        return

    if not mtoon1.get("enabled"):
        return

    extensions = mtoon1.get("extensions")
    if not isinstance(extensions, IDPropertyGroup):
        return

    vrmc_materials_mtoon = extensions.get("vrmc_materials_mtoon")
    if not isinstance(vrmc_materials_mtoon, IDPropertyGroup):
        return

    if vrmc_materials_mtoon.get("is_outline_material"):
        return

    addon_version = convert.float3_or(mtoon1.get("addon_version"), (0, 0, 0))
    if addon_version < (2, 16, 4):
        # https://github.com/saturday06/VRM-Addon-for-Blender/blob/2_10_0/io_scene_vrm/editor/mtoon1/property_group.py#L1658-L1683
        surface_node_name = "Mtoon1Material.MaterialOutputSurfaceIn"
        surface_node = node_tree.nodes.get(surface_node_name)
        if not isinstance(surface_node, NodeReroute):
            return

        connected = False
        surface_socket = surface_node.outputs[0]
        for link in node_tree.links:
            if (
                link.from_socket == surface_socket
                and link.to_socket
                and link.to_socket.node
                and link.to_socket.node.type == "OUTPUT_MATERIAL"
            ):
                connected = True
                break
        if not connected:
            return
    else:
        # https://github.com/saturday06/VRM-Addon-for-Blender/blob/2_16_4/io_scene_vrm/editor/mtoon1/property_group.py#L1913-L1929
        group_node = node_tree.nodes.get("Mtoon1Material.Mtoon1Output")
        if not isinstance(group_node, ShaderNodeGroup):
            return
        if not group_node.node_tree:
            return
        if group_node.node_tree.name != "VRM Add-on MToon 1.0 Output Revision 1":
            return

    if addon_version < (2, 20, 50):
        migrate_sampler_filter_node(material)

    alpha_mode: Optional[str] = None
    alpha_cutoff: Optional[float] = None
    if addon_version < (2, 20, 55):
        blender_4_2_migrated_material_names.append(material.name)
        alpha_cutoff = material.alpha_threshold
        blend_method = material.blend_method
        if blend_method in ["BLEND", "HASHED"]:
            alpha_mode = Mtoon1MaterialPropertyGroup.ALPHA_MODE_BLEND.identifier
        elif blend_method == "CLIP":
            alpha_mode = Mtoon1MaterialPropertyGroup.ALPHA_MODE_MASK.identifier
        else:
            alpha_mode = Mtoon1MaterialPropertyGroup.ALPHA_MODE_OPAQUE.identifier

    base_color_factor: Optional[tuple[float, float, float, float]] = None
    base_color_texture_backup: Optional[TextureInfoBackup] = None
    normal_texture_backup: Optional[TextureInfoBackup] = None
    normal_texture_scale: Optional[float] = None
    emissive_texture_backup: Optional[TextureInfoBackup] = None
    emissive_factor: Optional[tuple[float, float, float]] = None
    emissive_strength: Optional[float] = None

    transparent_with_z_write: Optional[bool] = None
    render_queue_offset_number: Optional[int] = None
    shade_multiply_texture_backup: Optional[TextureInfoBackup] = None
    shade_color_factor: Optional[tuple[float, float, float]] = None
    shading_shift_texture_backup: Optional[TextureInfoBackup] = None
    shading_shift_texture_scale: Optional[float] = None
    shading_shift_factor: Optional[float] = None
    shading_toony_factor: Optional[float] = None
    gi_equalization_factor: Optional[float] = None
    matcap_factor: Optional[tuple[float, float, float]] = None
    matcap_texture_backup: Optional[TextureInfoBackup] = None
    parametric_rim_color_factor: Optional[tuple[float, float, float]] = None
    rim_multiply_texture_backup: Optional[TextureInfoBackup] = None
    rim_lighting_mix_factor: Optional[float] = None
    parametric_rim_fresnel_power_factor: Optional[float] = None
    parametric_rim_lift_factor: Optional[float] = None
    outline_width_mode: Optional[str] = None
    outline_width_factor: Optional[float] = None
    outline_width_multiply_texture_backup: Optional[TextureInfoBackup] = None
    outline_color_factor: Optional[tuple[float, float, float]] = None
    outline_lighting_mix_factor: Optional[float] = None
    uv_animation_mask_texture_backup: Optional[TextureInfoBackup] = None
    uv_animation_scroll_x_speed_factor: Optional[float] = None
    uv_animation_scroll_y_speed_factor: Optional[float] = None
    uv_animation_rotation_speed_factor: Optional[float] = None
    if addon_version < (2, 20, 62):
        pbr_metallic_roughness = mtoon1.get("pbr_metallic_roughness")
        if isinstance(pbr_metallic_roughness, IDPropertyGroup):
            base_color_factor = convert.float4_or_none(
                pbr_metallic_roughness.get("base_color_factor")
            )
            base_color_texture_backup = backup_texture_info(
                pbr_metallic_roughness.get("base_color_texture")
            )
        normal_texture = mtoon1.get("normal_texture")
        normal_texture_backup = backup_texture_info(normal_texture)
        if isinstance(normal_texture, IDPropertyGroup):
            normal_texture_scale = convert.float_or_none(normal_texture.get("scale"))
        emissive_factor = convert.float3_or_none(mtoon1.get("emissive_factor"))
        emissive_texture_backup = backup_texture_info(mtoon1.get("emissive_texture"))
        khr_materials_emissive_strength = extensions.get(
            "khr_materials_emissive_strength"
        )
        if isinstance(khr_materials_emissive_strength, IDPropertyGroup):
            emissive_strength = convert.float_or_none(
                khr_materials_emissive_strength.get("emissive_strength")
            )

        transparent_with_z_write_object = vrmc_materials_mtoon.get(
            "transparent_with_z_write"
        )
        if isinstance(transparent_with_z_write_object, int):
            transparent_with_z_write = bool(transparent_with_z_write_object)

        render_queue_offset_number_object = vrmc_materials_mtoon.get(
            "render_queue_offset_number"
        )
        if isinstance(render_queue_offset_number_object, int):
            render_queue_offset_number = render_queue_offset_number_object

        shade_multiply_texture_backup = backup_texture_info(
            vrmc_materials_mtoon.get("shade_multiply_texture")
        )
        shade_color_factor = convert.float3_or_none(
            vrmc_materials_mtoon.get("shade_color_factor")
        )

        shading_shift_texture = vrmc_materials_mtoon.get("shading_shift_texture")
        shading_shift_texture_backup = backup_texture_info(shading_shift_texture)
        if isinstance(shading_shift_texture, IDPropertyGroup):
            shading_shift_texture_scale = convert.float_or_none(
                shading_shift_texture.get("scale")
            )

        shading_shift_factor = convert.float_or_none(
            vrmc_materials_mtoon.get("shading_shift_factor")
        )
        shading_toony_factor = convert.float_or_none(
            vrmc_materials_mtoon.get("shading_toony_factor")
        )
        matcap_factor = convert.float3_or_none(
            vrmc_materials_mtoon.get("matcap_factor")
        )
        matcap_texture_backup = backup_texture_info(
            vrmc_materials_mtoon.get("matcap_texture")
        )
        gi_equalization_factor = convert.float_or_none(
            vrmc_materials_mtoon.get("gi_equalization_factor")
        )
        parametric_rim_color_factor = convert.float3_or_none(
            vrmc_materials_mtoon.get("parametric_rim_color_factor")
        )
        rim_multiply_texture_backup = backup_texture_info(
            vrmc_materials_mtoon.get("rim_multiply_texture")
        )
        rim_lighting_mix_factor = convert.float_or_none(
            vrmc_materials_mtoon.get("rim_lighting_mix_factor")
        )
        parametric_rim_fresnel_power_factor = convert.float_or_none(
            vrmc_materials_mtoon.get("parametric_rim_fresnel_power_factor")
        )
        parametric_rim_lift_factor = convert.float_or_none(
            vrmc_materials_mtoon.get("parametric_rim_lift_factor")
        )
        outline_width_mode_number = vrmc_materials_mtoon.get("outline_width_mode")
        if isinstance(outline_width_mode_number, int):
            outline_width_mode_item = (
                Mtoon1VrmcMaterialsMtoonPropertyGroup.outline_width_mode_enum
            )
            outline_width_mode = outline_width_mode_item.value_to_identifier(
                outline_width_mode_number,
                Mtoon1VrmcMaterialsMtoonPropertyGroup.OUTLINE_WIDTH_MODE_NONE.identifier,
            )
        outline_width_factor = convert.float_or_none(
            vrmc_materials_mtoon.get("outline_width_factor")
        )
        outline_width_multiply_texture_backup = backup_texture_info(
            vrmc_materials_mtoon.get("outline_width_multiply_texture")
        )
        outline_color_factor = convert.float3_or_none(
            vrmc_materials_mtoon.get("outline_color_factor")
        )
        outline_lighting_mix_factor = convert.float_or_none(
            vrmc_materials_mtoon.get("outline_lighting_mix_factor")
        )
        uv_animation_mask_texture_backup = backup_texture_info(
            vrmc_materials_mtoon.get("uv_animation_mask_texture")
        )
        uv_animation_scroll_x_speed_factor = convert.float_or_none(
            vrmc_materials_mtoon.get("uv_animation_scroll_x_speed_factor")
        )
        uv_animation_scroll_y_speed_factor = convert.float_or_none(
            vrmc_materials_mtoon.get("uv_animation_scroll_y_speed_factor")
        )
        uv_animation_rotation_speed_factor = convert.float_or_none(
            vrmc_materials_mtoon.get("uv_animation_rotation_speed_factor")
        )

    if (
        addon_version < shader.LAST_MODIFIED_VERSION
        # Blender 4.2からノードの仕様変更があるので強制的にリセットする
        or (bpy.app.version >= (4, 2) and tuple(context.blend_data.version) < (4, 2))
    ):
        reset_shader_node_group(
            context, material, reset_material_node_tree=True, reset_node_groups=False
        )

    # ここから先は、シェーダーノードが最新の状態になっている想定のコードを書ける
    typed_mtoon1 = get_material_extension(material).mtoon1
    typed_vrmc_materials_mtoon = typed_mtoon1.extensions.vrmc_materials_mtoon
    if alpha_mode is not None:
        typed_mtoon1.alpha_mode = alpha_mode
    if alpha_cutoff is not None:
        typed_mtoon1.alpha_cutoff = alpha_cutoff
    if base_color_factor is not None:
        typed_mtoon1.pbr_metallic_roughness.base_color_factor = base_color_factor
    if base_color_texture_backup is not None:
        typed_mtoon1.pbr_metallic_roughness.base_color_texture.restore(
            base_color_texture_backup
        )
    if normal_texture_backup is not None:
        typed_mtoon1.normal_texture.restore(normal_texture_backup)
    if normal_texture_scale is not None:
        typed_mtoon1.normal_texture.scale = normal_texture_scale
    if emissive_texture_backup is not None:
        typed_mtoon1.emissive_texture.restore(emissive_texture_backup)
    if emissive_factor is not None:
        typed_mtoon1.emissive_factor = emissive_factor
    if emissive_strength is not None:
        typed_mtoon1.extensions.khr_materials_emissive_strength.emissive_strength = (
            emissive_strength
        )

    if transparent_with_z_write is not None:
        typed_vrmc_materials_mtoon.transparent_with_z_write = transparent_with_z_write
    if render_queue_offset_number is not None:
        typed_vrmc_materials_mtoon.render_queue_offset_number = (
            render_queue_offset_number
        )
    if shade_multiply_texture_backup is not None:
        typed_vrmc_materials_mtoon.shade_multiply_texture.restore(
            shade_multiply_texture_backup
        )
    if shade_color_factor is not None:
        typed_vrmc_materials_mtoon.shade_color_factor = shade_color_factor
    if shading_shift_texture_backup is not None:
        typed_vrmc_materials_mtoon.shading_shift_texture.restore(
            shading_shift_texture_backup
        )
    if shading_shift_factor is not None:
        typed_vrmc_materials_mtoon.shading_shift_factor = shading_shift_factor
    if shading_shift_texture_scale is not None:
        typed_vrmc_materials_mtoon.shading_shift_texture.scale = (
            shading_shift_texture_scale
        )
    if shading_toony_factor is not None:
        typed_vrmc_materials_mtoon.shading_toony_factor = shading_toony_factor
    if gi_equalization_factor is not None:
        typed_vrmc_materials_mtoon.gi_equalization_factor = gi_equalization_factor
    if matcap_factor is not None:
        typed_vrmc_materials_mtoon.matcap_factor = matcap_factor
    if matcap_texture_backup is not None:
        typed_vrmc_materials_mtoon.matcap_texture.restore(matcap_texture_backup)
    if parametric_rim_color_factor is not None:
        typed_vrmc_materials_mtoon.parametric_rim_color_factor = (
            parametric_rim_color_factor
        )
    if rim_multiply_texture_backup is not None:
        typed_vrmc_materials_mtoon.rim_multiply_texture.restore(
            rim_multiply_texture_backup
        )
    if rim_lighting_mix_factor is not None:
        typed_vrmc_materials_mtoon.rim_lighting_mix_factor = rim_lighting_mix_factor
    if parametric_rim_fresnel_power_factor is not None:
        typed_vrmc_materials_mtoon.parametric_rim_fresnel_power_factor = (
            parametric_rim_fresnel_power_factor
        )
    if parametric_rim_lift_factor is not None:
        typed_vrmc_materials_mtoon.parametric_rim_lift_factor = (
            parametric_rim_lift_factor
        )
    if outline_width_mode is not None:
        typed_vrmc_materials_mtoon.outline_width_mode = outline_width_mode
    if outline_width_factor is not None:
        typed_vrmc_materials_mtoon.outline_width_factor = outline_width_factor
    if outline_width_multiply_texture_backup is not None:
        typed_vrmc_materials_mtoon.outline_width_multiply_texture.restore(
            outline_width_multiply_texture_backup
        )
    if outline_color_factor is not None:
        typed_vrmc_materials_mtoon.outline_color_factor = outline_color_factor
    if outline_lighting_mix_factor is not None:
        typed_vrmc_materials_mtoon.outline_lighting_mix_factor = (
            outline_lighting_mix_factor
        )
    if uv_animation_mask_texture_backup is not None:
        typed_vrmc_materials_mtoon.uv_animation_mask_texture.restore(
            uv_animation_mask_texture_backup
        )
    if uv_animation_scroll_x_speed_factor is not None:
        typed_vrmc_materials_mtoon.uv_animation_scroll_x_speed_factor = (
            uv_animation_scroll_x_speed_factor
        )
    if uv_animation_scroll_y_speed_factor is not None:
        typed_vrmc_materials_mtoon.uv_animation_scroll_y_speed_factor = (
            uv_animation_scroll_y_speed_factor
        )
    if uv_animation_rotation_speed_factor is not None:
        typed_vrmc_materials_mtoon.uv_animation_rotation_speed_factor = (
            uv_animation_rotation_speed_factor
        )

    typed_mtoon1.setup_drivers()
    updated_addon_version = version.get_addon_version()
    if tuple(typed_mtoon1.addon_version) != updated_addon_version:
        typed_mtoon1.addon_version = updated_addon_version


def backup_texture_info(texture_info: object) -> Optional[TextureInfoBackup]:
    if not isinstance(texture_info, IDPropertyGroup):
        return None

    source: Optional[Image] = None
    wrap_s = Mtoon1SamplerPropertyGroup.WRAP_DEFAULT.identifier
    wrap_t = Mtoon1SamplerPropertyGroup.WRAP_DEFAULT.identifier
    offset_x = 0.0
    offset_y = 0.0
    scale_x = 1.0
    scale_y = 1.0

    index = texture_info.get("index")
    if isinstance(index, IDPropertyGroup):
        source_object = index.get("source")
        if isinstance(source_object, Image):
            source = source_object
        sampler = index.get("sampler")
        if isinstance(sampler, IDPropertyGroup):
            wrap_s_number = sampler.get("wrap_s")
            if isinstance(wrap_s_number, int):
                wrap_s = Mtoon1SamplerPropertyGroup.wrap_enum.value_to_identifier(
                    wrap_s_number,
                    wrap_s,
                )
            wrap_t_number = sampler.get("wrap_t")
            if isinstance(wrap_t_number, int):
                wrap_t = Mtoon1SamplerPropertyGroup.wrap_enum.value_to_identifier(
                    wrap_t_number,
                    wrap_t,
                )

    extensions = texture_info.get("extensions")
    if isinstance(extensions, IDPropertyGroup):
        khr_texture_transform = extensions.get("khr_texture_transform")
        if isinstance(khr_texture_transform, IDPropertyGroup):
            offset = convert.float2_or_none(khr_texture_transform.get("offset"))
            if offset is not None:
                offset_x, offset_y = offset
            scale = convert.float2_or_none(khr_texture_transform.get("scale"))
            if scale is not None:
                scale_x, scale_y = scale

    return TextureInfoBackup(
        source=source,
        mag_filter=None,
        min_filter=None,
        wrap_s=wrap_s,
        wrap_t=wrap_t,
        offset=(offset_x, offset_y),
        scale=(scale_x, scale_y),
    )


def migrate_sampler_filter_node(material: Material) -> None:
    node_tree = material.node_tree
    if not node_tree:
        return

    vrm_addon_extension = material.get("vrm_addon_extension")
    if not isinstance(vrm_addon_extension, IDPropertyGroup):
        return

    mtoon1 = vrm_addon_extension.get("mtoon1")
    if not mtoon1:
        return

    for node_name, attrs in [
        (
            "Mtoon1BaseColorTexture.Image",
            ("pbr_metallic_roughness", "base_color_texture"),
        ),
        ("Mtoon1EmissiveTexture.Image", ("emissive_texture",)),
        ("Mtoon1NormalTexture.Image", ("normal_texture",)),
        (
            "Mtoon1ShadeMultiplyTexture.Image",
            ("extensions", "vrmc_materials_mtoon", "shade_multiply_texture"),
        ),
        (
            "Mtoon1ShadingShiftTexture.Image",
            ("extensions", "vrmc_materials_mtoon", "shading_shift_texture"),
        ),
        (
            "Mtoon1OutlineWidthMultiplyTexture.Image",
            (
                "extensions",
                "vrmc_materials_mtoon",
                "outline_width_multiply_texture",
            ),
        ),
        (
            "Mtoon1UvAnimationMaskTexture.Image",
            ("extensions", "vrmc_materials_mtoon", "uv_animation_mask_texture"),
        ),
        (
            "Mtoon1MatcapTexture.Image",
            ("extensions", "vrmc_materials_mtoon", "matcap_texture"),
        ),
        (
            "Mtoon1RimMultiplyTexture.Image",
            ("extensions", "vrmc_materials_mtoon", "rim_multiply_texture"),
        ),
    ]:
        sampler = functools.reduce(
            lambda prop, attr: getattr(prop, attr, None),
            (*attrs, "index", "sampler"),
            mtoon1,
        )
        if not isinstance(sampler, IDPropertyGroup):
            continue

        mag_filter = sampler.get("mag_filter")
        if (
            not isinstance(mag_filter, int)
            or mag_filter not in Mtoon1SamplerPropertyGroup.mag_filter_enum.values()
        ):
            continue

        node = node_tree.nodes.get(node_name)
        if not isinstance(node, ShaderNodeTexImage):
            continue

        if (
            mag_filter == GL_NEAREST
            and node.interpolation != IMAGE_INTERPOLATION_CLOSEST
        ):
            node.interpolation = IMAGE_INTERPOLATION_CLOSEST
        if (
            mag_filter == GL_LINEAR
            and node.interpolation not in GL_LINEAR_IMAGE_INTERPOLATIONS
        ):
            node.interpolation = IMAGE_INTERPOLATION_LINEAR
