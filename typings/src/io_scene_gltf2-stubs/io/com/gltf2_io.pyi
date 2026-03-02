# SPDX-License-Identifier: Apache-2.0
# https://projects.blender.org/blender/blender-addons/src/tag/v2.93.0/io_scene_gltf2/io/com/gltf2_io.py
# https://projects.blender.org/blender/blender/src/branch/blender-v4.2-release/scripts/addons_core/io_scene_gltf2/io/com/gltf2_io.py

class Animation: ...

class Asset:
    extensions: dict[str, dict[str, object]] | None

class Material: ...
class Node: ...
class Image: ...
class Scene: ...

class Gltf:
    asset: Asset
    images: list[Image] | None
    extensions_used: list[str] | None
    extensions: dict[str, dict[str, object]] | None
    def to_dict(self) -> dict[str, object]: ...
