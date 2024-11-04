# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
def delete(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    use_global: bool = False,
    confirm: bool = True,
) -> set[str]: ...
def mode_set(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    mode: str = "OBJECT",
    toggle: bool = False,
) -> set[str]: ...
def select_all(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    action: str = "TOGGLE",
) -> set[str]: ...
def shade_smooth(
    execution_context: str = "EXEC_DEFAULT",
    /,
) -> set[str]: ...
def modifier_add(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    type: str = "SUBSURF",
) -> set[str]: ...
def transform_apply(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    location: bool = True,
    rotation: bool = True,
    scale: bool = True,
    properties: bool = True,
) -> set[str]: ...
def add(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    radius: float = 1.0,
    type: str = "EMPTY",
    enter_editmode: bool = False,
    align: str = "WORLD",
    location: tuple[float, float, float] = (0.0, 0.0, 0.0),
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    scale: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> set[str]: ...
def convert(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    target: str = "MESH",
    keep_original: bool = False,
    angle: float = 1.22173,
    thickness: int = 5,
    seams: bool = False,
    faces: bool = True,
    offset: float = 0.01,
) -> set[str]: ...
def origin_set(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    type: str = "GEOMETRY_ORIGIN",
    center: str = "MEDIAN",
) -> set[str]: ...
def shape_key_add(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    from_mix: bool = True,
) -> set[str]: ...
def parent_set(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    type: str = "OBJECT",
    xmirror: bool = False,
    keep_transform: bool = False,
) -> set[str]: ...
def vertex_group_limit_total(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    group_select_mode: str = "",
    limit: int = 4,
) -> set[str]: ...
