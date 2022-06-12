import uuid
from typing import Set

import bpy


class VRM_OT_add_spring_bone1_collider(  # noqa: N801
    bpy.types.Operator  # type: ignore[misc]
):
    bl_idname = "vrm.add_spring_bone1_collider"
    bl_label = "Add Collider"
    bl_description = "Add VRM 1.0 Collider"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if not isinstance(armature, bpy.types.Armature):
            return {"CANCELLED"}
        collider = armature.vrm_addon_extension.spring_bone1.colliders.add()
        collider.uuid = uuid.uuid4().hex

        obj = bpy.data.objects.new(
            name=f"{self.armature_data_name} Collider", object_data=None
        )
        collider.bpy_object = obj
        obj.empty_display_type = "SPHERE"
        obj.empty_display_size = 0.25
        collider.broadcast_bpy_object_name()
        context.scene.collection.objects.link(obj)
        return {"FINISHED"}


class VRM_OT_remove_spring_bone1_collider(  # noqa: N801
    bpy.types.Operator  # type: ignore[misc]
):
    bl_idname = "vrm.remove_spring_bone1_collider"
    bl_label = "Remove Collider"
    bl_description = "Remove VRM 0.x Collider"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    collider_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if not isinstance(armature, bpy.types.Armature):
            return {"CANCELLED"}
        spring_bone = armature.vrm_addon_extension.spring_bone1
        colliders = spring_bone.colliders
        if len(colliders) <= self.collider_index:
            return {"CANCELLED"}
        bpy_object = colliders[self.collider_index].bpy_object
        if bpy_object and bpy_object.name in context.scene.collection.objects:
            bpy_object.parent_type = "OBJECT"
            context.scene.collection.objects.unlink(bpy_object)
        collider_uuid = colliders[self.collider_index].uuid
        colliders.remove(self.collider_index)
        for collider_group in spring_bone.collider_groups:
            while True:
                removed = False
                for (index, collider) in enumerate(list(collider_group.colliders)):
                    if collider.collider_uuid != collider_uuid:
                        continue
                    collider_group.colliders.remove(index)
                    removed = True
                    break
                if not removed:
                    break

        return {"FINISHED"}


class VRM_OT_add_spring_bone1_spring(  # noqa: N801
    bpy.types.Operator  # type: ignore[misc]
):
    bl_idname = "vrm.add_spring_bone1_spring"
    bl_label = "Add Spring"
    bl_description = "Add VRM 1.0 Spring"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if not isinstance(armature, bpy.types.Armature):
            return {"CANCELLED"}
        spring = armature.vrm_addon_extension.spring_bone1.springs.add()
        spring.vrm_name = "Spring"
        return {"FINISHED"}


class VRM_OT_remove_spring_bone1_spring(  # noqa: N801
    bpy.types.Operator  # type: ignore[misc]
):
    bl_idname = "vrm.remove_spring_bone1_spring"
    bl_label = "Remove Spring"
    bl_description = "Remove VRM 1.0 Spring"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    spring_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if not isinstance(armature, bpy.types.Armature):
            return {"CANCELLED"}
        springs = armature.vrm_addon_extension.spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        springs.remove(self.spring_index)
        return {"FINISHED"}


class VRM_OT_add_spring_bone1_collider_group(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_spring_bone1_collider_group"
    bl_label = "Add Collider Group"
    bl_description = "Add VRM 1.0 Spring Bone Collider Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if not isinstance(armature, bpy.types.Armature):
            return {"CANCELLED"}
        collider_group = armature.vrm_addon_extension.spring_bone1.collider_groups.add()
        collider_group.vrm_name = "Collider Group"
        collider_group.uuid = uuid.uuid4().hex
        return {"FINISHED"}


class VRM_OT_remove_spring_bone1_collider_group(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_spring_bone1_collider_group"
    bl_label = "Remove Collider Group"
    bl_description = "Remove VRM 1.0 Spring Bone Collider Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    collider_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if not isinstance(armature, bpy.types.Armature):
            return {"CANCELLED"}
        spring_bone = armature.vrm_addon_extension.spring_bone1
        collider_groups = spring_bone.collider_groups
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider_group_uuid = collider_groups[self.collider_group_index].uuid
        collider_groups.remove(self.collider_group_index)
        for spring in spring_bone.springs:
            while True:
                removed = False
                for (index, collider_group) in enumerate(list(spring.collider_groups)):
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


class VRM_OT_add_spring_bone1_collider_group_collider(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_spring_bone1_collider_group_collider"
    bl_label = "Add Collider"
    bl_description = "Add VRM 1.0 Spring Bone Collider Group Collider"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    collider_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if not isinstance(armature, bpy.types.Armature):
            return {"CANCELLED"}
        collider_groups = armature.vrm_addon_extension.spring_bone1.collider_groups
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider_groups[self.collider_group_index].colliders.add()
        return {"FINISHED"}


class VRM_OT_remove_spring_bone1_collider_group_collider(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_spring_bone1_collider_group_collider"
    bl_label = "Remove Collider"
    bl_description = "Remove VRM 1.0 Spring Bone Collider Group Collider"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    collider_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )
    collider_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if not isinstance(armature, bpy.types.Armature):
            return {"CANCELLED"}
        collider_groups = armature.vrm_addon_extension.spring_bone1.collider_groups
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        colliders = collider_groups[self.collider_group_index].colliders
        if len(colliders) <= self.collider_index:
            return {"CANCELLED"}
        colliders.remove(self.collider_index)
        return {"FINISHED"}


class VRM_OT_add_spring_bone1_spring_collider_group(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_spring_bone1_spring_collider_group"
    bl_label = "Add Collider Group"
    bl_description = "Add VRM 1.0 Spring Bone Spring Collider Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    spring_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if not isinstance(armature, bpy.types.Armature):
            return {"CANCELLED"}
        springs = armature.vrm_addon_extension.spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        springs[self.spring_index].collider_groups.add()
        return {"FINISHED"}


class VRM_OT_remove_spring_bone1_spring_collider_group(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_spring_bone1_spring_collider_group"
    bl_label = "Remove Collider Group"
    bl_description = "Remove VRM 1.0 Spring Bone Spring Collider Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    spring_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )
    collider_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if not isinstance(armature, bpy.types.Armature):
            return {"CANCELLED"}
        springs = armature.vrm_addon_extension.spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        collider_groups = springs[self.spring_index].collider_groups
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider_groups.remove(self.collider_group_index)
        return {"FINISHED"}


class VRM_OT_add_spring_bone1_spring_joint(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_spring_bone1_spring_joint"
    bl_label = "Add Joint"
    bl_description = "Add VRM 1.0 Spring Bone Spring Joint"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    spring_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if not isinstance(armature, bpy.types.Armature):
            return {"CANCELLED"}
        springs = armature.vrm_addon_extension.spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        springs[self.spring_index].joints.add()
        return {"FINISHED"}


class VRM_OT_remove_spring_bone1_spring_joint(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_spring_bone1_spring_joint"
    bl_label = "Remove Joint"
    bl_description = "Remove VRM 1.0 Spring Bone Spring Joint"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    spring_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )
    joint_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if not isinstance(armature, bpy.types.Armature):
            return {"CANCELLED"}
        springs = armature.vrm_addon_extension.spring_bone1.springs
        if len(springs) <= self.spring_index:
            return {"CANCELLED"}
        joints = springs[self.spring_index].joints
        if len(joints) <= self.joint_index:
            return {"CANCELLED"}
        joints.remove(self.joint_index)
        return {"FINISHED"}
