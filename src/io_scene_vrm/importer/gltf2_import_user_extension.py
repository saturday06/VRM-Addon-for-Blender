# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import secrets
import string
from collections.abc import Mapping
from typing import ClassVar, Final, Optional

import bpy
from bpy.types import Armature, Image, Object, Scene
from io_scene_gltf2.io.com import gltf2_io
from io_scene_gltf2.io.imp.gltf2_io_gltf import glTFImporter

from ..common.deep import Json, make_json
from ..common.logger import get_logger
from ..editor.extension import (
    VrmAddonArmatureExtensionPropertyGroup,
    get_armature_extension,
)
from ..editor.khr_xmp_json_ld.property_group import (
    KhrXmpJsonLdKhrCharacterPacketPropertyGroup,
)

if bpy.app.version >= (4, 3):
    from io_scene_gltf2.blender.imp.vnode import VNode
else:
    from io_scene_gltf2.blender.imp.gltf2_blender_vnode import VNode

KHR_CHARACTER_SUPPORTED: Final[bool] = bpy.app.version >= (100000,)

logger = get_logger(__name__)


def get_list_from_json_ld(v: Json) -> list[str]:
    """Extract a list of strings from a JSON-LD @list value or plain list."""
    if isinstance(v, dict):
        items = v.get("@list")
        if isinstance(items, list):
            return [s for s in items if isinstance(s, str)]
    if isinstance(v, list):
        return [s for s in v if isinstance(s, str)]
    return []


def get_string_from_json_ld_value(v: Json) -> str:
    """Return a string from a plain string or localized JSON-LD object.

    A localized value looks like ``{"en": "hello", "und": "hello"}``.
    The first string value found is returned.  An empty string is returned
    when no string value can be extracted.
    """
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        for item in v.values():
            if isinstance(item, str):
                return item
    return ""


class Gltf2ImportUserExtensionVrm:
    current_import_id: ClassVar[Optional[str]] = None

    @classmethod
    def update_current_import_id(cls) -> str:
        import_id = "BlenderVrmAddonImport" + (
            "".join(secrets.choice(string.digits) for _ in range(10))
        )
        cls.current_import_id = import_id
        return import_id

    @classmethod
    def clear_current_import_id(cls) -> None:
        cls.current_import_id = None

    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/6f9d0d9fc1bb30e2b0bb019342ffe86bd67358fc/addons/io_scene_gltf2/blender/imp/gltf2_blender_image.py#L51
    def gather_import_image_after_hook(
        self,
        gltf_image: gltf2_io.Image,
        blender_image: Image,
        gltf: glTFImporter,
    ) -> None:
        current_import_id = self.current_import_id
        if current_import_id is None:
            return

        if not isinstance(gltf_data := getattr(gltf, "data", None), gltf2_io.Gltf):
            return

        images = gltf_data.images
        if not images:
            return

        if gltf_image not in images:
            return

        image_index = images.index(gltf_image)
        blender_image[current_import_id] = image_index


class Gltf2ImportUserExtensionVrmKhrCharacter(Gltf2ImportUserExtensionVrm):
    def __init__(self) -> None:
        self.image_index_to_blender_image: dict[int, Image] = {}
        self.armature_objects: list[Object] = []

    def gather_import_image_after_hook(
        self,
        gltf_image: gltf2_io.Image,
        blender_image: Image,
        gltf: glTFImporter,
    ) -> None:
        super().gather_import_image_after_hook(gltf_image, blender_image, gltf)

        if not isinstance(gltf_data := getattr(gltf, "data", None), gltf2_io.Gltf):
            return

        images = gltf_data.images
        if not images:
            return
        if gltf_image not in images:
            return
        image_index = images.index(gltf_image)
        self.image_index_to_blender_image[image_index] = blender_image

    def gather_import_node_after_hook(
        self,
        _vnode: VNode,
        _gltf_node: gltf2_io.Node,
        blender_object: Object,
        _gltf: glTFImporter,
    ) -> None:
        """Track armature objects created during import for KHR_character processing."""
        if blender_object.type == "ARMATURE":
            self.armature_objects.append(blender_object)

    def gather_import_scene_after_nodes_hook(
        self,
        _gltf_scene: gltf2_io.Scene,
        _blender_scene: Scene,
        gltf: glTFImporter,
    ) -> None:
        """Read KHR_character/KHR_xmp_json_ld and fill armature custom properties."""
        if not isinstance(gltf_data := getattr(gltf, "data", None), gltf2_io.Gltf):
            return

        extensions_used = gltf_data.extensions_used
        if not extensions_used:
            return

        if "KHR_character" not in extensions_used:
            return

        extensions = gltf_data.extensions
        if not extensions:
            return

        khr_character_dict = extensions.get("KHR_character")
        if not isinstance(khr_character_dict, dict):
            return

        packet_dict = None
        if (
            isinstance(khr_xmp_json_ld_dict := extensions.get("KHR_xmp_json_ld"), dict)
            and isinstance(
                packet_dicts := make_json(khr_xmp_json_ld_dict.get("packets")), list
            )
            and isinstance(asset_extensions := gltf_data.asset.extensions, dict)
            and isinstance(
                asset_khr_xmp_dict := asset_extensions.get("KHR_xmp_json_ld"), dict
            )
            and isinstance(packet_index := asset_khr_xmp_dict.get("packet"), int)
            and 0 <= packet_index < len(packet_dicts)
        ):
            packet_dict = packet_dicts[packet_index]

        if not isinstance(packet_dict, dict):
            return

        # Find armature objects: prefer tracked ones, fall back to vnodes
        armature_objects = self.armature_objects
        if not armature_objects:
            logger.warning(
                "gather_import_scene_after_nodes_hook:"
                " no armature found for KHR_character import"
            )
            return

        for armature_object in armature_objects:
            armature_data = armature_object.data
            if not isinstance(armature_data, Armature):
                continue
            ext = get_armature_extension(armature_data)
            if "VRMC_vrm" not in extensions_used and "VRM" not in extensions_used:
                ext.spec_version = (
                    VrmAddonArmatureExtensionPropertyGroup.SPEC_VERSION_KHR_CHARACTER
                )
            self.fill_khr_character_xmp_packet(
                ext.khr_character.khr_xmp_json_ld_packet, packet_dict
            )

    def fill_khr_character_xmp_packet(
        self,
        xmp: KhrXmpJsonLdKhrCharacterPacketPropertyGroup,
        packet_dict: Mapping[str, Json],
    ) -> None:
        """Populate KhrXmpJsonLdKhrCharacterPacketPropertyGroup from XMP packet."""
        # dc:title - plain string or localized {"lang": "value"}
        dc_title = get_string_from_json_ld_value(packet_dict.get("dc:title"))
        if dc_title:
            xmp.dc_title = dc_title

        # dc:creator - {"@list": [...]}
        for creator in get_list_from_json_ld(packet_dict.get("dc:creator")):
            item = xmp.dc_creator.add()
            item.value = creator

        # dc:license - {"@list": [...]}
        for license_url in get_list_from_json_ld(packet_dict.get("dc:license")):
            item = xmp.dc_license.add()
            item.value = license_url

        # dc:created - plain string
        dc_created = packet_dict.get("dc:created")
        if isinstance(dc_created, str):
            xmp.dc_created = dc_created

        # dc:rights - plain string or localized
        dc_rights = get_string_from_json_ld_value(packet_dict.get("dc:rights"))
        if dc_rights:
            xmp.dc_rights = dc_rights

        # dc:publisher - plain string
        dc_publisher = packet_dict.get("dc:publisher")
        if isinstance(dc_publisher, str):
            xmp.dc_publisher = dc_publisher

        # dc:description - plain string or localized
        dc_description = get_string_from_json_ld_value(
            packet_dict.get("dc:description")
        )
        if dc_description:
            xmp.dc_description = dc_description

        # dc:subject - {"@list": [...]}
        for subject in get_list_from_json_ld(packet_dict.get("dc:subject")):
            item = xmp.dc_subject.add()
            item.value = subject

        # dc:source - plain string
        dc_source = packet_dict.get("dc:source")
        if isinstance(dc_source, str):
            xmp.dc_source = dc_source

        # khr:version - plain string
        khr_version = packet_dict.get("khr:version")
        if isinstance(khr_version, str):
            xmp.khr_version = khr_version

        # khr:thumbnailImage - integer index into the glTF images array
        thumbnail_index = packet_dict.get("khr:thumbnailImage")
        if isinstance(thumbnail_index, int):
            bpy_image = self.image_index_to_blender_image.get(thumbnail_index)
            if isinstance(bpy_image, Image):
                xmp.khr_thumbnail_image = bpy_image


if KHR_CHARACTER_SUPPORTED:
    glTF2ImportUserExtension = Gltf2ImportUserExtensionVrmKhrCharacter
else:
    glTF2ImportUserExtension = Gltf2ImportUserExtensionVrm
