import datetime
import importlib

import bpy

#
# ここで `import io_scene_gltf2` をするとio_scene_gltf2が無効化されている場合全体を巻き込んで
# エラーになる。そのため関数内でインポートするように注意する。
#


class WM_OT_vrm_io_scene_gltf2_disabled_warning(bpy.types.Operator):
    bl_label = "glTF 2.0 add-on is disabled"
    bl_idname = "wm.vrm_gltf2_addon_disabled_warning"
    bl_options = {"REGISTER"}

    def execute(self, _context: bpy.types.Context) -> set[str]:
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, _context: bpy.types.Context) -> None:
        self.layout.label(
            text='Official add-on "glTF 2.0 format" is required. Please enable it.'
        )


def image_to_image_bytes(
    image: bpy.types.Image, export_settings: dict[str, object]
) -> tuple[bytes, str]:
    if bpy.app.version < (3, 6, 0):
        gltf2_blender_image = importlib.import_module(
            "io_scene_gltf2.blender.exp.gltf2_blender_image"
        )
    else:
        gltf2_blender_image = importlib.import_module(
            "io_scene_gltf2.blender.exp.material.extensions.gltf2_blender_image"
        )
    export_image = gltf2_blender_image.ExportImage.from_blender_image(image)

    if image.file_format == "JPEG":
        mime_type = "image/jpeg"
    else:
        mime_type = "image/png"

    if bpy.app.version < (3, 3, 0):
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/518b6466032534c4be4a4c50ca72d37c169a5ebf/addons/io_scene_gltf2/blender/exp/gltf2_blender_image.py
        return export_image.encode(mime_type), mime_type

    if bpy.app.version < (3, 5, 0):
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/b8901bb58fa29d78bc2741cadb3f01b6d30d7750/addons/io_scene_gltf2/blender/exp/gltf2_blender_image.py
        image_bytes, _specular_color_factor = export_image.encode(mime_type)
        return image_bytes, mime_type

    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/e662c281fc830d7ad3ea918d38c6a1881ee143c5/addons/io_scene_gltf2/blender/exp/gltf2_blender_image.py#L139
    image_bytes, _specular_color_factor = export_image.encode(
        mime_type, export_settings
    )
    return image_bytes, mime_type


def init_extras_export() -> None:
    try:
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/6f9d0d9fc1bb30e2b0bb019342ffe86bd67358fc/addons/io_scene_gltf2/blender/com/gltf2_blender_extras.py#L20-L21
        gltf2_blender_extras = importlib.import_module(
            "io_scene_gltf2.blender.com.gltf2_blender_extras"
        )
    except ModuleNotFoundError:
        return
    key = "vrm_addon_extension"
    if key not in gltf2_blender_extras.BLACK_LIST:
        gltf2_blender_extras.BLACK_LIST.append(key)


def create_export_settings() -> dict[str, object]:
    return {
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L522
        "timestamp": datetime.datetime.now(datetime.timezone.utc),
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L258-L268
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L552
        "gltf_materials": True,
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L120-L137
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L532
        "gltf_format": "GLB",
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L154-L168
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L533
        "gltf_image_format": "AUTO",
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L329-L333
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L569
        "gltf_extras": True,
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L611-L633
        "gltf_user_extensions": [],
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L606
        "gltf_binary": bytearray(),
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L176-L184
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/67b2ed150b0eba08129b970dbe1116c633a77d24/addons/io_scene_gltf2/__init__.py#L530
        "gltf_keep_original_textures": False,
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/bfe4ff8b1b5c26ba17b0531b67798376147d9fa7/addons/io_scene_gltf2/__init__.py#L273-L279
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/bfe4ff8b1b5c26ba17b0531b67798376147d9fa7/addons/io_scene_gltf2/__init__.py#L579
        "gltf_original_specular": False,
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/e662c281fc830d7ad3ea918d38c6a1881ee143c5/addons/io_scene_gltf2/__init__.py#L208-L214
        # https://github.com/KhronosGroup/glTF-Blender-IO/blob/e662c281fc830d7ad3ea918d38c6a1881ee143c5/addons/io_scene_gltf2/__init__.py#L617
        "gltf_jpeg_quality": 75,
    }


def export_scene_gltf(
    filepath: str,
    check_existing: bool,
    export_format: str,
    export_extras: bool,
    export_current_frame: bool,
    use_selection: bool,
    export_animations: bool,
    export_rest_position_armature: bool,
) -> set[str]:
    if bpy.app.version < (3, 6, 0):
        return bpy.ops.export_scene.gltf(
            filepath=filepath,
            check_existing=check_existing,
            export_format=export_format,
            export_extras=export_extras,
            export_current_frame=export_current_frame,
            use_selection=use_selection,
            export_animations=export_animations,
        )

    return bpy.ops.export_scene.gltf(
        filepath=filepath,
        check_existing=check_existing,
        export_format=export_format,
        export_extras=export_extras,
        export_current_frame=export_current_frame,
        use_selection=use_selection,
        export_animations=export_animations,
        export_rest_position_armature=export_rest_position_armature,
    )
