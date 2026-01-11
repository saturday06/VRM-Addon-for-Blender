# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import itertools
import math
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cached_property
from typing import Optional, Union

from bpy.types import Armature, Bone, Object
from mathutils import Matrix

from ..logger import get_logger
from ..vrm1.human_bone import (
    HumanBoneName,
    HumanBoneSpecification,
    HumanBoneSpecifications,
)

logger = get_logger(__name__)

MAX_SEARCH_COUNT = 500000
MAX_RECURSION_DEPTH = 10


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
        return NormalizedBone(
            name=bone.name,
            x=normalized_x,
            y=normalized_y,
            z=normalized_z,
            children=tuple(
                cls.create(armature_matrix, max_x, max_y, max_z, child)
                for child in bone.children
            ),
        )


@dataclass(frozen=True)
class SearchBranch:
    depth: int
    bone: NormalizedBone
    human_bone_specification: HumanBoneSpecification
    parent: Optional[tuple[NormalizedBone, HumanBoneSpecification]]
    children: tuple["SearchBranch", ...] = ()

    def with_depth(self, depth: int) -> "SearchBranch":
        return SearchBranch(
            depth=depth,
            bone=self.bone,
            human_bone_specification=self.human_bone_specification,
            parent=self.parent,
            children=self.children,
        )

    @cached_property
    def score(self) -> float:
        total_score = 0.0
        for child in self.children:
            total_score += child.score

        total_score -= math.sqrt(self.depth)

        if self.human_bone_specification.requirement:
            total_score += 100
        else:
            total_score += 20

        # 分岐のあるボーンの場合は、分岐されたボーンの位置が正しいかをチェックし
        # スコアを増やす。

        if self.human_bone_specification.name in [
            HumanBoneName.HEAD,
            HumanBoneName.NECK,
            HumanBoneName.UPPER_CHEST,
            HumanBoneName.CHEST,
            HumanBoneName.SPINE,
            HumanBoneName.HIPS,
        ]:
            total_score += self.bone.z - abs(self.bone.x)
        elif self.human_bone_specification.name in [
            HumanBoneName.LEFT_EYE,
            HumanBoneName.LEFT_HAND,
            HumanBoneName.LEFT_SHOULDER,
            HumanBoneName.LEFT_UPPER_ARM,
            HumanBoneName.LEFT_LOWER_ARM,
            HumanBoneName.LEFT_HAND,
        ]:
            total_score += self.bone.x / 2
        elif self.human_bone_specification.name in [
            HumanBoneName.LEFT_UPPER_LEG,
            HumanBoneName.LEFT_LOWER_LEG,
            HumanBoneName.LEFT_FOOT,
        ]:
            total_score += 0.2 if self.bone.x > 0 else 0
        elif self.human_bone_specification.name in [
            HumanBoneName.RIGHT_EYE,
            HumanBoneName.RIGHT_HAND,
            HumanBoneName.RIGHT_SHOULDER,
            HumanBoneName.RIGHT_UPPER_ARM,
            HumanBoneName.RIGHT_LOWER_ARM,
            HumanBoneName.RIGHT_HAND,
        ]:
            total_score += -self.bone.x / 2
        elif self.human_bone_specification.name in [
            HumanBoneName.RIGHT_UPPER_LEG,
            HumanBoneName.RIGHT_LOWER_LEG,
            HumanBoneName.RIGHT_FOOT,
        ]:
            total_score += 0.2 if self.bone.x < 0 else 0

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


class NoneCache:
    pass


def create_structure_based_mapping(
    armature: Object,
) -> Mapping[str, HumanBoneSpecification]:
    results: list[SearchBranch] = []
    counter = Counter()

    if not isinstance(armature_data := armature.data, Armature):
        message = f"{type(armature.data)} is not an Armature"
        raise TypeError(message)

    pose_position = armature_data.pose_position
    armature_data.pose_position = "REST"

    translations = [
        (armature.matrix_world @ bone.matrix_local).translation
        for bone in armature_data.bones
    ]
    if not translations:
        return {}
    max_x = max(abs(translation.x) for translation in translations)
    max_y = max(abs(translation.y) for translation in translations)
    max_z = max(abs(translation.z) for translation in translations)

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

    for root_bone in root_bones:
        logger.warning("Starting structure search from root bone: %s", root_bone.name)
        cache: dict[
            tuple[str, HumanBoneName, Optional[tuple[str, HumanBoneName]]],
            Union[SearchBranch, NoneCache],
        ] = {}
        result = search_structure_based_mapping(
            root_bone,
            HumanBoneSpecifications.HIPS,
            None,
            1,
            counter,
            cache,
        )
        if result:
            results.append(result)
    if not results:
        return {}
    result = max(results)

    mapping = result.recursive_mappings
    logger.warning(
        "Structure search completed. Total searches: %d, Cache hits: %d",
        counter.count,
        counter.cache_hit,
    )
    logger.warning(
        "Generated mappings:\n  %s\n",
        "\n  ".join(
            f"{spec.name.value}: {bone.name}" for spec, bone in mapping.items()
        ),
    )
    return {spec.name: bone for bone, spec in mapping.items()}


def search_structure_based_mapping(
    bone: NormalizedBone,
    human_bone_specification: HumanBoneSpecification,
    parent: Optional[tuple[NormalizedBone, HumanBoneSpecification]],
    depth: int,
    counter: Counter,
    cache: dict[
        tuple[str, HumanBoneName, Optional[tuple[str, HumanBoneName]]],
        Union[SearchBranch, NoneCache],
    ],
) -> Optional[SearchBranch]:
    if depth > MAX_RECURSION_DEPTH:
        # logger.warning(
        #     "%sMax recursion depth reached (%d). Terminating search.",
        #     pad,
        #     MAX_RECURSION_DEPTH,
        # )
        return None

    counter.count += 1
    if counter.count > MAX_SEARCH_COUNT:
        # logger.warning(
        #     "%sMax search count reached (%d). Terminating search.",
        #     pad,
        #     MAX_SEARCH_COUNT,
        # )
        return None

    # pad = "  " * depth
    results: list[SearchBranch] = []

    if parent:
        parent_bone, parent_human_bone_specification = parent
        cache_key = (
            bone.name,
            human_bone_specification.name,
            (parent_bone.name, parent_human_bone_specification.name),
        )
    else:
        parent_bone = None
        parent_human_bone_specification = None
        cache_key = (bone.name, human_bone_specification.name, None)

    cached_search_branch = cache.get(cache_key)
    if isinstance(cached_search_branch, SearchBranch):
        counter.cache_hit += 1
        if cached_search_branch.depth == depth:
            return cached_search_branch
        return cached_search_branch.with_depth(depth)

    # 現在注目しているボーンをスキップし、子ボーンの探索を行うパターン。
    results.extend(
        result
        for child_bone in bone.children
        if (
            result := search_structure_based_mapping(
                child_bone, human_bone_specification, parent, depth + 1, counter, cache
            )
        )
    )

    # 現在注目しているHumanBoneが必須ではない場合、そのHumanBoneの探索をスキップし、
    # その子のHumanBoneの探索を行うパターン。
    if not human_bone_specification.requirement:
        results.extend(
            result
            for child_specification in human_bone_specification.children()
            if (
                result := search_structure_based_mapping(
                    bone, child_specification, parent, depth + 1, counter, cache
                )
            )
        )

    # ボーンが伸びる方向が閾値外の場合、この探索は打ち切る。
    if human_bone_specification.name == HumanBoneName.HIPS:
        valid_bone_direction = bone.z > 0.0
    elif not parent_bone or not parent_human_bone_specification:
        valid_bone_direction = False
    elif human_bone_specification.name in [
        HumanBoneName.HEAD,
        HumanBoneName.NECK,
        HumanBoneName.UPPER_CHEST,
        HumanBoneName.CHEST,
        HumanBoneName.SPINE,
    ]:
        valid_bone_direction = bone.z > parent_bone.z or bone.y > parent_bone.y
    elif human_bone_specification.name in [
        HumanBoneName.LEFT_EYE,
        HumanBoneName.LEFT_HAND,
        HumanBoneName.LEFT_SHOULDER,
        HumanBoneName.LEFT_UPPER_ARM,
        HumanBoneName.LEFT_LOWER_ARM,
        HumanBoneName.LEFT_HAND,
    ]:
        valid_bone_direction = bone.x > 0
    elif human_bone_specification.name in [
        HumanBoneName.LEFT_UPPER_LEG,
        HumanBoneName.LEFT_LOWER_LEG,
        HumanBoneName.LEFT_FOOT,
    ]:
        valid_bone_direction = bone.x > 0 and bone.z < parent_bone.z
    elif human_bone_specification.name in [
        HumanBoneName.RIGHT_EYE,
        HumanBoneName.RIGHT_HAND,
        HumanBoneName.RIGHT_SHOULDER,
        HumanBoneName.RIGHT_UPPER_ARM,
        HumanBoneName.RIGHT_LOWER_ARM,
        HumanBoneName.RIGHT_HAND,
    ]:
        valid_bone_direction = bone.x < 0
    elif human_bone_specification.name in [
        HumanBoneName.RIGHT_UPPER_LEG,
        HumanBoneName.RIGHT_LOWER_LEG,
        HumanBoneName.RIGHT_FOOT,
    ]:
        valid_bone_direction = bone.x < 0 and bone.z < parent_bone.z
    else:
        valid_bone_direction = True

    if not valid_bone_direction:
        if results:
            selected_result = max(results)
            cache[cache_key] = selected_result
            return selected_result
        cache[cache_key] = NoneCache()
        return None

    results.append(
        SearchBranch(
            depth=depth,
            bone=bone,
            human_bone_specification=human_bone_specification,
            parent=parent,
            children=(),
        )
    )

    # 分岐同士の組み合わせごとに探索を行う。
    assignments: list[list[tuple[HumanBoneSpecification, NormalizedBone]]] = [
        list(zip(spec_children_permutation, bone_children))
        for spec_children, bone_children in itertools.product(
            itertools.combinations(
                human_bone_specification.children(),
                min(len(human_bone_specification.children()), len(bone.children)),
            ),
            itertools.combinations(bone.children, len(bone.children)),
        )
        for spec_children_permutation in itertools.permutations(spec_children)
    ]

    # logger.debug("%s| Found %d assignments", pad, len(assignments))
    for assignment in assignments:
        # logger.debug(
        #     "%s| Processing Assignment: { %s }",
        #     pad,
        #     ", ".join(
        #         f"{spec_child.name.value}: {bone_child.name}"
        #         for spec_child, bone_child in assignment
        #     ),
        # )
        child_branches: tuple[SearchBranch, ...] = tuple(
            child_branch
            for spec_child, bone_child in assignment
            if (
                child_branch := search_structure_based_mapping(
                    bone_child,
                    spec_child,
                    (bone, human_bone_specification),
                    depth + 1,
                    counter,
                    cache,
                )
            )
        )

        results.append(
            SearchBranch(
                depth=depth,
                bone=bone,
                human_bone_specification=human_bone_specification,
                parent=parent,
                children=tuple(child_branches),
            )
        )

    # for result in results:
    #     logger.debug(
    #         "%s| Result: %d [%s]",
    #         pad,
    #         result.score,
    #         ", ".join(
    #             f"{spec.name.value}: {bone.name}"
    #             for spec, bone in result.recursive_mappings.items()
    #         ),
    #     )

    selected_result = max(results)
    # logger.debug(
    #     "%s| Max: %d",
    #     pad,
    #     selected_result.score,
    # )
    cache[cache_key] = selected_result
    return selected_result
