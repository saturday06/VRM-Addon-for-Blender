# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
def smart_project(
    execution_context: str = "EXEC_DEFAULT",
    /,
    *,
    angle_limit: float = 1.15192,
    margin_method: str = "SCALED",
    island_margin: float = 0.0,
    area_weight: float = 0.0,
    correct_aspect: bool = True,
    scale_to_bounds: bool = False,
) -> bool: ...
