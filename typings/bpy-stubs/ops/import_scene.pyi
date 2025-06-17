# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from bpy.types import OperatorFileListElement, bpy_prop_collection

def gltf(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    filepath: str = "",
    filter_glob: str = "*.glb;*.gltf",
    files: bpy_prop_collection[OperatorFileListElement] | None = None,
    loglevel: int = 0,
    import_pack_images: bool = True,
    merge_vertices: bool = False,
    import_shading: str = "NORMALS",
    bone_heuristic: str = "TEMPERANCE",
    guess_original_bind_pose: bool = True,
    disable_bone_shape: bool = False,
) -> set[str]: ...
