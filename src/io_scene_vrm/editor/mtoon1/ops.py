# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Optional

from bpy.app.translations import pgettext
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import (
    Context,
    Event,
    Material,
    Operator,
)
from bpy_extras.io_utils import ImportHelper

from ...common.logger import get_logger
from ..extension_accessor import get_material_extension
from .property_group import (
    Mtoon0ReceiveShadowTexturePropertyGroup,
    Mtoon0ShadingGradeTexturePropertyGroup,
    Mtoon1BaseColorTexturePropertyGroup,
    Mtoon1EmissiveTexturePropertyGroup,
    Mtoon1MatcapTexturePropertyGroup,
    Mtoon1NormalTexturePropertyGroup,
    Mtoon1OutlineWidthMultiplyTexturePropertyGroup,
    Mtoon1RimMultiplyTexturePropertyGroup,
    Mtoon1ShadeMultiplyTexturePropertyGroup,
    Mtoon1ShadingShiftTexturePropertyGroup,
    Mtoon1UvAnimationMaskTexturePropertyGroup,
    convert_material_to_mtoon1,
    convert_mtoon1_to_bsdf_principled,
    refresh_mtoon1_outline,
    reset_shader_node_group,
)

_logger = get_logger(__name__)


class VRM_OT_convert_material_to_mtoon1(Operator):
    bl_idname = "vrm.convert_material_to_mtoon1"
    bl_label = "Convert Material to MToon 1.0"
    bl_description = "Convert Material to MToon 1.0"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    material_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )

    def execute(self, context: Context) -> set[str]:
        material = context.blend_data.materials.get(self.material_name)
        if not isinstance(material, Material):
            return {"CANCELLED"}
        convert_material_to_mtoon1(material, context)
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        material_name: str  # type: ignore[no-redef]


class VRM_OT_convert_mtoon1_to_bsdf_principled(Operator):
    bl_idname = "vrm.convert_mtoon1_to_bsdf_principled"
    bl_label = "Convert MToon 1.0 to Principled BSDF"
    bl_description = "Convert MToon 1.0 to Principled BSDF"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    material_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )

    def execute(self, context: Context) -> set[str]:
        material = context.blend_data.materials.get(self.material_name)
        if not isinstance(material, Material):
            return {"CANCELLED"}
        convert_mtoon1_to_bsdf_principled(material)
        return {"FINISHED"}

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        material_name: str  # type: ignore[no-redef]


class VRM_OT_reset_mtoon1_material_shader_node_tree(Operator):
    bl_idname = "vrm.reset_mtoon1_material_shader_node_group"
    bl_label = "Reset Shader Nodes"
    bl_description = "Reset MToon 1.0 Material Shader Node Tree"
    bl_options: ClassVar = {"REGISTER", "UNDO"}

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
    bl_options: ClassVar = {"REGISTER", "UNDO"}

    filepath: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},
        subtype="FILE_PATH",
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


class VRM_OT_refresh_mtoon1_outline(Operator):
    bl_idname = "vrm.refresh_mtoon1_outline"
    bl_label = "Refresh MToon 1.0 Outline Width Mode"
    bl_description = "Import Texture Image File"
    bl_options: ClassVar = {"UNDO"}

    material_name: StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )
    create_modifier: BoolProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}
    )

    def execute(self, context: Context) -> set[str]:
        material_name: Optional[str] = self.material_name
        if not material_name:
            material_name = None
        refresh_mtoon1_outline(
            context, material_name, create_modifier=self.create_modifier
        )
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
    bl_options: ClassVar = {"REGISTER"}

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
