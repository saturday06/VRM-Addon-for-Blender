# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
def render(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    animation: bool = False,
    write_still: bool = False,
    use_viewport: bool = False,
    layer: str = "",
    scene: str = "",
) -> set[str]: ...
