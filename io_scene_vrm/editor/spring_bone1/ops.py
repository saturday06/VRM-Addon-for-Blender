import uuid
from typing import Set

import bpy


class VRM_OT_add_spring_bone1_collider(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.add_spring_bone1_collider"
    bl_label = "Add Collider"
    bl_description = "Add VRM 1.0 Collider"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        collider = armature.data.vrm_addon_extension.spring_bone1.colliders.add()
        collider.uuid = uuid.uuid4().hex
        collider.shape.sphere.radius = 0.125
        collider.reset_bpy_object(context, armature)
        return {"FINISHED"}


class VRM_OT_remove_spring_bone1_collider(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.remove_spring_bone1_collider"
    bl_label = "Remove Collider"
    bl_description = "Remove VRM 0.x Collider"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    collider_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        spring_bone = armature.data.vrm_addon_extension.spring_bone1
        colliders = spring_bone.colliders
        if len(colliders) <= self.collider_index:
            return {"CANCELLED"}
        bpy_object = colliders[self.collider_index].bpy_object

        remove_objects = list(bpy_object.children) + [bpy_object]
        for collection in bpy.data.collections:
            for remove_object in remove_objects:
                remove_object.parent = None
                if remove_object.name in collection.objects:
                    collection.objects.unlink(remove_object)
        for remove_object in remove_objects:
            if remove_object.users <= 1:
                bpy.data.objects.remove(remove_object, do_unlink=True)

        collider_uuid = colliders[self.collider_index].uuid
        colliders.remove(self.collider_index)
        for collider_group in spring_bone.collider_groups:
            while True:
                removed = False
                for index, collider in enumerate(list(collider_group.colliders)):
                    if collider.collider_uuid != collider_uuid:
                        continue
                    collider_group.colliders.remove(index)
                    removed = True
                    break
                if not removed:
                    break

        return {"FINISHED"}


class VRM_OT_add_spring_bone1_spring(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.add_spring_bone1_spring"
    bl_label = "Add Spring"
    bl_description = "Add VRM 1.0 Spring"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        spring = armature.data.vrm_addon_extension.spring_bone1.springs.add()
        spring.vrm_name = "Spring"
        return {"FINISHED"}


class VRM_OT_remove_spring_bone1_spring(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.remove_spring_bone1_spring"
    bl_label = "Remove Spring"
    bl_description = "Remove VRM 1.0 Spring"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    spring_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        springs = armature.data.vrm_addon_extension.spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        springs.remove(self.spring_index)
        return {"FINISHED"}


class VRM_OT_add_spring_bone1_collider_group(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.add_spring_bone1_collider_group"
    bl_label = "Add Collider Group"
    bl_description = "Add VRM 1.0 Spring Bone Collider Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        collider_group = (
            armature.data.vrm_addon_extension.spring_bone1.collider_groups.add()
        )
        collider_group.vrm_name = "Collider Group"
        collider_group.uuid = uuid.uuid4().hex
        return {"FINISHED"}


class VRM_OT_remove_spring_bone1_collider_group(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.remove_spring_bone1_collider_group"
    bl_label = "Remove Collider Group"
    bl_description = "Remove VRM 1.0 Spring Bone Collider Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    collider_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        spring_bone = armature.data.vrm_addon_extension.spring_bone1
        collider_groups = spring_bone.collider_groups
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider_group_uuid = collider_groups[self.collider_group_index].uuid
        collider_groups.remove(self.collider_group_index)
        for spring in spring_bone.springs:
            while True:
                removed = False
                for index, collider_group in enumerate(list(spring.collider_groups)):
                    if collider_group.collider_group_uuid != collider_group_uuid:
                        continue
                    spring.collider_groups.remove(index)
                    removed = True
                    break
                if not removed:
                    break
        for collider_group in collider_groups:
            collider_group.fix_index()

        return {"FINISHED"}


class VRM_OT_add_spring_bone1_collider_group_collider(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.add_spring_bone1_collider_group_collider"
    bl_label = "Add Collider"
    bl_description = "Add VRM 1.0 Spring Bone Collider Group Collider"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    collider_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        collider_groups = armature.data.vrm_addon_extension.spring_bone1.collider_groups
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider_groups[self.collider_group_index].colliders.add()
        return {"FINISHED"}


class VRM_OT_remove_spring_bone1_collider_group_collider(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.remove_spring_bone1_collider_group_collider"
    bl_label = "Remove Collider"
    bl_description = "Remove VRM 1.0 Spring Bone Collider Group Collider"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    collider_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )
    collider_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        collider_groups = armature.data.vrm_addon_extension.spring_bone1.collider_groups
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        colliders = collider_groups[self.collider_group_index].colliders
        if len(colliders) <= self.collider_index:
            return {"CANCELLED"}
        colliders.remove(self.collider_index)
        return {"FINISHED"}


class VRM_OT_add_spring_bone1_spring_collider_group(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.add_spring_bone1_spring_collider_group"
    bl_label = "Add Collider Group"
    bl_description = "Add VRM 1.0 Spring Bone Spring Collider Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    spring_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        springs = armature.data.vrm_addon_extension.spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        springs[self.spring_index].collider_groups.add()
        return {"FINISHED"}


class VRM_OT_remove_spring_bone1_spring_collider_group(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.remove_spring_bone1_spring_collider_group"
    bl_label = "Remove Collider Group"
    bl_description = "Remove VRM 1.0 Spring Bone Spring Collider Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    spring_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )
    collider_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        springs = armature.data.vrm_addon_extension.spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        collider_groups = springs[self.spring_index].collider_groups
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider_groups.remove(self.collider_group_index)
        return {"FINISHED"}


class VRM_OT_add_spring_bone1_spring_joint(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.add_spring_bone1_spring_joint"
    bl_label = "Add Joint"
    bl_description = "Add VRM 1.0 Spring Bone Spring Joint"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    spring_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        springs = armature.data.vrm_addon_extension.spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        springs[self.spring_index].joints.add()
        return {"FINISHED"}


class VRM_OT_remove_spring_bone1_spring_joint(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.remove_spring_bone1_spring_joint"
    bl_label = "Remove Joint"
    bl_description = "Remove VRM 1.0 Spring Bone Spring Joint"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
    )
    spring_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )
    joint_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        options={"HIDDEN"},  # noqa: F821
        min=0,
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        springs = armature.data.vrm_addon_extension.spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        joints = springs[self.spring_index].joints
        if len(joints) <= self.joint_index:
            return {"CANCELLED"}
        joints.remove(self.joint_index)
        return {"FINISHED"}
