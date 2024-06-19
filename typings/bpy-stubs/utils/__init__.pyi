from typing import Union

from bpy.types import (
    AddonPreferences,
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
        Union[
            Panel,
            UIList,
            Menu,
            Header,
            Operator,
            KeyingSetInfo,
            RenderEngine,
            # 以下、ドキュメントには存在しないもの
            AddonPreferences,
            PropertyGroup,
        ]
    ],
) -> None: ...
def unregister_class(
    t: type[
        Union[
            Panel,
            UIList,
            Menu,
            Header,
            Operator,
            KeyingSetInfo,
            RenderEngine,
            # 以下、ドキュメントには存在しないもの
            AddonPreferences,
            PropertyGroup,
        ]
    ],
) -> None: ...
