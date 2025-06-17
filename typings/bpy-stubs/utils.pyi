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
        # 以下、ドキュメントには存在しないもの
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
        # 以下、ドキュメントには存在しないもの
        AddonPreferences
        | PropertyGroup
    ],
) -> None: ...
