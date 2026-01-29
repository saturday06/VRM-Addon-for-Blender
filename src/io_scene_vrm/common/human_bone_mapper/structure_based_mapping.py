# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import itertools
import math
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from functools import cached_property
from typing import Final, Optional, Union

from bpy.types import Armature, Bone, Object
from mathutils import Matrix

from ..deep import Json
from ..logger import get_logger
from ..vrm1.human_bone import (
    HumanBoneName,
    HumanBoneSpecification,
    HumanBoneSpecifications,
)

logger = get_logger(__name__)


CENTRAL_BONE_NAMES = frozenset(
    [
        HumanBoneName.HEAD,
        HumanBoneName.NECK,
        HumanBoneName.UPPER_CHEST,
        HumanBoneName.CHEST,
        HumanBoneName.SPINE,
        HumanBoneName.HIPS,
    ]
)

HIPS_TO_SPINE_BONE_NAMES = frozenset(
    [
        HumanBoneName.HIPS,
        HumanBoneName.SPINE,
    ]
)

SPINE_TO_UPPER_CHEST_BONE_NAMES = frozenset(
    [
        HumanBoneName.SPINE,
        HumanBoneName.CHEST,
        HumanBoneName.UPPER_CHEST,
    ]
)

SPINE_TO_NECK_NAMES = frozenset(
    [
        HumanBoneName.SPINE,
        HumanBoneName.CHEST,
        HumanBoneName.UPPER_CHEST,
        HumanBoneName.NECK,
    ]
)

LEFT_ARM_BONE_NAMES = frozenset(
    [
        HumanBoneName.LEFT_EYE,
        HumanBoneName.LEFT_HAND,
        HumanBoneName.LEFT_SHOULDER,
        HumanBoneName.LEFT_UPPER_ARM,
        HumanBoneName.LEFT_LOWER_ARM,
    ]
)

LEFT_LEG_BONE_NAMES = frozenset(
    [
        HumanBoneName.LEFT_UPPER_LEG,
        HumanBoneName.LEFT_LOWER_LEG,
        HumanBoneName.LEFT_FOOT,
    ]
)

RIGHT_ARM_BONE_NAMES = frozenset(
    [
        HumanBoneName.RIGHT_EYE,
        HumanBoneName.RIGHT_HAND,
        HumanBoneName.RIGHT_SHOULDER,
        HumanBoneName.RIGHT_UPPER_ARM,
        HumanBoneName.RIGHT_LOWER_ARM,
    ]
)

RIGHT_LEG_BONE_NAMES = frozenset(
    [
        HumanBoneName.RIGHT_UPPER_LEG,
        HumanBoneName.RIGHT_LOWER_LEG,
        HumanBoneName.RIGHT_FOOT,
    ]
)


@dataclass
class Counter:
    count: int = 0
    cache_hit: int = 0


@dataclass(frozen=True)
class NormalizedBone:
    name: str
    x: float
    y: float
    z: float
    children: tuple["NormalizedBone", ...]
    recursive_len: int

    @classmethod
    def create(
        cls,
        armature_matrix: Matrix,
        max_x: float,
        max_y: float,
        max_z: float,
        bone: Bone,
    ) -> "NormalizedBone":
        x, y, z = (armature_matrix @ bone.matrix_local).translation
        normalized_x = math.copysign(math.sqrt(abs(x) / max_x), x) if max_x > 0 else 0
        normalized_y = math.copysign(math.sqrt(abs(y) / max_y), y) if max_y > 0 else 0
        normalized_z = math.copysign(math.sqrt(abs(z) / max_z), z) if max_z > 0 else 0
        children = tuple(
            cls.create(armature_matrix, max_x, max_y, max_z, child)
            for child in bone.children
        )
        return NormalizedBone(
            name=bone.name,
            x=normalized_x,
            y=normalized_y,
            z=normalized_z,
            children=children,
            recursive_len=1 + sum(child.recursive_len for child in children),
        )

    @classmethod
    def from_json(cls, data: Json) -> "NormalizedBone":
        if not isinstance(data, Mapping):
            message = "NormalizedBone must be an object"
            raise TypeError(message)
        name = data.get("name")
        if not isinstance(name, str):
            message = "NormalizedBone.name must be a string"
            raise TypeError(message)

        x = data.get("x")
        y = data.get("y")
        z = data.get("z")
        if not isinstance(x, (int, float)):
            message = "NormalizedBone.x must be a number"
            raise TypeError(message)
        if not isinstance(y, (int, float)):
            message = "NormalizedBone.y must be a number"
            raise TypeError(message)
        if not isinstance(z, (int, float)):
            message = "NormalizedBone.z must be a number"
            raise TypeError(message)

        children_data = data.get("children")
        if children_data is None:
            children_data = []
        if not isinstance(children_data, list):
            message = "NormalizedBone.children must be a list"
            raise TypeError(message)
        children = tuple(cls.from_json(child) for child in children_data)

        recursive_len = data.get("recursiveLen")
        if recursive_len is None:
            recursive_len_value = 1 + sum(child.recursive_len for child in children)
        elif isinstance(recursive_len, int):
            recursive_len_value = recursive_len
        else:
            message = "NormalizedBone.recursiveLen must be an int"
            raise ValueError(message)

        return NormalizedBone(
            name=name,
            x=float(x),
            y=float(y),
            z=float(z),
            children=children,
            recursive_len=recursive_len_value,
        )

    def to_json(self) -> Json:
        return {
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "children": [child.to_json() for child in self.children],
            "recursiveLen": self.recursive_len,
        }

    def dump(self) -> str:
        output = f'("{self.name}", ({self.x:.3f}, {self.y:.3f}, {self.z:.3f})): {{\n'
        for child in self.children:
            output += child.dump()
        output += "},\n"
        return output


SearchBranch = Union["UnassignedSearchBranch", "AssignedSearchBranch"]


def parent_from_json(
    data: Json,
) -> Optional[tuple[NormalizedBone, HumanBoneSpecification]]:
    if data is None:
        return None
    if not isinstance(data, Mapping):
        message = "parent must be an object or null"
        raise TypeError(message)
    bone_data = data.get("bone")
    if not isinstance(bone_data, Mapping):
        message = "parent.bone must be an object"
        raise TypeError(message)
    bone = NormalizedBone.from_json(bone_data)
    human_bone_name_str = data.get("humanBoneName")
    if not isinstance(human_bone_name_str, str):
        message = "parent.humanBoneName must be a string"
        raise TypeError(message)
    human_bone_specification = HumanBoneSpecifications.from_name_str(
        human_bone_name_str
    )
    if human_bone_specification is None:
        message = f"Unknown human bone name: {human_bone_name_str}"
        raise ValueError(message)
    return (bone, human_bone_specification)


def search_branch_from_json(data: Json) -> SearchBranch:
    if not isinstance(data, Mapping):
        message = "SearchBranch must be an object"
        raise TypeError(message)
    type_name = data.get("type_name")
    if type_name == AssignedSearchBranch.__name__:
        return AssignedSearchBranch.from_json(data)

    if type_name == UnassignedSearchBranch.__name__:
        return UnassignedSearchBranch.from_json(data)

    message = (
        "SearchBranch.type_name must be 'AssignedSearchBranch'"
        + " or 'UnassignedSearchBranch'"
    )
    raise ValueError(message)


@dataclass(frozen=True)
class UnassignedSearchBranch:
    children: tuple[SearchBranch, ...] = ()

    def to_json(self) -> Json:
        return {
            "type_name": type(self).__name__,
            "children": [child.to_json() for child in self.children],
        }

    @classmethod
    def from_json(cls, data: Mapping[str, Json]) -> "UnassignedSearchBranch":
        children_data = data.get("children")
        if children_data is None:
            children_data = []
        if not isinstance(children_data, list):
            message = "UnassignedSearchBranch.children must be a list"
            raise TypeError(message)
        return UnassignedSearchBranch(
            children=tuple(search_branch_from_json(child) for child in children_data)
        )

    @cached_property
    def score(self) -> float:
        return sum((child.score for child in self.children), start=0.0)

    @cached_property
    def recursive_mappings(self) -> Mapping[HumanBoneSpecification, NormalizedBone]:
        result: dict[HumanBoneSpecification, NormalizedBone] = {}
        for child in self.children:
            result.update(child.recursive_mappings)
        return result

    def __lt__(self, other: "SearchBranch") -> bool:
        return self.score < other.score


@dataclass(frozen=True)
class AssignedSearchBranch:
    depth: int
    bone: NormalizedBone
    human_bone_specification: HumanBoneSpecification
    parent: Optional[tuple[NormalizedBone, HumanBoneSpecification]]
    children: tuple[SearchBranch, ...]

    def to_json(self) -> Json:
        parent = self.parent
        if parent is None:
            parent_json: Json = None
        else:
            parent_bone, parent_spec = parent
            parent_json = {
                "bone": parent_bone.to_json(),
                "humanBoneName": parent_spec.name.value,
            }
        return {
            "type_name": type(self).__name__,
            "depth": self.depth,
            "bone": self.bone.to_json(),
            "humanBoneName": self.human_bone_specification.name.value,
            "parent": parent_json,
            "children": [child.to_json() for child in self.children],
        }

    @classmethod
    def from_json(cls, data: Mapping[str, Json]) -> "AssignedSearchBranch":
        depth = data.get("depth")
        if not isinstance(depth, int):
            message = "AssignedSearchBranch.depth must be an int"
            raise TypeError(message)
        bone_data = data.get("bone")
        if not isinstance(bone_data, Mapping):
            message = "AssignedSearchBranch.bone must be an object"
            raise TypeError(message)
        bone = NormalizedBone.from_json(bone_data)
        human_bone_name_str = data.get("humanBoneName")
        if not isinstance(human_bone_name_str, str):
            message = "AssignedSearchBranch.humanBoneName must be a string"
            raise TypeError(message)
        human_bone_specification = HumanBoneSpecifications.from_name_str(
            human_bone_name_str
        )
        if human_bone_specification is None:
            message = f"Unknown human bone name: {human_bone_name_str}"
            raise ValueError(message)
        parent = parent_from_json(data.get("parent"))
        children_data = data.get("children")
        if children_data is None:
            children_data = []
        if not isinstance(children_data, list):
            message = "AssignedSearchBranch.children must be a list"
            raise TypeError(message)
        children = tuple(search_branch_from_json(child) for child in children_data)
        return AssignedSearchBranch(
            depth=depth,
            bone=bone,
            human_bone_specification=human_bone_specification,
            parent=parent,
            children=children,
        )

    @cached_property
    def score(self) -> float:
        total_score = sum((child.score for child in self.children), start=0.0)

        total_score -= math.sqrt(self.depth)

        if self.human_bone_specification.requirement:
            total_score += 1000
        else:
            total_score += 20

        human_bone_name = self.human_bone_specification.name

        if self.bone.z > 0:
            total_score += 5

        if human_bone_name in CENTRAL_BONE_NAMES:
            total_score += self.bone.z - abs(self.bone.x)
        elif human_bone_name in LEFT_ARM_BONE_NAMES:
            total_score += self.bone.x / 2
        elif human_bone_name in LEFT_LEG_BONE_NAMES:
            total_score += 0.2 if self.bone.x > 0 else 0
        elif human_bone_name in RIGHT_ARM_BONE_NAMES:
            total_score += -self.bone.x / 2
        elif human_bone_name in RIGHT_LEG_BONE_NAMES:
            total_score += 0.2 if self.bone.x < 0 else 0

        parent = self.parent
        if parent is None:
            return total_score

        parent_bone, parent_human_bone_specification = parent
        human_bone_name = self.human_bone_specification.name
        parent_human_bone_name = parent_human_bone_specification.name
        if human_bone_name == HumanBoneName.SPINE:
            if (
                parent_human_bone_name == HumanBoneName.HIPS
                and parent_bone.z < self.bone.z
            ):
                total_score += 5
        elif human_bone_name == HumanBoneName.CHEST:
            if (
                parent_human_bone_name in HIPS_TO_SPINE_BONE_NAMES
                and parent_bone.z < self.bone.z
            ):
                total_score += 5
        elif human_bone_name == HumanBoneName.UPPER_CHEST:
            if (
                parent_human_bone_name == HumanBoneName.CHEST
                and parent_bone.z < self.bone.z
            ):
                total_score += 5
        elif human_bone_name == HumanBoneName.NECK:
            if (
                parent_human_bone_name in SPINE_TO_UPPER_CHEST_BONE_NAMES
                and parent_bone.z < self.bone.z
            ):
                total_score += 5
        elif human_bone_name == HumanBoneName.HEAD:
            if (
                parent_human_bone_name in SPINE_TO_NECK_NAMES
                and parent_bone.z < self.bone.z
            ):
                total_score += 5
        else:
            pass

        return total_score

    @cached_property
    def recursive_mappings(self) -> Mapping[HumanBoneSpecification, NormalizedBone]:
        result: dict[HumanBoneSpecification, NormalizedBone] = {
            self.human_bone_specification: self.bone
        }
        for child in self.children:
            result.update(child.recursive_mappings)
        return result

    def __lt__(self, other: "SearchBranch") -> bool:
        return self.score < other.score


SEARCH_STOP_BRANCH: Final[SearchBranch] = UnassignedSearchBranch()


@dataclass(frozen=True)
class SearchContext:
    max_search_count: int
    require_requirement: int
    only_requirement: bool
    counter: Counter = field(default_factory=Counter)
    cache: dict[
        tuple[tuple[str, ...], tuple[str, ...], Optional[tuple[str, str]], int],
        SearchBranch,
    ] = field(
        default_factory=dict[
            tuple[tuple[str, ...], tuple[str, ...], Optional[tuple[str, str]], int],
            SearchBranch,
        ]
    )
    max_recursion_depth: int = 50


DEFAULT_MAX_SEARCH_COUNT: Final[int] = 1000000


def create_structure_based_mapping(
    armature: Object,
    human_bone_specification: HumanBoneSpecification = HumanBoneSpecifications.HIPS,
    max_search_count: int = DEFAULT_MAX_SEARCH_COUNT,
) -> Mapping[str, HumanBoneSpecification]:
    if not isinstance(armature_data := armature.data, Armature):
        message = f"{type(armature.data)} is not an Armature"
        raise TypeError(message)

    pose_position = armature_data.pose_position
    armature_data.pose_position = "REST"

    translations = [
        (armature.matrix_world @ bone.matrix_local).translation
        for bone in armature_data.bones
    ]
    max_x = max((abs(translation.x) for translation in translations), default=0)
    max_y = max((abs(translation.y) for translation in translations), default=0)
    max_z = max((abs(translation.z) for translation in translations), default=0)

    root_bones = [
        NormalizedBone.create(
            armature.matrix_world,
            max_x,
            max_y,
            max_z,
            bone,
        )
        for bone in armature_data.bones
        if bone.parent is None
    ]
    armature_data.pose_position = pose_position
    counter = Counter()
    max_result: SearchBranch = SEARCH_STOP_BRANCH

    for require_requirement, only_requirement in ((1, True), (0, False)):
        search_context = SearchContext(
            require_requirement=require_requirement,
            only_requirement=only_requirement,
            max_search_count=max_search_count,
            counter=counter,
        )
        for skip_count in range(1000):
            if counter.count > search_context.max_search_count:
                break
            changed = False
            for root_bone in root_bones:
                if counter.count > search_context.max_search_count:
                    break
                if (
                    root_bone.recursive_len
                    < skip_count
                    + HumanBoneSpecifications.HIPS.recursive_requirement_len
                    * require_requirement
                ):
                    break
                result = search_structure_based_mapping_step(
                    root_bone,
                    (human_bone_specification,),
                    None,
                    1,
                    skip_count,
                    search_context,
                )
                if max_result < result:
                    max_result = result
                    changed = True

            if not changed:
                continue

            logger.warning("Structure search context:")
            logger.warning("  Search Count Limit: %d", search_context.max_search_count)
            logger.warning("  Recursion Limit: %d", search_context.max_recursion_depth)
            logger.warning("  Skip Count: %d", skip_count)
            logger.warning(
                "  Require Requirement: %d", search_context.require_requirement
            )
            logger.warning("  Only Requirement: %d", search_context.only_requirement)
            logger.warning(
                "Structure search: Total searches: %d, Cache hits: %d",
                counter.count,
                counter.cache_hit,
            )
            logger.warning(
                "Generated mappings:\n  %s",
                "\n  ".join(
                    f"{spec.name.value}: {bone.name}"
                    for spec, bone in max_result.recursive_mappings.items()
                ),
            )

    logger.warning(
        "Structure search completed:"
        " Total searches: %d (soft limit: %d), Cache hits: %d",
        counter.count,
        max_search_count,
        counter.cache_hit,
    )
    mapping = max_result.recursive_mappings
    return {spec.name: bone for bone, spec in mapping.items()}


def search_structure_based_mapping_step(
    bone: NormalizedBone,
    human_bone_specifications: tuple[HumanBoneSpecification, ...],
    parent: Optional[tuple[NormalizedBone, HumanBoneSpecification]],
    depth: int,
    skip_count: int,
    search_context: SearchContext,
) -> SearchBranch:
    if skip_count < 0 or bone.recursive_len < skip_count:
        return SEARCH_STOP_BRANCH

    if search_context.require_requirement:
        recursive_requirement_len = sum(
            human_bone_specification.recursive_requirement_len
            for human_bone_specification in human_bone_specifications
        )
        if bone.recursive_len < skip_count + recursive_requirement_len:
            return SEARCH_STOP_BRANCH

    if depth > search_context.max_recursion_depth:
        return SEARCH_STOP_BRANCH

    counter = search_context.counter
    counter.count += 1
    if counter.count > search_context.max_search_count:
        return SEARCH_STOP_BRANCH

    cache_key = (
        (bone.name,),
        tuple(spec.name.value for spec in human_bone_specifications),
        None
        if parent is None
        else (
            parent[0].name,
            parent[1].name.value,
        ),
        skip_count,
    )
    cache = search_context.cache
    if (search_branchs := cache.get(cache_key)) is not None:
        counter.cache_hit += 1
        return search_branchs

    result = SEARCH_STOP_BRANCH

    if len(human_bone_specifications) == 1:
        human_bone_specification = human_bone_specifications[0]
        human_bone_specification_children = (
            human_bone_specification.required_children
            if search_context.only_requirement
            else human_bone_specification.children
        )
        if bone.children and human_bone_specification_children:
            children = (
                search_structure_based_mapping_product(
                    bone.children,
                    human_bone_specification_children,
                    (bone, human_bone_specification),
                    depth + 1,
                    skip_count,
                    search_context,
                ),
            )
        else:
            children = ()

        result = max(
            result,
            AssignedSearchBranch(
                depth=depth + 1,
                bone=bone,
                human_bone_specification=human_bone_specification,
                parent=parent,
                children=children,
            ),
        )

    if skip_count > 0:
        result = max(
            result,
            search_structure_based_mapping_product(
                bone.children,
                human_bone_specifications,
                parent,
                depth + 1,
                skip_count - 1,
                search_context,
            ),
        )

    cache[cache_key] = result
    return result


def search_structure_based_mapping_product(
    bones: tuple[NormalizedBone, ...],
    human_bone_specifications: tuple[HumanBoneSpecification, ...],
    parent: Optional[tuple[NormalizedBone, HumanBoneSpecification]],
    depth: int,
    skip_count: int,
    search_context: SearchContext,
) -> SearchBranch:
    if not bones or not human_bone_specifications:
        return SEARCH_STOP_BRANCH

    if depth > search_context.max_recursion_depth:
        return SEARCH_STOP_BRANCH

    if skip_count < 0 or sum(bone.recursive_len for bone in bones) < skip_count:
        return SEARCH_STOP_BRANCH

    counter = search_context.counter
    counter.count += 1
    if counter.count > search_context.max_search_count:
        return SEARCH_STOP_BRANCH

    cache = search_context.cache
    cache_key = (
        tuple(sorted(bone.name for bone in bones)),
        tuple(spec.name.value for spec in human_bone_specifications),
        None
        if parent is None
        else (
            parent[0].name,
            parent[1].name.value,
        ),
        skip_count,
    )
    if (search_branchs := cache.get(cache_key)) is not None:
        counter.cache_hit += 1
        return search_branchs

    result = SEARCH_STOP_BRANCH

    for skipping_human_bone_specification in human_bone_specifications:
        if skipping_human_bone_specification.requirement:
            continue
        skipping_children = sum(
            tuple(
                skipping_human_bone_specification.children
                if human_bone_specification == skipping_human_bone_specification
                else (human_bone_specification,)
                for human_bone_specification in human_bone_specifications
            ),
            (),
        )
        if skipping_children:
            result = max(
                result,
                search_structure_based_mapping_product(
                    bones,
                    skipping_children,
                    parent,
                    depth + 1,
                    skip_count,
                    search_context,
                ),
            )

    assignment_combination_len = min(len(human_bone_specifications), len(bones))
    if (
        not search_context.require_requirement
        or sum(int(s.requirement) for s in human_bone_specifications)
        <= assignment_combination_len
    ):
        spec_tuples = tuple(
            (human_bone_specification,)
            for human_bone_specification in human_bone_specifications
        )
        for spec_children, bone_children in itertools.product(
            itertools.combinations(spec_tuples, assignment_combination_len),
            itertools.combinations(bones, assignment_combination_len),
        ):
            for spec_children_permutation in itertools.permutations(spec_children):
                for bone_packings in iter_skip_counts_and_bone_combinations(
                    skip_count,
                    tuple(
                        zip(
                            bone_children,
                            (
                                sum(s.recursive_requirement_len for s in ss)
                                * search_context.require_requirement
                                for ss in spec_children_permutation
                            ),
                        )
                    ),
                ):
                    children = tuple(
                        search_structure_based_mapping_step(
                            bone_child,
                            spec_child,
                            parent,
                            depth + 1,
                            child_skip_count,
                            search_context,
                        )
                        for spec_child, (bone_child, child_skip_count) in zip(
                            spec_children_permutation, bone_packings
                        )
                    )
                    result = max(result, UnassignedSearchBranch(children=children))
                    if counter.count > search_context.max_search_count:
                        break

    for special_group in (
        (
            HumanBoneSpecifications.LEFT_UPPER_LEG,
            HumanBoneSpecifications.RIGHT_UPPER_LEG,
        ),
        (
            HumanBoneSpecifications.LEFT_UPPER_ARM,
            HumanBoneSpecifications.RIGHT_UPPER_ARM,
        ),
        (
            HumanBoneSpecifications.LEFT_EYE,
            HumanBoneSpecifications.RIGHT_EYE,
        ),
        # (HumanBoneSpecifications.LEFT_THUMB_METACARPAL,),
        # (HumanBoneSpecifications.RIGHT_THUMB_METACARPAL,),
    ):
        if not all(s in human_bone_specifications for s in special_group):
            continue

        remaining_group = list(human_bone_specifications)
        for special_human_bone_specification in special_group:
            remaining_group.remove(special_human_bone_specification)

        if remaining_group:
            groups = (
                special_group,
                *tuple((remaining,) for remaining in remaining_group),
            )
        else:
            groups = (special_group,)

        special_assignment_combination_len = min(len(groups), len(bones))
        if (
            search_context.require_requirement
            and special_assignment_combination_len
            < sum(int(any(s.requirement for s in group)) for group in groups)
        ):
            break

        for spec_children, bone_children in itertools.product(
            itertools.combinations(groups, special_assignment_combination_len),
            itertools.combinations(bones, special_assignment_combination_len),
        ):
            for spec_children_permutation in itertools.permutations(spec_children):
                for bone_packings in iter_skip_counts_and_bone_combinations(
                    skip_count,
                    tuple(
                        zip(
                            bone_children,
                            (
                                sum(s.recursive_requirement_len for s in ss)
                                * search_context.require_requirement
                                for ss in spec_children_permutation
                            ),
                        )
                    ),
                ):
                    children = tuple(
                        search_structure_based_mapping_step(
                            bone_child,
                            spec_child,
                            parent,
                            depth + 1,
                            child_skip_count,
                            search_context,
                        )
                        for spec_child, (bone_child, child_skip_count) in zip(
                            spec_children_permutation, bone_packings
                        )
                    )
                    result = max(result, UnassignedSearchBranch(children=children))
                    if counter.count > search_context.max_search_count:
                        break
        break

    cache[cache_key] = result
    return result


def backtrack_skip_counts_and_bone_combinations(
    *,
    bones: tuple[tuple[NormalizedBone, int], ...],
    counts: list[int],
    bone_index: int,
    remaining: int,
) -> Iterator[list[tuple[NormalizedBone, int]]]:
    if bone_index == len(bones):
        if remaining == 0:
            yield [(bones[i][0], counts[i]) for i in range(len(bones))]
        return

    bone, requirement_len = bones[bone_index]
    max_count = min(bone.recursive_len - requirement_len, remaining)
    for count in range(max_count, -1, -1):
        counts.append(count)
        yield from backtrack_skip_counts_and_bone_combinations(
            bones=bones,
            counts=counts,
            bone_index=bone_index + 1,
            remaining=remaining - count,
        )
        counts.pop()


def iter_skip_counts_and_bone_combinations(
    skip_count: int, bones: tuple[tuple[NormalizedBone, int], ...]
) -> Iterator[list[tuple[NormalizedBone, int]]]:
    if skip_count < 0:
        return

    if not bones:
        if skip_count == 0:
            yield []
        return

    total_recursive_len = sum(
        b.recursive_len - requirement_len for b, requirement_len in bones
    )
    if total_recursive_len < skip_count:
        return

    yield from backtrack_skip_counts_and_bone_combinations(
        bones=bones,
        counts=[],
        bone_index=0,
        remaining=skip_count,
    )
