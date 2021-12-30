import collections
from typing import Any, Dict, List, Tuple

from ..common import deep, glb
from .vrm_parser import decode_bin


def human_bone_sort_key(human_bone_dict: Any) -> int:
    if not isinstance(human_bone_dict, dict):
        return -1
    node = human_bone_dict.get("node")
    if not isinstance(node, int):
        return -1
    return node


def create_vrm_json_dict(data: bytes) -> Dict[str, Any]:
    vrm_json, binary_chunk = glb.parse(data)
    vrm_json["~accessors_decoded"] = decode_bin(vrm_json, binary_chunk)

    if "extensions" not in vrm_json:
        return vrm_json

    if "VRM" not in vrm_json["extensions"]:
        return vrm_json

    vrm0_extension = vrm_json["extensions"]["VRM"]
    if not isinstance(vrm0_extension, dict):
        return vrm_json

    if "firstPerson" not in vrm0_extension:
        vrm0_extension["firstPerson"] = {}

    first_person_dict = vrm0_extension["firstPerson"]
    if not isinstance(first_person_dict, dict):
        return vrm_json

    if isinstance(vrm0_extension.get("humanoid"), dict) and isinstance(
        vrm0_extension["humanoid"].get("humanBones"), list
    ):
        vrm0_extension["humanoid"]["humanBones"] = sorted(
            vrm0_extension["humanoid"]["humanBones"], key=human_bone_sort_key
        )

    if (
        first_person_dict.get("firstPersonBone") in [None, -1]
        and isinstance(vrm0_extension.get("humanoid"), dict)
        and isinstance(
            vrm0_extension["humanoid"].get("humanBones"), collections.Iterable
        )
    ):
        for human_bone in vrm0_extension["humanoid"]["humanBones"]:
            if not isinstance(human_bone, dict):
                continue
            node = human_bone.get("node")
            if not isinstance(node, int) or node < 0:
                continue
            if human_bone.get("bone") == "head":
                first_person_dict["firstPersonBone"] = node
                break

    for look_at_key in [
        "lookAtHorizontalInner",
        "lookAtHorizontalOuter",
        "lookAtVerticalDown",
        "lookAtVerticalUp",
    ]:
        if look_at_key not in first_person_dict:
            first_person_dict[look_at_key] = {}
        look_at_dict = first_person_dict[look_at_key]
        if not isinstance(look_at_dict, dict):
            continue
        if "curve" not in look_at_dict:
            look_at_dict["curve"] = [0, 0, 0, 1, 1, 1, 1, 0]

    if isinstance(vrm0_extension.get("blendShapeMaster"), dict) and isinstance(
        vrm0_extension["blendShapeMaster"].get("blendShapeGroups"),
        collections.Iterable,
    ):
        for blend_shape_group_dict in vrm0_extension["blendShapeMaster"][
            "blendShapeGroups"
        ]:
            if not isinstance(blend_shape_group_dict, dict):
                continue
            if "isBinary" not in blend_shape_group_dict:
                blend_shape_group_dict["isBinary"] = False
            if "binds" not in blend_shape_group_dict:
                blend_shape_group_dict["binds"] = []
            if "materialValues" not in blend_shape_group_dict:
                blend_shape_group_dict["materialValues"] = []

    if isinstance(vrm0_extension.get("secondaryAnimation"), dict) and isinstance(
        vrm0_extension["secondaryAnimation"].get("colliderGroups"), collections.Iterable
    ):

        def sort_collider_groups_with_index_key(
            collider_group_with_index: Tuple[int, Dict[str, Any]]
        ) -> int:
            (_, collider_group) = collider_group_with_index
            if not isinstance(collider_group, dict):
                return -999
            node = collider_group.get("node")
            if not isinstance(node, int):
                return -999
            return node

        sorted_collider_groups_with_original_index = sorted(
            enumerate(vrm0_extension["secondaryAnimation"]["colliderGroups"]),
            key=sort_collider_groups_with_index_key,
        )
        vrm0_extension["secondaryAnimation"]["colliderGroups"] = [
            collider_group
            for _, collider_group in sorted_collider_groups_with_original_index
        ]
        original_index_to_sorted_index = {
            original_index: sorted_index
            for (sorted_index, (original_index, _)) in enumerate(
                sorted_collider_groups_with_original_index
            )
        }

        bone_groups = vrm0_extension["secondaryAnimation"].get("boneGroups")
        if isinstance(bone_groups, collections.Iterable):
            for bone_group in bone_groups:
                if not isinstance(bone_group, dict):
                    continue
                if "comment" not in bone_group:
                    bone_group["comment"] = ""
                collider_groups = bone_group.get("colliderGroups")
                if not isinstance(collider_groups, collections.Iterable):
                    continue
                for i, collider_group in enumerate(list(collider_groups)):
                    if not isinstance(collider_group, int):
                        continue
                    if collider_group not in original_index_to_sorted_index:
                        bone_group["colliderGroups"][i] = -999
                        continue
                    bone_group["colliderGroups"][i] = original_index_to_sorted_index[
                        collider_group
                    ]

    return vrm_json


def vrm_diff(before: bytes, after: bytes, float_tolerance: float) -> List[str]:
    return deep.diff(
        create_vrm_json_dict(before), create_vrm_json_dict(after), float_tolerance
    )
