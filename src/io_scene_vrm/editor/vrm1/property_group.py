# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from typing import TYPE_CHECKING

from bpy.props import (
    CollectionProperty,
    IntProperty,
    PointerProperty,
)
from bpy.types import (
    Armature,
    PropertyGroup,
)

from ...common.logger import get_logger
from ..property_group import (
    StringPropertyGroup,
)

if TYPE_CHECKING:
    from ..property_group import CollectionPropertyProtocol


logger = get_logger(__name__)


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.humanoid.humanBones.schema.json
class Vrm1HumanBonesPropertyGroup(PropertyGroup):
    # for UI
    last_bone_names: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        last_bone_names: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.humanoid.schema.json
class Vrm1HumanoidPropertyGroup(PropertyGroup):
    human_bones: PointerProperty(type=Vrm1HumanBonesPropertyGroup)  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        human_bones: Vrm1HumanBonesPropertyGroup  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.expressions.schema.json
class Vrm1ExpressionsPropertyGroup(PropertyGroup):
    expression_ui_list_elements: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )
    active_expression_ui_list_element_index: IntProperty(min=0)  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        expression_ui_list_elements: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]
        active_expression_ui_list_element_index: int  # type: ignore[no-redef]


# https://github.com/vrm-c/vrm-specification/blob/6fb6baaf9b9095a84fb82c8384db36e1afeb3558/specification/VRMC_vrm-1.0-beta/schema/VRMC_vrm.schema.json
class Vrm1PropertyGroup(PropertyGroup):
    humanoid: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1HumanoidPropertyGroup
    )
    expressions: PointerProperty(  # type: ignore[valid-type]
        type=Vrm1ExpressionsPropertyGroup
    )
    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        humanoid: Vrm1HumanoidPropertyGroup  # type: ignore[no-redef]
        expressions: Vrm1ExpressionsPropertyGroup  # type: ignore[no-redef]


def get_armature_vrm1_extension(armature: Armature) -> Vrm1PropertyGroup:
    from ..extension import get_armature_extension

    vrm1: Vrm1PropertyGroup = get_armature_extension(armature).vrm1
    return vrm1
