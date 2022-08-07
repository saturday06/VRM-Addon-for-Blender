from typing import Set, Tuple, cast

import bpy


class WM_OT_vrm_io_scene_gltf2_disabled_warning(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_label = "glTF 2.0 add-on is disabled"
    bl_idname = "wm.vrm_gltf2_addon_disabled_warning"
    bl_options = {"REGISTER"}

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> Set[str]:
        return cast(
            Set[str], context.window_manager.invoke_props_dialog(self, width=500)
        )

    def draw(self, _context: bpy.types.Context) -> None:
        self.layout.label(
            text='Official add-on "glTF 2.0 format" is required. Please enable it.'
        )


def image_to_image_bytes(image: bpy.types.Image) -> Tuple[bytes, str]:
    from io_scene_gltf2.blender.exp.gltf2_blender_image import (
        ExportImage,
    )  # pyright: reportMissingImports=false

    export_image = ExportImage.from_blender_image(image)

    if image.file_format == "JPEG":
        mime_type = "image/jpeg"
    else:
        mime_type = "image/png"

    if bpy.app.version < (3, 3, 0):
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/518b6466032534c4be4a4c50ca72d37c169a5ebf/addons/io_scene_gltf2/blender/exp/gltf2_blender_image.py
        return export_image.encode(mime_type), mime_type

    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/b8901bb58fa29d78bc2741cadb3f01b6d30d7750/addons/io_scene_gltf2/blender/exp/gltf2_blender_image.py
    image_bytes, _specular_color_factor = export_image.encode(mime_type)
    return image_bytes, mime_type
