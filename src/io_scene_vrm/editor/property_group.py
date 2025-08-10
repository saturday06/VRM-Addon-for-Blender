# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import uuid
import warnings
from collections.abc import Iterator, Mapping, Sequence, ValuesView
from dataclasses import dataclass
from enum import Enum
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Final,
    Optional,
    Protocol,
    TypeVar,
    Union,
    overload,
)

import bpy
from bpy.app.translations import pgettext
from bpy.props import FloatProperty, PointerProperty, StringProperty
from bpy.types import Armature, Bone, Context, Material, Object, PropertyGroup, UILayout

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
    @staticmethod
    def get_all_bone_property_groups(
        armature: Union[Object, Armature],
    ) -> Iterator[tuple["BonePropertyGroup", BonePropertyGroupType]]:
        """Return (bone: BonePropertyGroup, is_vrm0: bool, is_vrm1: bool)."""
        from .extension import get_armature_extension

        if isinstance(armature, Object):
            armature_data = armature.data
            if not isinstance(armature_data, Armature):
                return
        else:
            armature_data = armature

        ext = get_armature_extension(armature_data)
        yield (
            ext.vrm0.first_person.first_person_bone,
            BonePropertyGroupType.VRM0_FIRST_PERSON,
        )
        for human_bone in ext.vrm0.humanoid.human_bones:
            yield human_bone.node, BonePropertyGroupType.VRM0_HUMAN
        for collider_group in ext.vrm0.secondary_animation.collider_groups:
            yield collider_group.node, BonePropertyGroupType.VRM0_COLLIDER_GROUP
        for bone_group in ext.vrm0.secondary_animation.bone_groups:
            yield bone_group.center, BonePropertyGroupType.VRM0_BONE_GROUP_CENTER
            yield from (
                (bone, BonePropertyGroupType.VRM0_BONE_GROUP)
                for bone in bone_group.bones
            )
        for (
            human_bone
        ) in ext.vrm1.humanoid.human_bones.human_bone_name_to_human_bone().values():
            yield human_bone.node, BonePropertyGroupType.VRM1_HUMAN
        for collider in ext.spring_bone1.colliders:
            yield collider.node, BonePropertyGroupType.SPRING_BONE1_COLLIDER
        for spring in ext.spring_bone1.springs:
            yield spring.center, BonePropertyGroupType.SPRING_BONE1_SPRING_CENTER
            for joint in spring.joints:
                yield joint.node, BonePropertyGroupType.SPRING_BONE1_SPRING_JOINT

    @staticmethod
    def find_bone_candidates(
        armature_data: Armature,
        target: HumanBoneSpecification,
        bpy_bone_name_to_human_bone_specification: Mapping[str, HumanBoneSpecification],
        error_bpy_bone_names: Sequence[str],
        diagnostics_layout: Optional[UILayout] = None,
    ) -> set[str]:
        bones = armature_data.bones
        human_bone_name_to_bpy_bone_name = {
            value.name: key
            for key, value in bpy_bone_name_to_human_bone_specification.items()
        }

        search_conditions: list[str] = []

        # If the target's ancestor has a Human Bone assignment, use that as the
        # search start bone
        searching_bones: Optional[list[Bone]] = None
        ancestor: Optional[HumanBoneSpecification] = target.parent()
        while ancestor:
            ancestor_bpy_bone_name = human_bone_name_to_bpy_bone_name.get(ancestor.name)
            if not ancestor_bpy_bone_name or not (
                ancestor_bpy_bone := bones.get(ancestor_bpy_bone_name)
            ):
                # If there's no Human Bone assignment, traverse to the parent
                ancestor = ancestor.parent()
                continue

            if ancestor_bpy_bone.name in error_bpy_bone_names:
                # If there's an error in the Human Bone assignment, return empty result
                if diagnostics_layout:
                    diagnostics_message = pgettext(
                        'The bone assigned to the VRM Human Bone "{human_bone}" must'
                        + " be descendants of the bones assigned \nto the VRM human"
                        + ' bone "{parent_human_bone}". However, it cannot retrieve'
                        + " bone candidates because there\nis an error in the"
                        + ' assignment of the VRM Human Bone "{parent_human_bone}".'
                        + " Please resolve the error in the\nassignment of the VRM"
                        + ' Human Bone "{parent_human_bone}" first.'
                    ).format(
                        human_bone=target.title,
                        parent_human_bone=ancestor.title,
                    )
                    diagnostics_column = diagnostics_layout.column(align=True)
                    for i, line in enumerate(diagnostics_message.splitlines()):
                        diagnostics_column.label(
                            text=line,
                            translate=False,
                            icon="ERROR" if i == 0 else "BLANK1",
                        )
                return set()

            # Use the child bones of the found ancestor bone as the search start bones
            searching_bones = list(ancestor_bpy_bone.children)
            if diagnostics_layout:
                search_conditions.append(
                    pgettext(
                        'Being a descendant of the bone "{bpy_bone}" assigned'
                        + ' to the VRM Human Bone "{human_bone}"'
                    ).format(
                        human_bone=ancestor.title,
                        bpy_bone=ancestor_bpy_bone_name,
                    )
                )
            break

        root_bones: Final[Sequence[Bone]] = [
            bone for bone in bones.values() if not bone.parent
        ]

        # If no ancestor bone is found, use the root bone as the search start bone
        if searching_bones is None and len(root_bones) > 1:
            # If there are multiple root bones,
            # select the root bone of the already assigned bone
            human_bone_specification = None
            for (
                bpy_bone_name,
                human_bone_specification,
            ) in bpy_bone_name_to_human_bone_specification.items():
                if not bpy_bone_name:
                    continue
                if bpy_bone_name in error_bpy_bone_names:
                    continue
                bpy_bone = bones.get(bpy_bone_name)
                if not bpy_bone:
                    continue

                main_root_bone: Optional[Bone] = None
                parent: Optional[Bone] = bpy_bone
                while parent:
                    main_root_bone = parent
                    parent = parent.parent
                if not main_root_bone:
                    continue

                searching_bones = [main_root_bone]
                if diagnostics_layout:
                    search_conditions.append(
                        pgettext(
                            'Sharing the root bone with the bone "{bpy_bone}" assigned'
                            + ' to the VRM Human Bone "{human_bone}"'
                        ).format(
                            human_bone=human_bone_specification.title,
                            bpy_bone=bpy_bone_name,
                        )
                    )
                break
        if searching_bones is None:
            searching_bones = list(root_bones)

        # Bone candidates
        bone_candidates: set[Bone] = set(searching_bones)

        # First, register all descendant bones as candidates
        filling_bones = searching_bones.copy()
        while filling_bones:
            filling_bone = filling_bones.pop()
            bone_candidates.update(filling_bone.children)
            filling_bones.extend(filling_bone.children)

        removing_bone_tree = set[Bone]()

        # Traverse descendant bones and when we encounter an already assigned bone,
        # examine its relationship and exclude unnecessary candidates.
        while searching_bones:
            searching_bone = searching_bones.pop()
            human_bone_specification = bpy_bone_name_to_human_bone_specification.get(
                searching_bone.name
            )

            # If not assigned to a Human Bone or if it's the target bone,
            # recursively traverse child bones
            if (
                human_bone_specification is None
                or human_bone_specification == target
                or searching_bone.name in error_bpy_bone_names
            ):
                searching_bones.extend(searching_bone.children)
                continue

            if human_bone_specification.is_ancestor_of(target):
                # If an ancestor bone has an assignment
                # This case shouldn't exist since we start from the nearest
                # ancestor bone
                continue

            if target.is_ancestor_of(human_bone_specification):
                # If a descendant bone has an assignment:
                # - Exclude that bone and its descendants
                # - Exclude branches when traversing from that bone to the root bone
                removing_bone_tree.add(searching_bone)

                parent = searching_bone
                while parent:
                    grand_parent = parent.parent
                    if grand_parent is None:
                        # If parent is a root bone,
                        # exclude other root bones except parent
                        removing_bone_tree.update(
                            root_bone for root_bone in root_bones if root_bone != parent
                        )
                        break
                    # Exclude sibling bones of parent
                    removing_bone_tree.update(
                        parent_sibling
                        for parent_sibling in grand_parent.children
                        if parent_sibling != parent
                    )
                    parent = grand_parent

                if diagnostics_layout:
                    search_conditions.append(
                        pgettext(
                            'Being an ancestor of the bone "{bpy_bone}" assigned'
                            + ' to the VRM Human Bone "{human_bone}"'
                        ).format(
                            human_bone=human_bone_specification.title,
                            bpy_bone=searching_bone.name,
                        )
                    )
            else:
                # If a bone that is neither ancestor nor descendant has an assignment:
                # - Exclude that bone and its descendants
                # - Exclude that bone and its ancestors
                removing_bone_tree.add(searching_bone)

                parent = searching_bone
                while parent:
                    bone_candidates.discard(parent)
                    parent = parent.parent
                if diagnostics_layout:
                    search_conditions.append(
                        pgettext(
                            'Not being an ancestor of the bone "{bpy_bone}" assigned'
                            + ' to the VRM Human Bone "{human_bone}"'
                        ).format(
                            human_bone=human_bone_specification.title,
                            bpy_bone=searching_bone.name,
                        )
                    )

        bone_candidates.difference_update(removing_bone_tree)
        while removing_bone_tree:
            removing_bone = removing_bone_tree.pop()
            bone_candidates.difference_update(removing_bone.children)
            removing_bone_tree.update(removing_bone.children)

        if diagnostics_layout and search_conditions:
            diagnostics_layout.label(
                text=pgettext(
                    "Bones that meet all of the following conditions will be "
                    + "candidates for assignment:"
                ),
                translate=False,
                icon="INFO",
            )
            for search_condition in sorted(search_conditions):
                diagnostics_layout.label(
                    text=search_condition,
                    translate=False,
                    icon="DOT",
                )

        return {bone_cancidate.name for bone_cancidate in bone_candidates}

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

    def get_bone_property_group_type(self) -> BonePropertyGroupType:
        armature_data = self.find_armature()
        for (
            bone_property_group,
            bone_property_group_type,
        ) in self.get_all_bone_property_groups(armature_data):
            if bone_property_group == self:
                return bone_property_group_type

        message = (
            f"{type(self)}/{self} is not associated with "
            + "BonePropertyGroupType.get_all_bone_property_groups"
        )
        raise AssertionError(message)

    def set_bone_name(self, value: str) -> None:
        from .extension import get_armature_extension, get_bone_extension

        context = bpy.context

        armature_data = self.find_armature()
        armature_objects = [
            obj for obj in context.blend_data.objects if obj.data == armature_data
        ]
        bone_property_group_type = self.get_bone_property_group_type()

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

        ext = get_armature_extension(armature_data)

        if bone_property_group_type in [
            BonePropertyGroupType.VRM0_COLLIDER_GROUP,
            BonePropertyGroupType.VRM0_BONE_GROUP,
        ]:
            for collider_group in ext.vrm0.secondary_animation.collider_groups:
                for armature_object in armature_objects:
                    collider_group.refresh(armature_object)

        if bone_property_group_type == BonePropertyGroupType.SPRING_BONE1_COLLIDER:
            for collider in ext.spring_bone1.colliders:
                for armature_object in armature_objects:
                    collider.reset_bpy_object(context, armature_object)

        if (
            ext.is_vrm0()
            and bone_property_group_type == BonePropertyGroupType.VRM0_HUMAN
        ):
            self.update_all_vrm0_node_candidates(armature_data)
        if (
            ext.is_vrm1()
            and bone_property_group_type == BonePropertyGroupType.VRM1_HUMAN
        ):
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

        # Set from parent to child since child nodes will always have errors
        # if parent node has errors
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

        # Set from parent to child since child nodes will always have errors
        # if parent node has errors
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
