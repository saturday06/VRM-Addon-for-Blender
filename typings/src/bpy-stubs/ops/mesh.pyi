# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
def select_all(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    action: str = "TOGGLE",
) -> set[str]: ...
def quads_convert_to_tris(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    quad_method: str = "BEAUTY",
    ngon_method: str = "BEAUTY",
) -> set[str]: ...
