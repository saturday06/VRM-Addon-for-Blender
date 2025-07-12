# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from bpy.types import (
    AddonPreferences,
    FileHandler,
    Header,
    KeyingSetInfo,
    Menu,
    Operator,
    Panel,
    PropertyGroup,
    RenderEngine,
    UIList,
)

def register_class(
    t: type[
        FileHandler
        | Panel
        | UIList
        | Menu
        | Header
        | Operator
        | KeyingSetInfo
        | RenderEngine
        |
        # The following do not exist in documentation
        AddonPreferences
        | PropertyGroup
    ],
) -> None: ...
def unregister_class(
    t: type[
        FileHandler
        | Panel
        | UIList
        | Menu
        | Header
        | Operator
        | KeyingSetInfo
        | RenderEngine
        |
        # The following do not exist in documentation
        AddonPreferences
        | PropertyGroup
    ],
) -> None: ...
