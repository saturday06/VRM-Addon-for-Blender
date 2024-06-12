import ctypes
import sysconfig
from collections.abc import Mapping
from platform import python_implementation
from typing import Optional

import bpy
from bpy.types import Material

from .logging import get_logger

logger = get_logger(__name__)


def read_blend_method_from_memory_address(material: Material) -> Optional[str]:
    """material.blend_methodの値を直接メモリから読み取る.

    Blender 4.2からmaterial.blend_methodの値が廃止されて読めなくなった。
    しかし、マテリアルのマイグレーションのためにはどうしてもその値を知る必要がある。

    仕方がないので既知のプラットフォームに限定してメモリから直接値を読む。
    ログは多めに出す。
    """
    if bpy.app.version < (4, 2):
        return material.blend_method

    if bpy.app.build_type != b"Release":
        logger.warning(
            f"Does not read the Blend Mode of {material.name}. "
            + f'"{bpy.app.build_type!r}" builds are not supported.'
        )
        return None

    if python_implementation() != "CPython":
        logger.warning(
            f"Does not read the Blend Mode of {material.name}. "
            + f"{python_implementation()} is not supported."
        )
        return None

    native_struct_offsets_by_major_minor: Mapping[
        tuple[int, int],
        Mapping[str, int],
    ] = {
        (4, 2): {
            "win-amd64": 324,
            "macosx-11.00-arm64": 324,
        },
    }

    major_minor = (  # Use [x] to make type checkers happy
        bpy.app.version[0],
        bpy.app.version[1],
    )
    native_struct_offsets = native_struct_offsets_by_major_minor.get(major_minor)
    if native_struct_offsets is None:
        logger.warning(
            f"Does not read the Blend Mode of {material.name}. "
            + f"Blender {major_minor[0]}.{major_minor[1]} is not supported."
        )
        return None

    platform = sysconfig.get_platform()
    native_struct_offset = native_struct_offsets.get(platform)
    if native_struct_offset is None:
        logger.warning(
            f"Does not read the Blend Mode of {material.name}. "
            + f"{platform} is not supported."
        )
        return None

    logger.warning(
        f"Starts reading the Blend Mode of {material.name} from its memory address."
    )
    native_char = ctypes.c_char.from_address(
        material.as_pointer() + native_struct_offset
    )
    logger.warning(
        f"Finished reading the Blend Mode of {material.name} from its memory address."
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
