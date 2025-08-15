# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import uuid
import warnings
from collections.abc import Iterator, ValuesView
from dataclasses import dataclass
from enum import Enum
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Optional,
    Protocol,
    TypeVar,
    overload,
)

import bpy
from bpy.props import FloatProperty, PointerProperty, StringProperty
from bpy.types import Armature, Context, Material, Object, PropertyGroup

from ..common.logger import get_logger
from ..common.vrm0 import human_bone as vrm0_human_bone
from ..common.vrm1 import human_bone as vrm1_human_bone

HumanBoneSpecification = TypeVar(
    "HumanBoneSpecification",
    vrm0_human_bone.HumanBoneSpecification,
    vrm1_human_bone.HumanBoneSpecification,
)

logger = get_logger(__name__)


# https://docs.blender.org/api/2.93/bpy.types.EnumPropertyItem.html#bpy.types.EnumPropertyItem
@dataclass(frozen=True)
class PropertyGroupEnumItem:
    identifier: str
    name: str
    description: str
    icon: str
    value: int

    @staticmethod
    def from_enum_property_items(
        items: tuple[tuple[str, str, str, str, int], ...],
    ) -> tuple[tuple[str, ...], tuple[int, ...], tuple["PropertyGroupEnumItem", ...]]:
        enum_items = tuple(
            PropertyGroupEnumItem(
                identifier=identifier,
                name=name,
                description=description,
                icon=icon,
                value=value,
            )
            for identifier, name, description, icon, value in items
        )
        identifiers = tuple(enum_item.identifier for enum_item in enum_items)
        values = tuple(enum_item.value for enum_item in enum_items)
        return identifiers, values, enum_items


class PropertyGroupEnum:
    def __init__(self, enum_items: tuple[tuple[str, str, str, str, int], ...]) -> None:
        self.enum_items = enum_items

    def items(self) -> tuple[tuple[str, str, str, str, int], ...]:
        return self.enum_items

    def value_to_identifier(self, value: int, default: str) -> str:
        return next(
            (enum.identifier for enum in self if enum.value == value),
            default,
        )

    def identifier_to_value(self, identifier: str, default: int) -> int:
        return next(
            (enum.value for enum in self if enum.identifier == identifier),
            default,
        )

    def identifiers(self) -> tuple[str, ...]:
        return tuple(enum.identifier for enum in self)

    def values(self) -> tuple[int, ...]:
        return tuple(enum.value for enum in self)

    def __iter__(self) -> Iterator[PropertyGroupEnumItem]:
        return (
            PropertyGroupEnumItem(
                identifier=identifier,
                name=name,
                description=description,
                icon=icon,
                value=value,
            )
            for identifier, name, description, icon, value in self.items()
        )


def property_group_enum(
    *items: tuple[str, str, str, str, int],
) -> tuple[PropertyGroupEnum, Iterator[PropertyGroupEnumItem]]:
    enum = PropertyGroupEnum(items)
    return enum, enum.__iter__()


class StringPropertyGroup(PropertyGroup):
    def get_value(self) -> str:
        value = self.get("value")
        if isinstance(value, str):
            return value
        return str(value)

    def set_value(self, value: str) -> None:
        self.name = value
        self["value"] = value

    value: StringProperty(  # type: ignore[valid-type]
        name="String Value",
        get=get_value,
        set=set_value,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        value: str  # type: ignore[no-redef]


class FloatPropertyGroup(PropertyGroup):
    def get_value(self) -> float:
        value = self.get("value")
        if isinstance(value, (float, int)):
            return float(value)
        return 0.0

    def set_value(self, value: float) -> None:
        self.name = str(value)
        self["value"] = value

    value: FloatProperty(  # type: ignore[valid-type]
        name="Float Value",
        get=get_value,
        set=set_value,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        value: float  # type: ignore[no-redef]


class MeshObjectPropertyGroup(PropertyGroup):
    def get_mesh_object_name(self) -> str:
        bpy_object = self.bpy_object
        if not bpy_object or not bpy_object.name or bpy_object.type != "MESH":
            return ""
        return str(bpy_object.name)

    def set_mesh_object_name(self, value: object) -> None:
        context = bpy.context

        if (
            not isinstance(value, str)
            or not (obj := context.blend_data.objects.get(value))
            or obj.type != "MESH"
        ):
            if self.bpy_object:
                self.bpy_object = None
            return

        if self.bpy_object != obj:
            self.bpy_object = obj

    mesh_object_name: StringProperty(  # type: ignore[valid-type]
        get=get_mesh_object_name, set=set_mesh_object_name
    )

    saved_mesh_object_name_to_restore: StringProperty()  # type: ignore[valid-type]

    def get_value(self) -> str:
        message = (
            "`MeshObjectPropertyGroup.value` is deprecated and will be removed in the"
            " next major release. Please use `MeshObjectPropertyGroup.mesh_object_name`"
            " instead."
        )
        logger.warning(message)
        warnings.warn(message, DeprecationWarning, stacklevel=5)
        return str(self.mesh_object_name)

    def set_value(self, value: str) -> None:
        message = (
            "`MeshObjectPropertyGroup.value` is deprecated and will be removed in the"
            " next major release. Please use `MeshObjectPropertyGroup.mesh_object_name`"
            " instead."
        )
        logger.warning(message)
        warnings.warn(message, DeprecationWarning, stacklevel=5)
        self.mesh_object_name = value

    value: StringProperty(  # type: ignore[valid-type]
        get=get_value,
        set=set_value,
    )
    """`value` is deprecated and will be removed in the next
    major release. Please use `mesh_object_name` instead.
    """

    def poll_bpy_object(self, obj: object) -> bool:
        return isinstance(obj, Object) and obj.type == "MESH"

    def update_bpy_object(self, _context: Context) -> None:
        bpy_object = self.bpy_object
        self.saved_mesh_object_name_to_restore = bpy_object.name if bpy_object else ""

    bpy_object: PointerProperty(  # type: ignore[valid-type]
        type=Object,
        poll=poll_bpy_object,
        update=update_bpy_object,
    )

    def restore_object_assignment(self, context: Context) -> None:
        if self.bpy_object:
            return
        obj = context.blend_data.objects.get(self.saved_mesh_object_name_to_restore)
        if not obj:
            return
        self.set_mesh_object_name(obj.name)

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        mesh_object_name: str  # type: ignore[no-redef]
        saved_mesh_object_name_to_restore: str  # type: ignore[no-redef]
        value: str  # type: ignore[no-redef]
        bpy_object: Optional[Object]  # type: ignore[no-redef]


class MaterialPropertyGroup(PropertyGroup):
    material: PointerProperty(  # type: ignore[valid-type]
        type=Material,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        material: Optional[Material]  # type: ignore[no-redef]


class BonePropertyGroupType(Enum):
    VRM0_FIRST_PERSON = 1
    VRM0_HUMAN = 2
    VRM0_COLLIDER_GROUP = 3
    VRM0_BONE_GROUP_CENTER = 4
    VRM0_BONE_GROUP = 5
    VRM1_HUMAN = 6
    SPRING_BONE1_COLLIDER = 7
    SPRING_BONE1_SPRING_CENTER = 8
    SPRING_BONE1_SPRING_JOINT = 9

    @staticmethod
    def is_vrm0(bone_property_group_type: "BonePropertyGroupType") -> bool:
        return bone_property_group_type in {
            BonePropertyGroupType.VRM0_FIRST_PERSON,
            BonePropertyGroupType.VRM0_HUMAN,
            BonePropertyGroupType.VRM0_COLLIDER_GROUP,
            BonePropertyGroupType.VRM0_BONE_GROUP_CENTER,
            BonePropertyGroupType.VRM0_BONE_GROUP,
        }

    @staticmethod
    def is_vrm1(bone_property_group_type: "BonePropertyGroupType") -> bool:
        return bone_property_group_type in {
            BonePropertyGroupType.VRM1_HUMAN,
            BonePropertyGroupType.SPRING_BONE1_COLLIDER,
            BonePropertyGroupType.SPRING_BONE1_SPRING_CENTER,
            BonePropertyGroupType.SPRING_BONE1_SPRING_JOINT,
        }


class BonePropertyGroup(PropertyGroup):
    armature_data_name_and_bone_uuid_to_bone_name_cache: ClassVar[
        dict[tuple[str, str], str]
    ] = {}

    def get_bone_name(self) -> str:
        from .extension import get_bone_extension

        if not self.bone_uuid:
            return ""

        armature_data = self.find_armature()

        # Use cache to speed up this function since profiling showed it was slow
        cache_key = (armature_data.name, self.bone_uuid)
        cached_bone_name = self.armature_data_name_and_bone_uuid_to_bone_name_cache.get(
            cache_key
        )
        if cached_bone_name is not None:
            if (
                cached_bone := armature_data.bones.get(cached_bone_name)
            ) and get_bone_extension(cached_bone).uuid == self.bone_uuid:
                return cached_bone_name
            # If there's even one old value in the cache, clear everything for safety
            self.armature_data_name_and_bone_uuid_to_bone_name_cache.clear()

        for bone in armature_data.bones:
            if get_bone_extension(bone).uuid == self.bone_uuid:
                self.armature_data_name_and_bone_uuid_to_bone_name_cache[cache_key] = (
                    bone.name
                )
                return bone.name

        return ""

    def find_armature(self) -> Armature:
        id_data = self.id_data
        if isinstance(id_data, Armature):
            return id_data

        message = (
            f"{type(self)}/{self}.id_data is not a {Armature}"
            + f" but {type(id_data)}/{id_data}"
        )
        raise AssertionError(message)

    def set_bone_name(self, value: str) -> None:
        from .extension import get_bone_extension

        armature_data = self.find_armature()

        # Assign UUIDs and regenerate it if duplication exist
        found_uuids: set[str] = set()
        for bone in armature_data.bones:
            bone_extension = get_bone_extension(bone)
            found_uuid = bone_extension.uuid
            if not found_uuid or found_uuid in found_uuids:
                bone_extension.uuid = uuid.uuid4().hex
                self.armature_data_name_and_bone_uuid_to_bone_name_cache.clear()
            found_uuids.add(bone_extension.uuid)

        if not value or not (bone := armature_data.bones.get(value)):
            if not self.bone_uuid:
                # Not changed
                return
            self.bone_uuid = ""
        elif self.bone_uuid and self.bone_uuid == get_bone_extension(bone).uuid:
            # Not changed
            return
        else:
            self.bone_uuid = get_bone_extension(bone).uuid

    bone_name: StringProperty(  # type: ignore[valid-type]
        name="Bone",
        get=get_bone_name,
        set=set_bone_name,
    )

    def get_value(self) -> str:
        message = (
            "`BonePropertyGroup.value` is deprecated and will be removed in the"
            " next major release. Please use `BonePropertyGroup.bone_name` instead."
        )
        logger.warning(message)
        warnings.warn(message, DeprecationWarning, stacklevel=5)
        return str(self.bone_name)

    def set_value(self, value: str) -> None:
        message = (
            "`BonePropertyGroup.value` is deprecated and will be removed in the"
            " next major release. Please use `BonePropertyGroup.bone_name` instead."
        )
        logger.warning(message)
        warnings.warn(message, DeprecationWarning, stacklevel=5)
        self.bone_name = value

    value: StringProperty(  # type: ignore[valid-type]
        name="Bone",
        get=get_value,
        set=set_value,
    )
    """`value` is deprecated and will be removed in the next major
    release. Please use `bone_name` instead."
    """

    bone_uuid: StringProperty()  # type: ignore[valid-type]
    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        bone_name: str  # type: ignore[no-redef]
        value: str  # type: ignore[no-redef]
        bone_uuid: str  # type: ignore[no-redef]


T_co = TypeVar("T_co", covariant=True)


# The actual type does not take type arguments.
class CollectionPropertyProtocol(Protocol[T_co]):
    def add(self) -> T_co: ...  # TODO: undocumented

    def __len__(self) -> int: ...  # TODO: undocumented

    def __iter__(self) -> Iterator[T_co]: ...  # TODO: undocumented

    def clear(self) -> None: ...  # TODO: undocumented

    @overload
    def __getitem__(self, index: int) -> T_co: ...  # TODO: undocumented

    @overload
    def __getitem__(
        self, index: "slice[Optional[int], Optional[int], Optional[int]]"
    ) -> tuple[T_co, ...]: ...  # TODO: undocumented

    def remove(self, index: int) -> None: ...  # TODO: undocumented

    def values(self) -> ValuesView[T_co]: ...  # TODO: undocumented

    def __contains__(self, value: str) -> bool: ...  # TODO: undocumented

    def move(self, from_index: int, to_index: int) -> None: ...  # TODO: undocumented
