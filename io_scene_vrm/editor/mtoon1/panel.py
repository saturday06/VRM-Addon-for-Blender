from typing import Optional

import bpy
from bpy.app.translations import pgettext

from .. import search
from ..ops import VRM_OT_open_url_in_web_browser
from .ops import (
    VRM_OT_import_mtoon1_texture_image_file,
    VRM_OT_reset_mtoon1_material_shader_node_tree,
)
from .property_group import (
    Mtoon1MaterialPropertyGroup,
    Mtoon1VrmcMaterialsMtoonPropertyGroup,
)


def draw_texture_info(
    material_name: str,
    ext: Mtoon1MaterialPropertyGroup,
    is_vrm0: bool,
    parent_layout: bpy.types.UILayout,
    base_property_group: bpy.types.PropertyGroup,
    texture_info_attr_name: str,
    color_factor_attr_name: Optional[str] = None,
) -> bpy.types.UILayout:
    texture_info = getattr(base_property_group, texture_info_attr_name)
    layout = parent_layout.split(factor=0.3)
    toggle_layout = layout.row()
    toggle_layout.alignment = "LEFT"
    toggle_layout.prop(
        texture_info,
        "show_expanded",
        emboss=False,
        text=texture_info.panel_label,
        translate=False,
        icon="TRIA_DOWN" if texture_info.show_expanded else "TRIA_RIGHT",
    )
    input_layout = layout.row(align=True)
    input_layout.prop(texture_info.index, "source", text="")
    import_image_file_op = input_layout.operator(
        VRM_OT_import_mtoon1_texture_image_file.bl_idname,
        text="",
        translate=False,
        icon="FILEBROWSER",
    )
    import_image_file_op.material_name = material_name
    import_image_file_op.target_texture_info = type(texture_info).__name__
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
            != texture_info.colorspace
        ):
            box.box().label(
                text=pgettext(
                    'It is recommended to set "{colorspace}" to "{input_colorspace}" for "{texture_label}"'
                ).format(
                    texture_label=texture_info.label,
                    colorspace=pgettext(texture_info.colorspace),
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
                text="Offset and Scale in VRM 0.0 are the values of the Lit Color Texture",
                icon="ERROR",
            )

    return input_layout


def draw_mtoon1_material(
    context: bpy.types.Context, layout: bpy.types.UILayout
) -> None:
    material = context.material
    ext = material.vrm_addon_extension
    layout = layout.column()

    layout.prop(ext.mtoon1, "enabled")
    if not ext.mtoon1.enabled:
        return

    is_vrm0 = search.current_armature_is_vrm0(context)
    gltf = ext.mtoon1
    mtoon1 = gltf.extensions.vrmc_materials_mtoon

    # https://github.com/vrm-c/UniVRM/blob/v0.102.0/Assets/VRMShaders/VRM10/MToon10/Editor/MToonInspector.cs#L14
    layout.label(text="Rendering", translate=False)
    rendering_box = layout.box().column()
    rendering_box.prop(gltf, "alpha_mode")
    if gltf.alpha_mode == gltf.ALPHA_MODE_MASK:
        rendering_box.prop(gltf, "alpha_cutoff", slider=True)
    if gltf.alpha_mode == gltf.ALPHA_MODE_BLEND:
        rendering_box.prop(mtoon1, "transparent_with_z_write")
    rendering_box.prop(gltf, "double_sided")
    rendering_box.prop(mtoon1, "render_queue_offset_number", slider=True)

    layout.label(text="Lighting", translate=False)
    lighting_box = layout.box().column()
    draw_texture_info(
        material.name,
        ext.mtoon1,
        is_vrm0,
        lighting_box,
        gltf.pbr_metallic_roughness,
        "base_color_texture",
        "base_color_factor",
    )
    draw_texture_info(
        material.name,
        ext.mtoon1,
        is_vrm0,
        lighting_box,
        mtoon1,
        "shade_multiply_texture",
        "shade_color_factor",
    )
    normal_texture_layout = draw_texture_info(
        material.name,
        ext.mtoon1,
        is_vrm0,
        lighting_box,
        gltf,
        "normal_texture",
    )
    normal_texture_layout.separator(factor=0.5)
    normal_texture_layout.prop(gltf.normal_texture, "scale")

    lighting_box.prop(mtoon1, "shading_toony_factor", slider=True)
    lighting_box.prop(mtoon1, "shading_shift_factor", slider=True)
    shading_shift_texture_layout = draw_texture_info(
        material.name,
        ext.mtoon1,
        is_vrm0,
        lighting_box,
        mtoon1,
        "shading_shift_texture",
    )
    shading_shift_texture_layout.separator(factor=0.5)
    shading_shift_texture_layout.prop(mtoon1.shading_shift_texture, "scale")

    # UniVRM (MIT License)
    # https://github.com/vrm-c/UniVRM/blob/d2b4ad1964b754341873f2a1b093d58e1df1713f/Assets/VRMShaders/VRM10/MToon10/Editor/MToonInspector.cs#L120-L128
    if (
        not mtoon1.shading_shift_texture.index.source
        and mtoon1.shading_toony_factor - mtoon1.shading_shift_factor < 1.0 - 0.001
    ):
        lighting_box.box().label(
            text="The lit area includes non-lit area.", icon="ERROR"
        )

    layout.label(text="Global Illumination", translate=False)
    gi_box = layout.box()
    gi_box.prop(mtoon1, "gi_equalization_factor", slider=True)

    layout.label(text="Emission", translate=False)
    emission_box = layout.box().column()
    emissive_texture_layout = draw_texture_info(
        material.name,
        ext.mtoon1,
        is_vrm0,
        emission_box,
        gltf,
        "emissive_texture",
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
        is_vrm0,
        rim_lighting_box,
        mtoon1,
        "rim_multiply_texture",
    )
    rim_lighting_box.prop(mtoon1, "rim_lighting_mix_factor", slider=True)
    draw_texture_info(
        material.name,
        ext.mtoon1,
        is_vrm0,
        rim_lighting_box,
        mtoon1,
        "matcap_texture",
        "matcap_factor",
    )
    rim_lighting_box.row().prop(mtoon1, "parametric_rim_color_factor")
    rim_lighting_box.prop(mtoon1, "parametric_rim_fresnel_power_factor", slider=True)
    rim_lighting_box.prop(mtoon1, "parametric_rim_lift_factor", slider=True)

    layout.label(text="Outline", translate=False)
    outline_box = layout.box().column()
    outline_box.prop(mtoon1, "outline_width_mode")
    if (
        bpy.app.version >= (3, 3)
        and mtoon1.outline_width_mode
        == Mtoon1VrmcMaterialsMtoonPropertyGroup.OUTLINE_WIDTH_MODE_SCREEN_COORDINATES
    ):
        outline_warning_message = pgettext(
            'The "Screen Coordinates" display is not yet implemented.\n'
            + 'It is displayed in the same way as "World Coordinates".'
        )
        outline_warning_column = outline_box.box().column()
        for index, outline_warning_line in enumerate(
            outline_warning_message.splitlines()
        ):
            outline_warning_column.label(
                text=outline_warning_line, icon="BLANK1" if index else "INFO"
            )
    if (
        mtoon1.outline_width_mode
        != Mtoon1VrmcMaterialsMtoonPropertyGroup.OUTLINE_WIDTH_MODE_NONE
    ):
        outline_width_multiply_texture_layout = draw_texture_info(
            material.name,
            ext.mtoon1,
            is_vrm0,
            outline_box,
            mtoon1,
            "outline_width_multiply_texture",
        )
        outline_width_multiply_texture_layout.separator(factor=0.5)
        outline_width_multiply_texture_layout.prop(
            mtoon1, "outline_width_factor", slider=True, text=""
        )
        outline_box.row().prop(mtoon1, "outline_color_factor")
        outline_box.prop(mtoon1, "outline_lighting_mix_factor", slider=True)

    layout.label(text="UV Animation", translate=False)
    uv_animation_box = layout.box().column()
    draw_texture_info(
        material.name,
        ext.mtoon1,
        is_vrm0,
        uv_animation_box,
        mtoon1,
        "uv_animation_mask_texture",
    )
    uv_animation_box.prop(mtoon1, "uv_animation_scroll_x_speed_factor")
    uv_animation_box.prop(mtoon1, "uv_animation_scroll_y_speed_factor")
    uv_animation_box.prop(mtoon1, "uv_animation_rotation_speed_factor")

    layout.operator(
        VRM_OT_reset_mtoon1_material_shader_node_tree.bl_idname
    ).material_name = context.material.name


def draw_material(context: bpy.types.Context, layout: bpy.types.UILayout) -> None:
    ext = context.material.vrm_addon_extension
    if ext.mtoon1.is_outline_material:
        layout.box().label(icon="INFO", text="This is a MToon Outline material")
        return

    draw_mtoon1_material(context, layout)

    node = search.vrm_shader_node(context.material)
    if ext.mtoon1.enabled or (node and node.node_tree["SHADER"] == "MToon_unversioned"):
        layout.prop(ext.mtoon1, "export_shape_key_normals")
        return
    if node and node.node_tree["SHADER"] in ["TRANSPARENT_ZWRITE", "GLTF"]:
        return

    help_column = layout.box().column()
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
    url = "https://docs.blender.org/manual/en/2.83/addons/import_export/scene_gltf2.html#exported-materials"
    link_row = help_column.split(factor=0.8)
    link_row.label(text="   " + url, translate=False)
    web_op = link_row.operator(VRM_OT_open_url_in_web_browser.bl_idname, icon="URL")
    web_op.url = url


class VRM_PT_vrm_material_property(bpy.types.Panel):  # type: ignore[misc]
    bl_idname = "VRM_PT_vrm_material_property"
    bl_label = "VRM Material"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return isinstance(context.material, bpy.types.Material)

    def draw(self, context: bpy.types.Context) -> None:
        draw_material(context, self.layout)
