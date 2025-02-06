# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import uuid
from collections.abc import Iterator, ValuesView
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Protocol, TypeVar, overload

import bpy
from bpy.props import FloatProperty, PointerProperty, StringProperty
from bpy.types import Armature, Bone, Material, Object, PropertyGroup

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
        if (
            not self.bpy_object
            or not self.bpy_object.name
            or self.bpy_object.type != "MESH"
        ):
            return ""
        return str(self.bpy_object.name)

    def set_mesh_object_name(self, value: object) -> None:
        context = bpy.context

        if (
            not isinstance(value, str)
            or value not in context.blend_data.objects
            or context.blend_data.objects[value].type != "MESH"
        ):
            self.bpy_object = None
            return
        self.bpy_object = context.blend_data.objects[value]

    mesh_object_name: StringProperty(  # type: ignore[valid-type]
        get=get_mesh_object_name, set=set_mesh_object_name
    )

    def get_value(self) -> str:
        logger.warning(
            "MeshObjectPropertyGroup.value is deprecated."
            " Use MeshObjectPropertyGroup.mesh_object_name instead."
        )
        return str(self.mesh_object_name)

    def set_value(self, value: str) -> None:
        logger.warning(
            "MeshObjectPropertyGroup.value is deprecated."
            " Use MeshObjectPropertyGroup.mesh_object_name instead."
        )
        self.mesh_object_name = value

    # "value" is deprecated. Use "mesh_object_name" instead
    value: StringProperty(  # type: ignore[valid-type]
        get=get_value,
        set=set_value,
    )

    def poll_bpy_object(self, obj: object) -> bool:
        return isinstance(obj, Object) and obj.type == "MESH"

    bpy_object: PointerProperty(  # type: ignore[valid-type]
        type=Object,
        poll=poll_bpy_object,
    )

    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        mesh_object_name: str  # type: ignore[no-redef]
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


class BonePropertyGroup(PropertyGroup):
    @staticmethod
    def get_all_bone_property_groups(
        armature: Object,
    ) -> Iterator["BonePropertyGroup"]:
        from .extension import get_armature_extension

        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        ext = get_armature_extension(armature_data)
        yield ext.vrm0.first_person.first_person_bone
        for human_bone in ext.vrm0.humanoid.human_bones:
            yield human_bone.node
        for collider_group in ext.vrm0.secondary_animation.collider_groups:
            yield collider_group.node
        for bone_group in ext.vrm0.secondary_animation.bone_groups:
            yield bone_group.center
            yield from bone_group.bones
        for (
            human_bone
        ) in ext.vrm1.humanoid.human_bones.human_bone_name_to_human_bone().values():
            yield human_bone.node
        for collider in ext.spring_bone1.colliders:
            yield collider.node
        for spring in ext.spring_bone1.springs:
            yield spring.center
            for joint in spring.joints:
                yield joint.node

    @staticmethod
    def find_bone_candidates(
        armature_data: Armature,
        target: HumanBoneSpecification,
        bpy_bone_name_to_human_bone_specification: dict[str, HumanBoneSpecification],
    ) -> set[str]:
        bones = armature_data.bones
        root_bones = [bone for bone in bones.values() if not bone.parent]
        result: set[str] = set(bones.keys())
        remove_bones_tree: set[Bone] = set()

        for (
            bpy_bone_name,
            human_bone_specification,
        ) in bpy_bone_name_to_human_bone_specification.items():
            if human_bone_specification == target:
                continue

            parent = bones.get(bpy_bone_name)
            if not parent:
                continue

            if human_bone_specification.is_ancestor_of(target):
                remove_ancestors = True
                remove_ancestor_branches = True
            elif target.is_ancestor_of(human_bone_specification):
                remove_bones_tree.add(parent)
                remove_ancestors = False
                remove_ancestor_branches = True
            else:
                remove_bones_tree.add(parent)
                remove_ancestors = True
                remove_ancestor_branches = False

            while True:
                if remove_ancestors and parent.name in result:
                    result.remove(parent.name)
                grand_parent = parent.parent
                if not grand_parent:
                    if remove_ancestor_branches:
                        remove_bones_tree.update(
                            root_bone for root_bone in root_bones if root_bone != parent
                        )
                    break

                if remove_ancestor_branches:
                    for grand_parent_child in grand_parent.children:
                        if grand_parent_child != parent:
                            remove_bones_tree.add(grand_parent_child)

                parent = grand_parent

        while remove_bones_tree:
            child = remove_bones_tree.pop()
            if child.name in result:
                result.remove(child.name)
            remove_bones_tree.update(child.children)

        return result

    def get_bone_name(self) -> str:
        from .extension import get_bone_extension

        context = bpy.context

        if not self.bone_uuid:
            return ""
        if not self.armature_data_name:
            return ""
        armature_data = context.blend_data.armatures.get(self.armature_data_name)
        if not armature_data:
            return ""

        # TODO: Optimization
        for bone in armature_data.bones:
            if get_bone_extension(bone).uuid == self.bone_uuid:
                return bone.name

        return ""

    def set_bone_name_and_refresh_node_candidates(self, value: object) -> None:
        self.set_bone_name(
            None if value is None else str(value), refresh_node_candidates=True
        )

    def set_bone_name(
        self, value: Optional[str], *, refresh_node_candidates: bool = False
    ) -> None:
        from .extension import get_armature_extension, get_bone_extension

        context = bpy.context

        armature: Optional[Object] = None

        # Reassign self.armature_data_name in case of armature duplication.
        self.search_one_time_uuid = uuid.uuid4().hex
        for found_armature in context.blend_data.objects:
            if found_armature.type != "ARMATURE":
                continue
            if all(
                bone_property_group.search_one_time_uuid != self.search_one_time_uuid
                for bone_property_group in (
                    BonePropertyGroup.get_all_bone_property_groups(found_armature)
                )
            ):
                continue
            armature = found_armature
            break
        if not armature:
            self.armature_data_name = ""
            self.bone_uuid = ""
            return

        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            self.armature_data_name = ""
            self.bone_uuid = ""
            return

        self.armature_data_name = armature_data.name

        # Reassign UUIDs if duplicate UUIDs exist in case of bone duplication.
        found_uuids: set[str] = set()
        for bone in armature_data.bones:
            found_uuid = get_bone_extension(bone).uuid
            if not found_uuid or found_uuid in found_uuids:
                get_bone_extension(bone).uuid = uuid.uuid4().hex
            found_uuids.add(get_bone_extension(bone).uuid)

        if not value or value not in armature_data.bones:
            if not self.bone_uuid:
                return
            self.bone_uuid = ""
        elif (
            self.bone_uuid
            and self.bone_uuid == get_bone_extension(armature_data.bones[value]).uuid
        ):
            return
        else:
            bone = armature_data.bones[value]
            self.bone_uuid = get_bone_extension(bone).uuid

        ext = get_armature_extension(armature_data)
        for collider_group in ext.vrm0.secondary_animation.collider_groups:
            collider_group.refresh(armature)

        if not refresh_node_candidates:
            return

        vrm0_bpy_bone_name_to_human_bone_specification: dict[
            str, vrm0_human_bone.HumanBoneSpecification
        ] = {
            human_bone.node.bone_name: vrm0_human_bone.HumanBoneSpecifications.get(
                vrm0_human_bone.HumanBoneName(human_bone.bone)
            )
            for human_bone in ext.vrm0.humanoid.human_bones
            if human_bone.node.bone_name
            and vrm0_human_bone.HumanBoneName.from_str(human_bone.bone) is not None
        }

        for human_bone in ext.vrm0.humanoid.human_bones:
            human_bone.update_node_candidates(
                armature_data,
                vrm0_bpy_bone_name_to_human_bone_specification,
            )

        human_bone_name_to_human_bone = (
            ext.vrm1.humanoid.human_bones.human_bone_name_to_human_bone()
        )
        vrm1_bpy_bone_name_to_human_bone_specification: dict[
            str, vrm1_human_bone.HumanBoneSpecification
        ] = {
            human_bone.node.bone_name: vrm1_human_bone.HumanBoneSpecifications.get(
                human_bone_name
            )
            for human_bone_name, human_bone in human_bone_name_to_human_bone.items()
            if human_bone.node.bone_name
        }

        for (
            human_bone_name,
            human_bone,
        ) in human_bone_name_to_human_bone.items():
            human_bone.update_node_candidates(
                armature_data,
                vrm1_human_bone.HumanBoneSpecifications.get(human_bone_name),
                vrm1_bpy_bone_name_to_human_bone_specification,
            )

    bone_name: StringProperty(  # type: ignore[valid-type]
        name="Bone",
        get=get_bone_name,
        set=set_bone_name_and_refresh_node_candidates,
    )

    def get_value(self) -> str:
        logger.warning(
            "BonePropertyGroup.value is deprecated."
            " Use BonePropertyGroup.bone_name instead."
        )
        return str(self.bone_name)

    def set_value(self, value: str) -> None:
        logger.warning(
            "BonePropertyGroup.value is deprecated."
            " Use BonePropertyGroup.bone_name instead."
        )
        self.bone_name = value

    # "value" is deprecated. Use "bone_name" instead
    value: StringProperty(  # type: ignore[valid-type]
        name="Bone",
        get=get_value,
        set=set_value,
    )
    bone_uuid: StringProperty()  # type: ignore[valid-type]
    armature_data_name: StringProperty()  # type: ignore[valid-type]
    search_one_time_uuid: StringProperty()  # type: ignore[valid-type]
    if TYPE_CHECKING:
        # This code is auto generated.
        # To regenerate, run the `uv run tools/property_typing.py` command.
        bone_name: str  # type: ignore[no-redef]
        value: str  # type: ignore[no-redef]
        bone_uuid: str  # type: ignore[no-redef]
        armature_data_name: str  # type: ignore[no-redef]
        search_one_time_uuid: str  # type: ignore[no-redef]


T_co = TypeVar("T_co", covariant=True)


# The actual type does not take type arguments.
class CollectionPropertyProtocol(Protocol[T_co]):
    def add(self) -> T_co: ...  # TODO: undocumented

    def __len__(self) -> int: ...  # TODO: undocumented

    def __iter__(self) -> Iterator[T_co]: ...  # TODO: undocumented

    def clear(self) -> None: ...  # TODO: undocumented

    @overload
    def __getitem__(
        self, index: "slice[Optional[int], Optional[int], Optional[int]]"
    ) -> tuple[T_co, ...]: ...  # TODO: undocumented

    @overload
    def __getitem__(self, index: int) -> T_co: ...  # TODO: undocumented

    def remove(self, index: int) -> None: ...  # TODO: undocumented

    def values(self) -> ValuesView[T_co]: ...  # TODO: undocumented

    def __contains__(self, value: str) -> bool: ...  # TODO: undocumented

    def move(self, from_index: int, to_index: int) -> None: ...  # TODO: undocumented
