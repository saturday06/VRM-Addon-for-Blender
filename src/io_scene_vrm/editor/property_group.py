# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import uuid
import warnings
from collections.abc import Iterator, Mapping, Sequence, ValuesView
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Optional, Protocol, TypeVar, overload

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
    ) -> Iterator[tuple["BonePropertyGroup", bool, bool]]:
        """Return (bone: BonePropertyGroup, is_vrm0: bool, is_vrm1: bool)."""
        from .extension import get_armature_extension

        armature_data = armature.data
        if not isinstance(armature_data, Armature):
            return
        ext = get_armature_extension(armature_data)
        yield ext.vrm0.first_person.first_person_bone, False, False
        for human_bone in ext.vrm0.humanoid.human_bones:
            yield human_bone.node, True, False
        for collider_group in ext.vrm0.secondary_animation.collider_groups:
            yield collider_group.node, False, False
        for bone_group in ext.vrm0.secondary_animation.bone_groups:
            yield bone_group.center, False, False
            yield from ((bone, False, False) for bone in bone_group.bones)
        for (
            human_bone
        ) in ext.vrm1.humanoid.human_bones.human_bone_name_to_human_bone().values():
            yield human_bone.node, False, True
        for collider in ext.spring_bone1.colliders:
            yield collider.node, False, False
        for spring in ext.spring_bone1.springs:
            yield spring.center, False, False
            for joint in spring.joints:
                yield joint.node, False, False

    @staticmethod
    def find_bone_candidates(
        armature_data: Armature,
        target: HumanBoneSpecification,
        bpy_bone_name_to_human_bone_specification: Mapping[str, HumanBoneSpecification],
        error_bpy_bone_names: Sequence[str],
    ) -> set[str]:
        bones = armature_data.bones
        human_bone_name_to_bpy_bone_name = {
            value.name: key
            for key, value in bpy_bone_name_to_human_bone_specification.items()
        }

        # targetの祖先のHuman Boneの割り当てがある場合はそこから探索を開始。
        # 無い場合はルートボーンから探索を開始。
        searching_bones: Optional[list[Bone]] = None
        ancestor = target.parent()
        while ancestor:
            ancestor_bpy_bone_name = human_bone_name_to_bpy_bone_name.get(ancestor.name)
            if ancestor_bpy_bone_name is not None and (
                ancestor_bpy_bone := bones.get(ancestor_bpy_bone_name)
            ):
                if ancestor_bpy_bone.name in error_bpy_bone_names:
                    return set()
                searching_bones = list(ancestor_bpy_bone.children)
                break
            ancestor = ancestor.parent()
        if not searching_bones:
            searching_bones = [bone for bone in bones.values() if not bone.parent]

        # 他の割り当て済みのHuman Boneにぶつかるまで、再帰的にボーンの名前を候補に追加
        bone_candidates: set[str] = set()
        while searching_bones:
            searching_bone = searching_bones.pop()
            human_bone_specification = bpy_bone_name_to_human_bone_specification.get(
                searching_bone.name
            )
            if human_bone_specification and human_bone_specification != target:
                continue
            bone_candidates.add(searching_bone.name)
            searching_bones.extend(searching_bone.children)

        return bone_candidates

    armature_data_name_and_bone_uuid_to_bone_name_cache: ClassVar[
        dict[tuple[str, str], str]
    ] = {}

    def get_bone_name(self) -> str:
        from .extension import get_bone_extension

        context = bpy.context

        if not self.bone_uuid:
            return ""
        if not self.armature_data_name:
            return ""

        cache_key = (self.armature_data_name, self.bone_uuid)
        cached_bone_name = self.armature_data_name_and_bone_uuid_to_bone_name_cache.get(
            cache_key
        )

        if cached_bone_name is not None:
            if cached_bone_name == "":
                return ""

            # armature_dataのチェックは実際に骨名が有効な場合のみ行う
            armature_data = context.blend_data.armatures.get(self.armature_data_name)
            if not armature_data:
                return ""

            if (
                cached_bone := armature_data.bones.get(cached_bone_name)
            ) and get_bone_extension(cached_bone).uuid == self.bone_uuid:
                return cached_bone_name
            # キャッシュに古い値が一つでも入っていたら安全のため全てクリア
            self.armature_data_name_and_bone_uuid_to_bone_name_cache.clear()

        armature_data = context.blend_data.armatures.get(self.armature_data_name)
        if not armature_data:
            self.armature_data_name_and_bone_uuid_to_bone_name_cache[cache_key] = ""
            return ""

        for bone in armature_data.bones:
            if get_bone_extension(bone).uuid == self.bone_uuid:
                self.armature_data_name_and_bone_uuid_to_bone_name_cache[cache_key] = (
                    bone.name
                )
                return bone.name

        self.armature_data_name_and_bone_uuid_to_bone_name_cache[cache_key] = ""
        return ""

    def set_bone_name(self, value: str) -> None:
        from .extension import get_armature_extension, get_bone_extension

        context = bpy.context

        armature: Optional[Object] = None
        bone_is_vrm0_human_bone = False
        bone_is_vrm1_human_bone = False

        # Reassign self.armature_data_name in case of armature duplication.
        self.search_one_time_uuid = uuid.uuid4().hex
        for found_armature in context.blend_data.objects:
            if found_armature.type != "ARMATURE":
                continue

            same_uuid_bone_found = False
            for (
                bone_property_group,
                found_bone_is_vrm0_human_bone,
                found_bone_is_vrm1_human_bone,
            ) in BonePropertyGroup.get_all_bone_property_groups(found_armature):
                if (
                    bone_property_group.search_one_time_uuid
                    == self.search_one_time_uuid
                ):
                    same_uuid_bone_found = True
                    bone_is_vrm0_human_bone = found_bone_is_vrm0_human_bone
                    bone_is_vrm1_human_bone = found_bone_is_vrm1_human_bone
                    break
            if not same_uuid_bone_found:
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
            bone_extension = get_bone_extension(bone)
            found_uuid = bone_extension.uuid
            if not found_uuid or found_uuid in found_uuids:
                bone_extension.uuid = uuid.uuid4().hex
            found_uuids.add(bone_extension.uuid)

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

        if ext.is_vrm0() and bone_is_vrm0_human_bone:
            self.update_all_vrm0_node_candidates(armature_data)
        if ext.is_vrm1() and bone_is_vrm1_human_bone:
            self.update_all_vrm1_node_candidates(armature_data)

    @staticmethod
    def update_all_vrm0_node_candidates(armature_data: Armature) -> None:
        from .extension import get_armature_extension

        ext = get_armature_extension(armature_data)

        bpy_bone_name_to_human_bone_specification: dict[
            str, vrm0_human_bone.HumanBoneSpecification
        ] = {}
        for human_bone in ext.vrm0.humanoid.human_bones:
            if not human_bone.node.bone_name:
                continue
            human_bone_name = vrm0_human_bone.HumanBoneName.from_str(human_bone.bone)
            if human_bone_name is None:
                continue
            bpy_bone_name_to_human_bone_specification[human_bone.node.bone_name] = (
                vrm0_human_bone.HumanBoneSpecifications.get(human_bone_name)
            )

        # 親ノードがエラーだと子ノードは必ずエラーになるため、親から順番に設定していく
        traversing_human_bone_specifications = [
            vrm0_human_bone.HumanBoneSpecifications.HIPS
        ]
        error_bpy_bone_names = []
        node_candidates_updated = True
        while traversing_human_bone_specifications:
            traversing_human_bone_specification = (
                traversing_human_bone_specifications.pop()
            )

            if node_candidates_updated:
                error_bpy_bone_names = [
                    error_human_bone.node.bone_name
                    for error_human_bone in ext.vrm0.humanoid.human_bones
                    if error_human_bone.node.bone_name
                    and error_human_bone.node.bone_name
                    not in error_human_bone.node_candidates
                ]

            human_bone = next(
                (
                    human_bone
                    for human_bone in ext.vrm0.humanoid.human_bones
                    if vrm0_human_bone.HumanBoneName.from_str(human_bone.bone)
                    == traversing_human_bone_specification.name
                ),
                None,
            )
            if human_bone:
                node_candidates_updated = human_bone.update_node_candidates(
                    armature_data,
                    bpy_bone_name_to_human_bone_specification,
                    error_bpy_bone_names,
                )

            traversing_human_bone_specifications.extend(
                traversing_human_bone_specification.children()
            )

    @staticmethod
    def update_all_vrm1_node_candidates(armature_data: Armature) -> None:
        from .extension import get_armature_extension

        ext = get_armature_extension(armature_data)

        human_bone_name_to_human_bone = (
            ext.vrm1.humanoid.human_bones.human_bone_name_to_human_bone()
        )
        bpy_bone_name_to_human_bone_specification: dict[
            str, vrm1_human_bone.HumanBoneSpecification
        ] = {}
        for human_bone_name, human_bone in human_bone_name_to_human_bone.items():
            if not human_bone.node.bone_name:
                continue
            bpy_bone_name_to_human_bone_specification[human_bone.node.bone_name] = (
                vrm1_human_bone.HumanBoneSpecifications.get(human_bone_name)
            )

        # 親ノードがエラーだと子ノードは必ずエラーになるため、親から順番に設定していく
        traversing_human_bone_specifications = [
            vrm1_human_bone.HumanBoneSpecifications.HIPS
        ]
        error_bpy_bone_names = []
        node_candidates_updated = True
        while traversing_human_bone_specifications:
            traversing_human_bone_specification = (
                traversing_human_bone_specifications.pop()
            )

            if node_candidates_updated:
                error_bpy_bone_names = [
                    error_human_bone.node.bone_name
                    for error_human_bone in human_bone_name_to_human_bone.values()
                    if error_human_bone.node.bone_name
                    and error_human_bone.node.bone_name
                    not in error_human_bone.node_candidates
                ]

            human_bone = human_bone_name_to_human_bone[
                traversing_human_bone_specification.name
            ]
            node_candidates_updated = human_bone.update_node_candidates(
                armature_data,
                traversing_human_bone_specification,
                bpy_bone_name_to_human_bone_specification,
                error_bpy_bone_names,
            )

            traversing_human_bone_specifications.extend(
                traversing_human_bone_specification.children()
            )

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
