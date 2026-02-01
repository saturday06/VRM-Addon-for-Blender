# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from typing import TYPE_CHECKING, Optional

from bpy.props import (
    CollectionProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import (
    Image,
    PropertyGroup,
)

from ..property_group import StringPropertyGroup

if TYPE_CHECKING:
    from ..property_group import CollectionPropertyProtocol


class KhrXmpJsonLdKhrCharacterPacketPropertyGroup(PropertyGroup):
    dc_title: StringProperty(  # type: ignore[valid-type]
        name="Title"
    )
    dc_creator: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )
    dc_license: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )
    dc_created: StringProperty(  # type: ignore[valid-type]
        name="Created Date"
    )
    dc_rights: StringProperty(  # type: ignore[valid-type]
        name="Rights"
    )
    dc_publisher: StringProperty(  # type: ignore[valid-type]
        name="Publisher"
    )
    dc_description: StringProperty(  # type: ignore[valid-type]
        name="Description"
    )
    dc_subject: CollectionProperty(  # type: ignore[valid-type]
        type=StringPropertyGroup
    )
    dc_source: StringProperty(  # type: ignore[valid-type]
        name="Source"
    )
    khr_version: StringProperty(  # type: ignore[valid-type]
        name="Version"
    )
    khr_thumbnail_image: PointerProperty(  # type: ignore[valid-type]
        type=Image
    )

    # for UI
    active_dc_creator_index: IntProperty(min=0)  # type: ignore[valid-type]
    active_dc_license_index: IntProperty(min=0)  # type: ignore[valid-type]
    active_dc_subject_index: IntProperty(min=0)  # type: ignore[valid-type]

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        dc_title: str  # type: ignore[no-redef]
        dc_creator: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]
        dc_license: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]
        dc_created: str  # type: ignore[no-redef]
        dc_rights: str  # type: ignore[no-redef]
        dc_publisher: str  # type: ignore[no-redef]
        dc_description: str  # type: ignore[no-redef]
        dc_subject: CollectionPropertyProtocol[  # type: ignore[no-redef]
            StringPropertyGroup
        ]
        dc_source: str  # type: ignore[no-redef]
        khr_version: str  # type: ignore[no-redef]
        khr_thumbnail_image: Optional[Image]  # type: ignore[no-redef]
        active_dc_creator_index: int  # type: ignore[no-redef]
        active_dc_license_index: int  # type: ignore[no-redef]
        active_dc_subject_index: int  # type: ignore[no-redef]
