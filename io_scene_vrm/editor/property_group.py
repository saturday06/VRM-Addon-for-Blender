import uuid
from typing import Any, Iterator, Optional, Set

import bpy


class ObjectPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    value: bpy.props.PointerProperty(  # type: ignore[valid-type]
        name="Object Value", type=bpy.types.Object  # noqa: F722
    )


class StringPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    value: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="String Value"  # noqa: F722
    )


class FloatPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    value: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Float Value"  # noqa: F722
    )


class MeshPropertyGroup(bpy.types.PropertyGroup):  # type: ignore[misc]
    def get_value(self) -> str:
        if (
            not self.link_to_mesh
            or not self.link_to_mesh.name
            or not self.link_to_mesh.parent
            or self.link_to_mesh.parent.type != "MESH"
            or not self.link_to_mesh.parent.data
            or not self.link_to_mesh.parent.data.name
        ):
            return ""
        return str(self.link_to_mesh.parent.data.name)

    def set_value(self, value: Any) -> None:
        if not isinstance(value, str) or value not in bpy.data.meshes:
            return
        mesh = bpy.data.meshes[value]
        mesh_obj: Optional[bpy.types.Object] = None
        for obj in bpy.data.objects:
            if obj.data == mesh:
                mesh_obj = obj
                break
        if mesh_obj is None:
            return

        if not self.link_to_mesh or not self.link_to_mesh.name:
            uuid_str = uuid.uuid4().hex
            self.link_to_mesh = bpy.data.objects.new(
                name="VrmAddonLinkToMesh" + uuid_str, object_data=None
            )
        self.link_to_mesh.parent = mesh_obj

    value: bpy.props.StringProperty(  # type: ignore[valid-type]
        get=get_value, set=set_value
    )
    link_to_mesh: bpy.props.PointerProperty(  # type: ignore[valid-type]
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

    def refresh(self, armature: bpy.types.Object) -> None:
        if (
            self.link_to_bone
            and self.link_to_bone.parent
            and self.link_to_bone.parent == armature
        ):
            return

        value = self.value
        uuid_str = uuid.uuid4().hex
        self.link_to_bone = bpy.data.objects.new(
            name="VrmAddonLinkToBone" + uuid_str, object_data=None
        )
        self.link_to_bone.parent = armature
        self.value = value

    def get_value(self) -> str:
        if (
            self.link_to_bone
            and self.link_to_bone.parent_bone
            and self.link_to_bone.parent
            and self.link_to_bone.parent.name
            and self.link_to_bone.parent.type == "ARMATURE"
            and self.link_to_bone.parent_bone in self.link_to_bone.parent.data.bones
        ):
            return str(self.link_to_bone.parent_bone)
        return ""

    def set_value(self, value: Any) -> None:
        if not self.link_to_bone or not self.link_to_bone.parent:
            for armature in bpy.data.objects:
                if armature.type != "ARMATURE":
                    continue
                if all(
                    bone_property_group != self
                    for bone_property_group in BonePropertyGroup.get_all_bone_property_groups(
                        armature
                    )
                ):
                    continue
                self.refresh(armature)
                break
        if not self.link_to_bone.parent:
            print("WARNING: No armature found")
            return

        value_str = str(value)
        if not value_str or value_str not in self.link_to_bone.parent.data.bones:
            self.link_to_bone.parent_type = "OBJECT"
            self.link_to_bone.parent_bone = ""
        elif self.link_to_bone.parent_bone == value_str:
            return
        else:
            self.link_to_bone.parent_bone = value_str
            self.link_to_bone.parent_type = "BONE"

        armature_data = self.link_to_bone.parent.data
        ext = armature_data.vrm_addon_extension
        for collider_group in ext.vrm0.secondary_animation.collider_groups:
            collider_group.refresh(self.link_to_bone.parent)

        assigned_blender_bone_names: Set[str] = {
            human_bone.node.value
            for human_bone in ext.vrm0.humanoid.human_bones
            if human_bone.node.value
        }
        for human_bone in ext.vrm0.humanoid.human_bones:
            human_bone.update_node_candidates(
                armature_data, assigned_blender_bone_names
            )

    value: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Bone",  # noqa: F821
        get=get_value,
        set=set_value,
    )
    link_to_bone: bpy.props.PointerProperty(  # type: ignore[valid-type]
        type=bpy.types.Object  # noqa: F722
    )
