# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from typing import TYPE_CHECKING

from bpy.props import BoolProperty
from bpy.types import PropertyGroup


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_springBone-1.0-beta/schema/VRMC_springBone.schema.json
class NodeConstraint1NodeConstraintPropertyGroup(PropertyGroup):
    # for UI
    show_expanded_roll_constraints: BoolProperty(  # type: ignore[valid-type]
        name="Roll Constraint"
    )
    show_expanded_aim_constraints: BoolProperty(  # type: ignore[valid-type]
        name="Aim Constraint"
    )
    show_expanded_rotation_constraints: BoolProperty(  # type: ignore[valid-type]
        name="Rotation Constraint"
    )
    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        show_expanded_roll_constraints: bool  # type: ignore[no-redef]
        show_expanded_aim_constraints: bool  # type: ignore[no-redef]
        show_expanded_rotation_constraints: bool  # type: ignore[no-redef]
