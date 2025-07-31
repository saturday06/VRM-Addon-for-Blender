# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
def flush_edits(
    execution_context: str = "EXEC_DEFAULT",
    /,
) -> set[str]: ...
def lib_id_fake_user_toggle(
    execution_context: str = "EXEC_DEFAULT",
    /,
) -> set[str]: ...
def lib_id_generate_preview(
    execution_context: str = "EXEC_DEFAULT",
    /,
) -> set[str]: ...
def lib_id_load_custom_preview(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    filepath: str = "",
    hide_props_region: bool = True,
    filter_blender: bool = False,
    filter_backup: bool = False,
    filter_image: bool = True,
    filter_movie: bool = False,
    filter_python: bool = False,
    filter_font: bool = False,
    filter_sound: bool = False,
    filter_text: bool = False,
    filter_archive: bool = False,
    filter_btx: bool = False,
    filter_collada: bool = False,
    filter_alembic: bool = False,
    filter_usd: bool = False,
    filter_volume: bool = False,
    filter_folder: bool = True,
    filter_blenlib: bool = False,
    filemode: int = 9,
    show_multiview: bool = False,
    use_multiview: bool = False,
    display_type: str = "DEFAULT",
    sort_method: str = "",
) -> set[str]: ...
def lib_id_unlink(
    execution_context: str = "EXEC_DEFAULT",
    /,
) -> set[str]: ...
def redo(
    execution_context: str = "EXEC_DEFAULT",
    /,
) -> set[str]: ...
def undo(
    execution_context: str = "EXEC_DEFAULT",
    /,
) -> set[str]: ...
def undo_history(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    item: int = 0,
) -> set[str]: ...
def undo_push(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    message: str = ...,
) -> set[str]: ...
def undo_redo(
    execution_context: str = "EXEC_DEFAULT",
    /,
) -> set[str]: ...
