from typing import Optional

from bpy.types import OperatorFileListElement, bpy_prop_collection

def vrm(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    filepath: str = "",
    use_addon_preferences: bool = False,
    extract_textures_into_folder: bool = True,
    make_new_texture_folder: bool = True,
) -> set[str]: ...
def gltf(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    filepath: str = "",
    filter_glob: str = "*.glb;*.gltf",
    files: Optional[bpy_prop_collection[OperatorFileListElement]] = None,
    loglevel: int = 0,
    import_pack_images: bool = True,
    merge_vertices: bool = False,
    import_shading: str = "NORMALS",
    bone_heuristic: str = "TEMPERANCE",
    guess_original_bind_pose: bool = True,
) -> set[str]: ...
def vrma(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    filepath: str = "",
    armature_object_name: str = "",
) -> set[str]: ...
