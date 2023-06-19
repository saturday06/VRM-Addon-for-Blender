import uuid
from typing import Dict, Iterator, Optional, Set, TypeVar, Union

import bpy

from ..common.logging import get_logger
from ..common.vrm0 import human_bone as vrm0_human_bone
from ..common.vrm1 import human_bone as vrm1_human_bone

HumanBoneSpecification = TypeVar(
    "HumanBoneSpecification",
    vrm0_human_bone.HumanBoneSpecification,
    vrm1_human_bone.HumanBoneSpecification,
)

logger = get_logger(__name__)


class StringPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    def get_value(self) -> str:
        value = self.get("value")
        if isinstance(value, str):
            return value
        return str(value)

    def set_value(self, value: str) -> None:
        self.name = value  # pylint: disable=attribute-defined-outside-init
        self["value"] = value

    value: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="String Value",  # noqa: F722
        get=get_value,
        set=set_value,
    )


class FloatPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    def get_value(self) -> float:
        value = self.get("value")
        if isinstance(value, (float, int)):
            return float(value)
        return 0.0

    def set_value(self, value: float) -> None:
        self.name = str(value)  # pylint: disable=attribute-defined-outside-init
        self["value"] = value

    value: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Float Value",  # noqa: F722
        get=get_value,
        set=set_value,
    )


class MeshObjectPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    def get_mesh_object_name(self) -> str:
        if (
            not self.bpy_object
            or not self.bpy_object.name
            or self.bpy_object.type != "MESH"
        ):
            return ""
        return str(self.bpy_object.name)

    def set_mesh_object_name(self, value: object) -> None:
        if (
            not isinstance(value, str)
            or value not in bpy.data.objects
            or bpy.data.objects[value].type != "MESH"
        ):
            self.bpy_object = None
            return
        self.bpy_object = bpy.data.objects[value]

    mesh_object_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        get=get_mesh_object_name, set=set_mesh_object_name
    )

    def get_value(self) -> str:
        logger.warning(
            "MeshObjectPropertyGroup.value is deprecated."
            + " Use MeshObjectPropertyGroup.mesh_object_name instead."
        )
        return str(self.mesh_object_name)

    def set_value(self, value: str) -> None:
        logger.warning(
            "MeshObjectPropertyGroup.value is deprecated."
            + " Use MeshObjectPropertyGroup.mesh_object_name instead."
        )
        self.mesh_object_name = value

    # "value" is deprecated. Use "mesh_object_name" instead
    value: bpy.props.StringProperty(  # type: ignore[valid-type]
        get=get_value,
        set=set_value,
    )

    bpy_object: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Object  # noqa: F722
    )


class BonePropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    @staticmethod
    def get_all_bone_property_groups(
        armature: bpy.types.Object,
    ) -> Iterator[bpy.types.PropertyGroup]:
        ext = armature.data.vrm_addon_extension
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
        armature_data: bpy.types.Armature,
        target: HumanBoneSpecification,
        bpy_bone_name_to_human_bone_specification: Dict[str, HumanBoneSpecification],
    ) -> Set[str]:
        bones = armature_data.bones
        result: Set[str] = set(bones.keys())
        remove_bones_tree: Union[Set[bpy.types.Bone], Set[bpy.types.EditBone]] = set()

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
                            bone
                            for bone in bones.values()
                            if not bone.parent and bone != parent
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
        if not self.bone_uuid:
            return ""
        if not self.armature_data_name:
            return ""
        armature_data = bpy.data.armatures.get(self.armature_data_name)
        if not armature_data:
            return ""

        # TODO: Optimization
        for bone in armature_data.bones:
            if bone.vrm_addon_extension.uuid == self.bone_uuid:
                return str(bone.name)

        return ""

    def set_bone_name(self, value: object) -> None:
        armature: Optional[bpy.types.Armature] = None

        # アーマチュアの複製が行われた場合を考えてself.armature_data_nameの振り直しをする
        self.search_one_time_uuid = uuid.uuid4().hex
        for found_armature in bpy.data.objects:
            if found_armature.type != "ARMATURE":
                continue
            if all(
                bone_property_group.search_one_time_uuid != self.search_one_time_uuid
                for bone_property_group in BonePropertyGroup.get_all_bone_property_groups(
                    found_armature
                )
            ):
                continue
            armature = found_armature
            break
        if not armature:
            self.armature_data_name = ""
            self.bone_uuid = ""
            return
        self.armature_data_name = armature.data.name

        # ボーンの複製が行われた場合を考えてUUIDの重複がある場合再割り当てを行う
        found_uuids = set()
        for bone in armature.data.bones:
            found_uuid = bone.vrm_addon_extension.uuid
            if not found_uuid or found_uuid in found_uuids:
                bone.vrm_addon_extension.uuid = uuid.uuid4().hex
            found_uuids.add(bone.vrm_addon_extension.uuid)

        value_str = str(value)
        if not value_str or value_str not in armature.data.bones:
            if not self.bone_uuid:
                return
            self.bone_uuid = ""
        elif (
            self.bone_uuid
            and self.bone_uuid
            == armature.data.bones[value_str].vrm_addon_extension.uuid
        ):
            return
        else:
            bone = armature.data.bones[value_str]
            self.bone_uuid = bone.vrm_addon_extension.uuid

        ext = armature.data.vrm_addon_extension
        for collider_group in ext.vrm0.secondary_animation.collider_groups:
            collider_group.refresh(armature)

        vrm0_bpy_bone_name_to_human_bone_specification: Dict[
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
                armature.data,
                vrm0_bpy_bone_name_to_human_bone_specification,
            )

        human_bone_name_to_human_bone = (
            ext.vrm1.humanoid.human_bones.human_bone_name_to_human_bone()
        )
        vrm1_bpy_bone_name_to_human_bone_specification: Dict[
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
                armature.data,
                vrm1_human_bone.HumanBoneSpecifications.get(human_bone_name),
                vrm1_bpy_bone_name_to_human_bone_specification,
            )

    bone_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Bone",  # noqa: F821
        get=get_bone_name,
        set=set_bone_name,
    )

    def get_value(self) -> str:
        logger.warning(
            "BonePropertyGroup.value is deprecated."
            + " Use BonePropertyGroup.bone_name instead."
        )
        return str(self.bone_name)

    def set_value(self, value: str) -> None:
        logger.warning(
            "BonePropertyGroup.value is deprecated."
            + " Use BonePropertyGroup.bone_name instead."
        )
        self.bone_name = value

    # "value" is deprecated. Use "bone_name" instead
    value: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Bone",  # noqa: F821
        get=get_value,
        set=set_value,
    )
    bone_uuid: bpy.props.StringProperty()  # type: ignore[valid-type]
    armature_data_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    search_one_time_uuid: bpy.props.StringProperty()  # type: ignore[valid-type]
