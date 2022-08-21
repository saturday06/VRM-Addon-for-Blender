from typing import Optional

import bpy

from .property_group import Mtoon1MaterialVrmcMaterialsMtoonPropertyGroup


def draw_texture_info(
    name: str,
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
        text=name,
        translate=False,
        icon="TRIA_DOWN" if texture_info.show_expanded else "TRIA_RIGHT",
    )
    layout.prop(texture_info.index, "source", text="")
    if color_factor_attr_name:
        layout.prop(base_property_group, color_factor_attr_name, text="")

    if not texture_info.show_expanded:
        return layout

    box = parent_layout.box().column()
    box.prop(texture_info.index.sampler, "mag_filter")
    box.prop(texture_info.index.sampler, "min_filter")
    box.prop(texture_info.index.sampler, "wrap_s")
    box.prop(texture_info.index.sampler, "wrap_t")
    box.prop(texture_info.extensions.khr_texture_transform, "offset")
    box.prop(texture_info.extensions.khr_texture_transform, "scale")

    return layout


class VRM_PT_vrm_material_property(bpy.types.Panel):  # type: ignore[misc] # noqa: N801
    bl_idname = "VRM_PT_vrm_material_property"
    bl_label = "VRM Material"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.material)

    def draw(self, context: bpy.types.Context) -> None:
        ext = context.material.vrm_addon_extension
        layout = self.layout.column()
        layout.prop(ext.mtoon1, "enabled")
        if not ext.mtoon1.enabled:
            return

        gltf = ext.mtoon1
        mtoon1 = gltf.extensions.vrmc_materials_mtoon

        # https://github.com/vrm-c/UniVRM/blob/v0.102.0/Assets/VRMShaders/VRM10/MToon10/Editor/MToonInspector.cs#L14
        layout.label(text="Rendering", translate=False)
        rendering_box = layout.box().column()
        rendering_box.prop(gltf, "alpha_mode")
        if gltf.alpha_mode == gltf.ALPHA_MODE_MASK:
            rendering_box.prop(gltf, "alpha_cut_off", slider=True)
        if gltf.alpha_mode == gltf.ALPHA_MODE_BLEND:
            rendering_box.prop(mtoon1, "transparent_with_z_write")
        rendering_box.prop(gltf, "double_sided")
        rendering_box.prop(mtoon1, "render_queue_offset_number", slider=True)

        layout.label(text="Lighting", translate=False)
        lighting_box = layout.box().column()
        draw_texture_info(
            "Lit Color, Alpha",
            lighting_box,
            gltf.pbr_metallic_roughness,
            "base_color_texture",
            "base_color_factor",
        )
        draw_texture_info(
            "Shade Color",
            lighting_box,
            mtoon1,
            "shade_multiply_texture",
            "shade_color_factor",
        )
        normal_texture_layout = draw_texture_info(
            "Normal Map",
            lighting_box,
            gltf,
            "normal_texture",
        )
        normal_texture_layout.prop(gltf.normal_texture, "scale")

        lighting_box.prop(mtoon1, "shading_toony_factor", slider=True)
        lighting_box.prop(mtoon1, "shading_shift_factor", slider=True)
        shading_shift_texture_layout = draw_texture_info(
            "Additive Shading Shift", lighting_box, mtoon1, "shading_shift_texture"
        )
        shading_shift_texture_layout.prop(mtoon1.shading_shift_texture, "scale")

        layout.label(text="Global Illumination", translate=False)
        gi_box = layout.box()
        gi_box.prop(mtoon1, "gi_equalization_factor", slider=True)

        layout.label(text="Emission", translate=False)
        emission_box = layout.box().column()
        draw_texture_info(
            "Emission", emission_box, gltf, "emissive_texture", "emissive_factor"
        )

        layout.label(text="Rim Lighting", translate=False)
        rim_lighting_box = layout.box().column()
        draw_texture_info("Rim Color", rim_lighting_box, mtoon1, "rim_multiply_texture")
        rim_lighting_box.prop(mtoon1, "rim_lighting_mix_factor", slider=True)
        matcap_texture_layout = draw_texture_info(
            "Matcap Rim", rim_lighting_box, mtoon1, "matcap_texture"
        )
        matcap_texture_layout.prop(mtoon1, "matcap_factor", text="")
        rim_lighting_box.row().prop(mtoon1, "parametric_rim_color_factor")
        rim_lighting_box.prop(
            mtoon1, "parametric_rim_fresnel_power_factor", slider=True
        )
        rim_lighting_box.prop(mtoon1, "parametric_rim_lift_factor", slider=True)

        layout.label(text="Outline", translate=False)
        outline_box = layout.box().column()
        outline_box.prop(mtoon1, "outline_width_mode")
        if (
            mtoon1.outline_width_mode
            != Mtoon1MaterialVrmcMaterialsMtoonPropertyGroup.OUTLINE_WIDTH_MODE_NONE
        ):
            outline_width_multiply_texture_layout = draw_texture_info(
                "Outline Width", outline_box, mtoon1, "outline_width_multiply_texture"
            )
            outline_width_multiply_texture_layout.prop(
                mtoon1, "outline_width_factor", slider=True, text=""
            )
            outline_box.row().prop(mtoon1, "outline_color_factor")
            outline_box.prop(mtoon1, "outline_lighting_mix_factor", slider=True)

        layout.label(text="UV Animation", translate=False)
        uv_animation_box = layout.box().column()
        draw_texture_info("Mask", uv_animation_box, mtoon1, "uv_animation_mask_texture")
        uv_animation_box.prop(mtoon1, "uv_animation_scroll_x_speed_factor")
        uv_animation_box.prop(mtoon1, "uv_animation_scroll_y_speed_factor")
        uv_animation_box.prop(mtoon1, "uv_animation_rotation_speed_factor")
