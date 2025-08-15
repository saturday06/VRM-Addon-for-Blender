# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
# SPDX-FileCopyrightText: 2018 iCyP

from typing import Union

import bpy
from bpy.props import PointerProperty
from bpy.types import (
    AddonPreferences,
    Armature,
    Header,
    KeyingSetInfo,
    Menu,
    Operator,
    Panel,
    PropertyGroup,
    RenderEngine,
    UIList,
)

from .common.logger import get_logger
from .editor import (
    extension,
    property_group,
)
from .editor.vrm1 import panel as vrm1_panel
from .editor.vrm1 import property_group as vrm1_property_group
from .editor.vrm1 import ui_list as vrm1_ui_list

logger = get_logger(__name__)


classes: list[
    Union[
        type[Panel],
        type[UIList],
        type[Menu],
        type[Header],
        type[Operator],
        type[KeyingSetInfo],
        type[RenderEngine],
        type[AddonPreferences],
        type[PropertyGroup],
        type["bpy.types.FileHandler"],  # bpy.app.version >= (4, 1, 0)
    ]
] = [
    property_group.StringPropertyGroup,
    vrm1_property_group.Vrm1HumanBonesPropertyGroup,
    vrm1_property_group.Vrm1HumanoidPropertyGroup,
    vrm1_property_group.Vrm1ExpressionsPropertyGroup,
    vrm1_property_group.Vrm1PropertyGroup,
    vrm1_panel.VRM_PT_vrm1_expressions_ui,
    vrm1_ui_list.VRM_UL_vrm1_expression,
    extension.VrmAddonArmatureExtensionPropertyGroup,
]


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)

    Armature.vrm_addon_extension = PointerProperty(  # type: ignore[attr-defined, assignment, unused-ignore]
        type=extension.VrmAddonArmatureExtensionPropertyGroup
    )


def unregister() -> None:
    if hasattr(Armature, "vrm_addon_extension"):
        del Armature.vrm_addon_extension  # pyright: ignore [reportAttributeAccessIssue]

    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            logger.exception("Failed to unregister %s", cls)
