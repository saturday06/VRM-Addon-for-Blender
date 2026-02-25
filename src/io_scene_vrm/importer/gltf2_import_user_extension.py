# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import secrets
import string
from typing import ClassVar, Final, Optional

import bpy
from bpy.types import Armature, Image, Object
from io_scene_gltf2.io.com import gltf2_io
from io_scene_gltf2.io.imp.gltf2_io_gltf import glTFImporter

from ..common.convert import sequence_or_none
from ..common.deep import Json, make_json
from ..common.logger import get_logger
from ..editor.extension import (
    VrmAddonArmatureExtensionPropertyGroup,
    get_armature_extension,
)
from ..editor.khr_xmp_json_ld.property_group import (
    KhrXmpJsonLdKhrCharacterPacketPropertyGroup,
)

KHR_CHARACTER_SUPPORTED: Final[bool] = bpy.app.version >= (100000,)

logger = get_logger(__name__)


def get_list_from_json_ld(v: object) -> list[str]:
    """Extract a list of strings from a JSON-LD @list value or plain list."""
    v = make_json(v)
    if isinstance(v, dict):
        items = v.get("@list")
        if isinstance(items, list):
            return [s for s in items if isinstance(s, str)]
    if isinstance(v, list):
        return [s for s in v if isinstance(s, str)]
    return []


def get_string_from_json_ld_value(v: object) -> str:
    """Return a string from a plain string or localized JSON-LD object.

    A localized value looks like ``{"en": "hello", "und": "hello"}``.
    The first string value found is returned.  An empty string is returned
    when no string value can be extracted.
    """
    v = make_json(v)
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
        self, image: object, bpy_image: object, gltf_importer: object
    ) -> None:
        current_import_id = self.current_import_id
        if current_import_id is None:
            return

        if not isinstance(bpy_image, Image):
            logger.warning(
                "gather_import_image_after_hook: bpy_image is not a Image but %s",
                type(bpy_image),
            )
            return

        images = sequence_or_none(
            getattr(getattr(gltf_importer, "data", None), "images", None)
        )
        if images is None:
            logger.warning(
                "gather_import_image_after_hook:"
                " gltf_importer is unexpected structure: %s",
                gltf_importer,
            )
            return

        if image not in images:
            logger.warning(
                "gather_import_image_after_hook: %s not in %s", image, images
            )
            return

        index = images.index(image)

        bpy_image[current_import_id] = index


class Gltf2ImportUserExtensionVrmKhrCharacter(Gltf2ImportUserExtensionVrm):
    def __init__(self) -> None:
        # Per-import image index -> Blender Image (for KHR_character thumbnail)
        self._image_index_to_bpy_image: dict[int, Image] = {}
        # Per-import list of imported armature objects
        self._imported_armature_objects: list[Object] = []

    def gather_import_image_after_hook(
        self, image: object, bpy_image: object, gltf_importer: object
    ) -> None:
        super().gather_import_image_after_hook(image, bpy_image, gltf_importer)

        if not isinstance(image, gltf2_io.Image):
            return

        if not isinstance(gltf_importer, glTFImporter):
            return

        if not isinstance(bpy_image, Image):
            logger.warning(
                "gather_import_image_after_hook: bpy_image is not a Image but %s",
                type(bpy_image),
            )
            return

    def gather_import_node_after_hook(
        self,
        _vnode: object,
        _gltf_node: object,
        blender_object: object,
        _gltf: object,
    ) -> None:
        """Track armature objects created during import for KHR_character processing."""
        if isinstance(blender_object, Object) and blender_object.type == "ARMATURE":
            self._imported_armature_objects.append(blender_object)

    def gather_import_scene_after_nodes_hook(
        self,
        _gltf_scene: object,
        _blender_scene: object,
        gltf: object,
    ) -> None:
        """Read KHR_character/KHR_xmp_json_ld and fill armature custom properties."""
        data = getattr(gltf, "data", None)
        if data is None:
            return

        # Only process files that declare the KHR_character extension
        extensions_used = make_json(getattr(data, "extensions_used", None))
        if not isinstance(extensions_used, list):
            return

        if "KHR_character" not in extensions_used:
            return

        extensions = make_json(getattr(data, "extensions", None))
        if not isinstance(extensions, dict):
            return

        khr_character = extensions.get("KHR_character")
        if not isinstance(khr_character, dict):
            return

        # Locate the KHR_xmp_json_ld packets array
        khr_xmp_json_ld = extensions.get("KHR_xmp_json_ld")
        if not isinstance(khr_xmp_json_ld, dict):
            return
        packets = khr_xmp_json_ld.get("packets")
        if not isinstance(packets, list) or not packets:
            return

        # Determine which packet is the character packet
        # (asset.extensions.KHR_xmp_json_ld.packet holds the index, default 0)
        packet_index = 0
        asset = make_json(getattr(data, "asset", None))
        if asset is not None:
            asset_extensions = make_json(getattr(asset, "extensions", None))
            if isinstance(asset_extensions, dict):
                asset_khr_xmp = asset_extensions.get("KHR_xmp_json_ld")
                if isinstance(asset_khr_xmp, dict):
                    idx = asset_khr_xmp.get("packet")
                    if isinstance(idx, int) and 0 <= idx < len(packets):
                        packet_index = idx

        if packet_index >= len(packets):
            logger.warning(
                "gather_import_scene_after_nodes_hook:"
                " packet index %d out of range (packets: %d)",
                packet_index,
                len(packets),
            )
            return
        packet = packets[packet_index]
        if not isinstance(packet, dict):
            return

        # Find armature objects: prefer tracked ones, fall back to vnodes
        armature_objects = list(self._imported_armature_objects)
        if not armature_objects:
            vnodes = getattr(gltf, "vnodes", {}) or {}
            for vnode in vnodes.values():
                blender_obj = getattr(vnode, "blender_object", None)
                if (
                    blender_obj is not None
                    and getattr(blender_obj, "type", None) == "ARMATURE"
                ):
                    armature_objects.append(blender_obj)

        if not armature_objects:
            logger.warning(
                "gather_import_scene_after_nodes_hook:"
                " no armature found for KHR_character import"
            )
            return

        for armature_obj in armature_objects:
            armature_data = getattr(armature_obj, "data", None)
            if not isinstance(armature_data, Armature):
                continue
            ext = get_armature_extension(armature_data)
            ext.spec_version = (
                VrmAddonArmatureExtensionPropertyGroup.SPEC_VERSION_KHR_CHARACTER
            )
            self.fill_khr_character_xmp_packet(
                ext.khr_character.khr_xmp_json_ld_packet, packet
            )

    def fill_khr_character_xmp_packet(
        self,
        xmp: KhrXmpJsonLdKhrCharacterPacketPropertyGroup,
        packet: dict[str, Json],
    ) -> None:
        """Populate KhrXmpJsonLdKhrCharacterPacketPropertyGroup from XMP packet."""
        # dc:title - plain string or localized {"lang": "value"}
        dc_title = get_string_from_json_ld_value(packet.get("dc:title"))
        if dc_title:
            xmp.dc_title = dc_title

        # dc:creator - {"@list": [...]}
        for creator in get_list_from_json_ld(packet.get("dc:creator")):
            item = xmp.dc_creator.add()
            item.value = creator

        # dc:license - {"@list": [...]}
        for license_url in get_list_from_json_ld(packet.get("dc:license")):
            item = xmp.dc_license.add()
            item.value = license_url

        # dc:created - plain string
        dc_created = packet.get("dc:created")
        if isinstance(dc_created, str):
            xmp.dc_created = dc_created

        # dc:rights - plain string or localized
        dc_rights = get_string_from_json_ld_value(packet.get("dc:rights"))
        if dc_rights:
            xmp.dc_rights = dc_rights

        # dc:publisher - plain string
        dc_publisher = packet.get("dc:publisher")
        if isinstance(dc_publisher, str):
            xmp.dc_publisher = dc_publisher

        # dc:description - plain string or localized
        dc_description = get_string_from_json_ld_value(packet.get("dc:description"))
        if dc_description:
            xmp.dc_description = dc_description

        # dc:subject - {"@list": [...]}
        for subject in get_list_from_json_ld(packet.get("dc:subject")):
            item = xmp.dc_subject.add()
            item.value = subject

        # dc:source - plain string
        dc_source = packet.get("dc:source")
        if isinstance(dc_source, str):
            xmp.dc_source = dc_source

        # khr:version - plain string
        khr_version = packet.get("khr:version")
        if isinstance(khr_version, str):
            xmp.khr_version = khr_version

        # khr:thumbnailImage - integer index into the glTF images array
        thumbnail_index = packet.get("khr:thumbnailImage")
        if isinstance(thumbnail_index, int):
            bpy_image = self._image_index_to_bpy_image.get(thumbnail_index)
            if isinstance(bpy_image, Image):
                xmp.khr_thumbnail_image = bpy_image


if KHR_CHARACTER_SUPPORTED:
    glTF2ImportUserExtension = Gltf2ImportUserExtensionVrmKhrCharacter
else:
    glTF2ImportUserExtension = Gltf2ImportUserExtensionVrm
