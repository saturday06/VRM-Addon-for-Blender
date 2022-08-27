import secrets
import string
from collections import abc
from typing import Any, Optional

import bpy

from ..common.logging import get_logger

logger = get_logger(__name__)


class Gltf2AddonImporterUserExtension:
    __current_import_id: Optional[str] = None

    @classmethod
    def update_current_import_id(cls) -> str:
        import_id = "BlenderVrmAddonImport" + (
            "".join(secrets.choice(string.digits) for _ in range(10))
        )
        cls.__current_import_id = import_id
        return import_id

    @classmethod
    def clear_current_import_id(cls) -> None:
        cls.__current_import_id = None

    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/6f9d0d9fc1bb30e2b0bb019342ffe86bd67358fc/addons/io_scene_gltf2/blender/imp/gltf2_blender_image.py#L51
    def gather_import_image_after_hook(
        self, img: Any, blender_image: Any, gltf_importer: Any
    ) -> None:
        if self.__current_import_id is None:
            return

        if (
            not hasattr(gltf_importer, "data")
            or not hasattr(gltf_importer.data, "images")
            or not isinstance(gltf_importer.data.images, abc.Sequence)
        ):
            logger.warning(
                f"gather_import_image_after_hook: gltf_importer is unexpected structure: {gltf_importer}"
            )
            return
        if img not in gltf_importer.data.images:
            logger.warning(
                f"gather_import_image_after_hook: {img} not in {gltf_importer.data.images}"
            )
            return
        index = gltf_importer.data.images.index(img)
        if not isinstance(blender_image, bpy.types.Image):
            return
        blender_image[self.__current_import_id] = index
