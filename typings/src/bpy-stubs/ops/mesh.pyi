# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Sequence

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
def primitive_cube_add(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    size: float = 2.0,
    calc_uvs: bool = True,
    enter_editmode: bool = False,
    align: str = "WORLD",
    location: Sequence[float] = (0.0, 0.0, 0.0),
    rotation: Sequence[float] = (0.0, 0.0, 0.0),
    scale: Sequence[float] = (0.0, 0.0, 0.0),
) -> set[str]: ...
