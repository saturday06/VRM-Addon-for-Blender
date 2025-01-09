# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from typing import Optional

import bpy
from bpy.app.translations import pgettext
from bpy.types import Context, Panel, PropertyGroup, UILayout

from ...common.logger import get_logger
from .. import search
from ..extension import get_material_extension
from ..ops import VRM_OT_open_url_in_web_browser, layout_operator
from .ops import (
    VRM_OT_import_mtoon1_texture_image_file,
    VRM_OT_reset_mtoon1_material_shader_node_tree,
)
from .property_group import (
    Mtoon0TexturePropertyGroup,
    Mtoon1MaterialPropertyGroup,
    Mtoon1TextureInfoPropertyGroup,
)

logger = get_logger(__name__)


def draw_texture_info(
    material_name: str,
    ext: Mtoon1MaterialPropertyGroup,
    parent_layout: UILayout,
    base_property_group: PropertyGroup,
    texture_info_attr_name: str,
    color_factor_attr_name: Optional[str] = None,
    *,
    is_vrm0: bool,
) -> UILayout:
    texture_info = getattr(base_property_group, texture_info_attr_name, None)
    if not isinstance(texture_info, Mtoon1TextureInfoPropertyGroup):
        raise TypeError
    layout = parent_layout.split(factor=0.3)
    toggle_layout = layout.row()
    toggle_layout.alignment = "LEFT"
    toggle_layout.prop(
        texture_info,
        "show_expanded",
        emboss=False,
        text=texture_info.index.panel_label,
        translate=False,
        icon="TRIA_DOWN" if texture_info.show_expanded else "TRIA_RIGHT",
    )
    input_layout = layout.row(align=True)

    node_image = texture_info.index.get_connected_node_image()
    if node_image == texture_info.index.source:
        source_prop_name = "source"
        placeholder = ""
    else:
        source_prop_name = "source_for_desynced_node_tree"
        placeholder = node_image.name if node_image else ""

    if bpy.app.version >= (4, 1):
        input_layout.prop(
            texture_info.index,
            source_prop_name,
            text="",
            translate=False,
            placeholder=placeholder,
        )
    else:
        input_layout.prop(
            texture_info.index,
            source_prop_name,
            text="",
            translate=False,
        )

    import_image_file_op = layout_operator(
        input_layout,
        VRM_OT_import_mtoon1_texture_image_file,
        text="",
        translate=False,
        icon="FILEBROWSER",
    )
    import_image_file_op.material_name = material_name
    import_image_file_op.target_texture = type(texture_info.index).__name__
    if color_factor_attr_name:
        input_layout.separator(factor=0.5)
        input_layout.prop(base_property_group, color_factor_attr_name, text="")

    if not texture_info.show_expanded:
        return input_layout

    box = parent_layout.box().column()
    if texture_info.index.source:
        box.prop(texture_info.index.source.colorspace_settings, "name")
        if (
            texture_info.index.source.colorspace_settings.name
            != texture_info.index.colorspace
        ):
            box.box().label(
                text=pgettext(
                    'It is recommended to set "{colorspace}"'
                    + ' to "{input_colorspace}" for "{texture_label}"'
                ).format(
                    texture_label=texture_info.index.label,
                    colorspace=pgettext(texture_info.index.colorspace),
                    input_colorspace=pgettext("Input Color Space"),
                ),
                icon="ERROR",
            )
    box.prop(texture_info.index.sampler, "mag_filter")
    box.prop(texture_info.index.sampler, "min_filter")
    box.prop(texture_info.index.sampler, "wrap_s")
    box.prop(texture_info.index.sampler, "wrap_t")
    box.prop(texture_info.extensions.khr_texture_transform, "offset")
    box.prop(texture_info.extensions.khr_texture_transform, "scale")

    if is_vrm0:
        if ext.extensions.vrmc_materials_mtoon.matcap_texture == texture_info:
            box.box().label(
                text="Offset and Scale are ignored in VRM 0.0", icon="ERROR"
            )
        elif ext.pbr_metallic_roughness.base_color_texture != texture_info:
            box.box().label(
                text="Offset and Scale in VRM 0.0 are"
                + " the values of the Lit Color Texture",
                icon="ERROR",
            )

    return input_layout


def draw_mtoon0_texture(
    material_name: str,
    parent_layout: UILayout,
    base_property_group: PropertyGroup,
    texture_attr_name: str,
    scalar_factor_attr_name: str,
) -> UILayout:
    texture = getattr(base_property_group, texture_attr_name, None)
    if not isinstance(texture, Mtoon0TexturePropertyGroup):
        raise TypeError
    layout = parent_layout.split(factor=0.3)
    toggle_layout = layout.row()
    toggle_layout.alignment = "LEFT"
    toggle_layout.prop(
        texture,
        "show_expanded",
        emboss=False,
        text=texture.panel_label,
        translate=False,
        icon="TRIA_DOWN" if texture.show_expanded else "TRIA_RIGHT",
    )
    input_layout = layout.row(align=True)
    input_layout.prop(texture, "source", text="")
    import_image_file_op = layout_operator(
        input_layout,
        VRM_OT_import_mtoon1_texture_image_file,
        text="",
        translate=False,
        icon="FILEBROWSER",
    )
    import_image_file_op.material_name = material_name
    import_image_file_op.target_texture = type(texture).__name__

    input_layout.separator(factor=0.5)
    input_layout.prop(base_property_group, scalar_factor_attr_name, text="")

    if not texture.show_expanded:
        return input_layout

    box = parent_layout.box().column()
    if texture.source:
        box.prop(texture.source.colorspace_settings, "name")
        if texture.source.colorspace_settings.name != texture.colorspace:
            box.box().label(
                text=pgettext(
                    'It is recommended to set "{colorspace}"'
                    + ' to "{input_colorspace}" for "{texture_label}"'
                ).format(
                    texture_label=texture.label,
                    colorspace=pgettext(texture.colorspace),
                    input_colorspace=pgettext("Input Color Space"),
                ),
                icon="ERROR",
            )
    box.prop(texture.sampler, "mag_filter")
    box.prop(texture.sampler, "min_filter")
    box.prop(texture.sampler, "wrap_s")
    box.prop(texture.sampler, "wrap_t")
    return input_layout


def draw_mtoon1_material(context: Context, layout: UILayout) -> None:
    material = context.material
    if not material:
        return
    ext = get_material_extension(material)
    layout = layout.column()

    layout.prop(ext.mtoon1, "enabled")
    if not ext.mtoon1.enabled:
        return

    is_vrm0 = search.current_armature_is_vrm0(context)
    gltf = ext.mtoon1
    mtoon = gltf.extensions.vrmc_materials_mtoon

    # https://github.com/vrm-c/UniVRM/blob/v0.102.0/Assets/VRMShaders/VRM10/MToon10/Editor/MToonInspector.cs#L14
    layout.label(text="Rendering", translate=False)
    rendering_box = layout.box().column()
    rendering_box.prop(gltf, "alpha_mode")
    if gltf.alpha_mode == gltf.ALPHA_MODE_MASK.identifier:
        rendering_box.prop(gltf, "alpha_cutoff", slider=True)
    if gltf.alpha_mode == gltf.ALPHA_MODE_BLEND.identifier:
        rendering_box.prop(mtoon, "transparent_with_z_write")
    rendering_box.prop(gltf, "double_sided")
    rendering_box.prop(mtoon, "render_queue_offset_number", slider=True)

    layout.label(text="Lighting", translate=False)
    lighting_box = layout.box().column()
    draw_texture_info(
        material.name,
        ext.mtoon1,
        lighting_box,
        gltf.pbr_metallic_roughness,
        "base_color_texture",
        "base_color_factor",
        is_vrm0=is_vrm0,
    )
    draw_texture_info(
        material.name,
        ext.mtoon1,
        lighting_box,
        mtoon,
        "shade_multiply_texture",
        "shade_color_factor",
        is_vrm0=is_vrm0,
    )
    normal_texture_layout = draw_texture_info(
        material.name,
        ext.mtoon1,
        lighting_box,
        gltf,
        "normal_texture",
        is_vrm0=is_vrm0,
    )
    normal_texture_layout.separator(factor=0.5)
    normal_texture_layout.prop(gltf.normal_texture, "scale")

    lighting_box.prop(mtoon, "shading_toony_factor", slider=True)
    lighting_box.prop(mtoon, "shading_shift_factor", slider=True)
    shading_shift_texture_layout = draw_texture_info(
        material.name,
        ext.mtoon1,
        lighting_box,
        mtoon,
        "shading_shift_texture",
        is_vrm0=is_vrm0,
    )
    shading_shift_texture_layout.separator(factor=0.5)
    shading_shift_texture_layout.prop(mtoon.shading_shift_texture, "scale")

    # UniVRM (MIT License)
    # https://github.com/vrm-c/UniVRM/blob/d2b4ad1964b754341873f2a1b093d58e1df1713f/Assets/VRMShaders/VRM10/MToon10/Editor/MToonInspector.cs#L120-L128
    if (
        not mtoon.shading_shift_texture.index.source
        and mtoon.shading_toony_factor - mtoon.shading_shift_factor < 1.0 - 0.001
    ):
        lighting_box.box().label(
            text="The lit area includes non-lit area.", icon="ERROR"
        )

    layout.label(text="Global Illumination", translate=False)
    gi_box = layout.box()
    gi_box.prop(mtoon, "gi_equalization_factor", slider=True)

    layout.label(text="Emission", translate=False)
    emission_box = layout.box().column()
    emissive_texture_layout = draw_texture_info(
        material.name,
        ext.mtoon1,
        emission_box,
        gltf,
        "emissive_texture",
        is_vrm0=is_vrm0,
    ).row(align=True)
    emissive_texture_layout.scale_x = 0.71
    emissive_texture_layout.separator(factor=0.5 / 0.71)
    emissive_texture_layout.prop(gltf, "emissive_factor", text="")
    emissive_texture_layout.prop(
        gltf.extensions.khr_materials_emissive_strength, "emissive_strength"
    )

    layout.label(text="Rim Lighting", translate=False)
    rim_lighting_box = layout.box().column()
    draw_texture_info(
        material.name,
        ext.mtoon1,
        rim_lighting_box,
        mtoon,
        "rim_multiply_texture",
        is_vrm0=is_vrm0,
    )
    rim_lighting_box.prop(mtoon, "rim_lighting_mix_factor", slider=True)
    draw_texture_info(
        material.name,
        ext.mtoon1,
        rim_lighting_box,
        mtoon,
        "matcap_texture",
        "matcap_factor",
        is_vrm0=is_vrm0,
    )
    rim_lighting_box.row().prop(mtoon, "parametric_rim_color_factor")
    rim_lighting_box.prop(mtoon, "parametric_rim_fresnel_power_factor", slider=True)
    rim_lighting_box.prop(mtoon, "parametric_rim_lift_factor", slider=True)

    layout.label(text="Outline", translate=False)
    outline_box = layout.box().column()
    outline_box.prop(mtoon, "outline_width_mode")
    if (
        bpy.app.version >= (3, 3)
        and mtoon.outline_width_mode
        == mtoon.OUTLINE_WIDTH_MODE_SCREEN_COORDINATES.identifier
    ):
        outline_warning_message = pgettext(
            'The "Screen Coordinates" display is not yet implemented.\n'
            + 'It is displayed in the same way as "World Coordinates".'
        )
        outline_warning_column = outline_box.box().column(align=True)
        for index, outline_warning_line in enumerate(
            outline_warning_message.splitlines()
        ):
            outline_warning_column.label(
                text=outline_warning_line,
                translate=False,
                icon="BLANK1" if index else "INFO",
            )
    if mtoon.outline_width_mode != mtoon.OUTLINE_WIDTH_MODE_NONE.identifier:
        outline_width_multiply_texture_layout = draw_texture_info(
            material.name,
            ext.mtoon1,
            outline_box,
            mtoon,
            "outline_width_multiply_texture",
            is_vrm0=is_vrm0,
        )
        outline_width_multiply_texture_layout.separator(factor=0.5)
        outline_width_multiply_texture_layout.prop(
            mtoon, "outline_width_factor", slider=True, text=""
        )
        outline_box.row().prop(mtoon, "outline_color_factor")
        outline_box.prop(mtoon, "outline_lighting_mix_factor", slider=True)
    outline_box.prop(mtoon, "enable_outline_preview", text="Enable Preview")

    layout.label(text="UV Animation", translate=False)
    uv_animation_box = layout.box().column()
    draw_texture_info(
        material.name,
        ext.mtoon1,
        uv_animation_box,
        mtoon,
        "uv_animation_mask_texture",
        is_vrm0=is_vrm0,
    )
    uv_animation_box.prop(mtoon, "uv_animation_scroll_x_speed_factor")
    uv_animation_box.prop(mtoon, "uv_animation_scroll_y_speed_factor")
    uv_animation_box.prop(mtoon, "uv_animation_rotation_speed_factor")

    layout.prop(gltf, "show_expanded_mtoon0")
    if gltf.show_expanded_mtoon0:
        mtoon0_box = layout.box().column()
        mtoon0_box.prop(gltf, "mtoon0_front_cull_mode")
        draw_mtoon0_texture(
            material.name,
            mtoon0_box,
            ext.mtoon1,
            "mtoon0_receive_shadow_texture",
            "mtoon0_receive_shadow_rate",
        )
        draw_mtoon0_texture(
            material.name,
            mtoon0_box,
            ext.mtoon1,
            "mtoon0_shading_grade_texture",
            "mtoon0_shading_grade_rate",
        )
        mtoon0_box.prop(gltf, "mtoon0_light_color_attenuation", slider=True)
        mtoon0_box.prop(gltf, "mtoon0_rim_lighting_mix", slider=True)
        mtoon0_box.prop(gltf, "mtoon0_outline_scaled_max_distance", slider=True)
        mtoon0_box.prop(gltf, "mtoon0_render_queue_and_clamp", slider=True)

    reset_op = layout_operator(layout, VRM_OT_reset_mtoon1_material_shader_node_tree)
    reset_op.material_name = material.name


def draw_material(context: Context, layout: UILayout) -> None:
    material = context.material
    if not material:
        return
    ext = get_material_extension(material)
    if ext.mtoon1.is_outline_material:
        layout.box().label(icon="INFO", text="This is a MToon Outline material")
        return

    draw_mtoon1_material(context, layout)

    node, legacy_shader_name = search.legacy_shader_node(material)
    if ext.mtoon1.enabled or (node and legacy_shader_name == "MToon_unversioned"):
        layout.prop(ext.mtoon1, "export_shape_key_normals")
        return
    if node and legacy_shader_name in ["TRANSPARENT_ZWRITE", "GLTF"]:
        return

    help_column = layout.box().column(align=True)
    help_message = pgettext(
        "How to export this material to VRM.\n"
        + "Meet one of the following conditions.\n"
        + " - VRM MToon Material is enabled\n"
        + ' - Connect the "Surface" to a "Principled BSDF"\n'
        + ' - Connect the "Surface" to a "MToon_unversioned"\n'
        + ' - Connect the "Surface" to a "TRANSPARENT_ZWRITE"\n'
        + " - Others that are compatible with the glTF 2.0 add-on export\n"
    )
    for index, help_line in enumerate(help_message.splitlines()):
        help_column.label(
            text=help_line, translate=False, icon="HELP" if index == 0 else "NONE"
        )
    url = "https://docs.blender.org/manual/en/2.93/addons/import_export/scene_gltf2.html#exported-materials"
    link_row = help_column.split(factor=0.8)
    link_row.label(text="   " + url, translate=False)
    web_op = layout_operator(link_row, VRM_OT_open_url_in_web_browser, icon="URL")
    web_op.url = url


class VRM_PT_vrm_material_property(Panel):
    bl_idname = "VRM_PT_vrm_material_property"
    bl_label = "VRM Material"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    @classmethod
    def poll(cls, context: Context) -> bool:
        return bool(context.material)

    def draw(self, context: Context) -> None:
        draw_material(context, self.layout)
