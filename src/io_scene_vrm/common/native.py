import ctypes
import sysconfig
from collections.abc import Mapping
from typing import Optional

import bpy
from bpy.types import Material

from .logging import get_logger

logger = get_logger(__name__)


def read_blend_method_from_memory_address(material: Material) -> Optional[str]:
    """material.blend_methodの値を直接メモリから読み取る.

    Blender 4.2からmaterial.blend_methodの値が廃止されて読めなくなった。
    しかし、マテリアルのマイグレーションのためにはどうしてもその値を知る必要がある。

    仕方がないので、既知のビルドを利用している場合はメモリアドレスから直接値を読む。
    ログは多めに出す。
    """
    if bpy.app.version < (4, 2):
        return material.blend_method

    if bpy.app.build_type != b"Release":
        logger.warning(
            'The Blend Mode of "%s" could not be read. "%s" builds are not supported.',
            material.name,
            bpy.app.build_type,
        )
        return None

    native_struct_offsets: Mapping[tuple[int, int, str, Optional[str]], int] = {
        (4, 2, "linux-x86_64", ".cpython-311-x86_64-linux-gnu.so"): 324,
        (4, 2, "macosx-10.15-x86_64", ".cpython-311-darwin.so"): 324,
        (4, 2, "macosx-11.00-arm64", ".cpython-311-darwin.so"): 324,
        (4, 2, "win-amd64", ".cp311-win_amd64.pyd"): 324,
    }

    major = bpy.app.version[0]
    minor = bpy.app.version[1]
    platform = sysconfig.get_platform()
    ext_suffix = sysconfig.get_config_var("EXT_SUFFIX")
    native_struct_offset = native_struct_offsets.get(
        (major, minor, platform, ext_suffix)
    )
    if native_struct_offset is None:
        logger.warning(
            'The Blend Mode of "%s" could not be read.'
            " Blender %s.%s (platform=%s, ext_suffix=%s) is not supported.",
            material.name,
            major,
            minor,
            platform,
            ext_suffix,
        )
        return None

    logger.warning(
        "Starts reading the Blend Mode of %s from its memory address.", material.name
    )
    ##### BEGIN DANGER ZONE #####
    native_char = ctypes.c_char.from_address(
        material.as_pointer() + native_struct_offset
    )
    ##### END DANGER ZONE #####
    logger.warning(
        "Finished reading the Blend Mode of %s from its memory address.", material.name
    )

    if native_char.value == bytes([0]):
        return "OPAQUE"
    if native_char.value == bytes([3]):
        return "CLIP"
    if native_char.value == bytes([4]):
        return "HASHED"
    if native_char.value == bytes([5]):
        return "BLEND"

    return None
