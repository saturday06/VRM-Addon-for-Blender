import uuid
from typing import Set

import bpy

from ...common.human_bone_mapper.human_bone_mapper import create_human_bone_mapping
from .property_group import Vrm0HumanoidPropertyGroup


class VRM_OT_add_vrm0_first_person_mesh_annotation(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.add_vrm0_first_person_mesh_annotation"
    bl_label = "Add Mesh Annotation"
    bl_description = "Add VRM 0.x First Person Mesh Annotation"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature.data.vrm_addon_extension.vrm0.first_person.mesh_annotations.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm0_first_person_mesh_annotation(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.remove_vrm0_first_person_mesh_annotation"
    bl_label = "Remove Mesh Annotation"
    bl_description = "Remove VRM 0.x First Person Mesh Annotation"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    mesh_annotation_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        mesh_annotations = (
            armature.data.vrm_addon_extension.vrm0.first_person.mesh_annotations
        )
        if len(mesh_annotations) <= self.mesh_annotation_index:
            return {"CANCELLED"}
        mesh_annotations.remove(self.mesh_annotation_index)
        return {"FINISHED"}


class VRM_OT_add_vrm0_material_value_bind(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.add_vrm0_material_value_bind"
    bl_label = "Add Material Value Bind"
    bl_description = "Add VRM 0.x Blend Shape Material Value Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    blend_shape_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        blend_shape_groups = (
            armature.data.vrm_addon_extension.vrm0.blend_shape_master.blend_shape_groups
        )
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        blend_shape_groups[self.blend_shape_group_index].material_values.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm0_material_value_bind(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.remove_vrm0_material_value_bind"
    bl_label = "Remove Material Value Bind"
    bl_description = "Remove VRM 0.x Blend Shape Material Value Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    blend_shape_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )
    material_value_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        blend_shape_groups = (
            armature.data.vrm_addon_extension.vrm0.blend_shape_master.blend_shape_groups
        )
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        material_values = blend_shape_groups[
            self.blend_shape_group_index
        ].material_values
        if len(material_values) <= self.material_value_index:
            return {"CANCELLED"}
        material_values.remove(self.material_value_index)
        return {"FINISHED"}


class VRM_OT_add_vrm0_material_value_bind_target_value(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.add_vrm0_material_value_bind_target_value"
    bl_label = "Add Value"
    bl_description = "Add VRM 0.x Blend Shape Material Value Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    blend_shape_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )
    material_value_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        blend_shape_groups = (
            armature.data.vrm_addon_extension.vrm0.blend_shape_master.blend_shape_groups
        )
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        material_values = blend_shape_groups[
            self.blend_shape_group_index
        ].material_values
        if len(material_values) <= self.material_value_index:
            return {"CANCELLED"}
        material_values[self.material_value_index].target_value.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm0_material_value_bind_target_value(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.remove_vrm0_material_value_bind_target_value"
    bl_label = "Remove Value"
    bl_description = "Remove VRM 0.x Blend Shape Material Value Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    blend_shape_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )
    material_value_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )
    target_value_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        blend_shape_groups = (
            armature.data.vrm_addon_extension.vrm0.blend_shape_master.blend_shape_groups
        )
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        material_values = blend_shape_groups[
            self.blend_shape_group_index
        ].material_values
        if len(material_values) <= self.material_value_index:
            return {"CANCELLED"}
        target_value = material_values[self.material_value_index].target_value
        if len(target_value) <= self.target_value_index:
            return {"CANCELLED"}
        target_value.remove(self.target_value_index)
        return {"FINISHED"}


class VRM_OT_add_vrm0_blend_shape_bind(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.add_vrm0_blend_shape_bind"
    bl_label = "Add Blend Shape Bind"
    bl_description = "Add VRM 0.x Blend Shape Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    blend_shape_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        blend_shape_groups = (
            armature.data.vrm_addon_extension.vrm0.blend_shape_master.blend_shape_groups
        )
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        blend_shape_groups[self.blend_shape_group_index].binds.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm0_blend_shape_bind(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.remove_vrm0_blend_shape_bind"
    bl_label = "Remove Blend Shape Bind"
    bl_description = "Remove VRM 0.x Blend Shape Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    blend_shape_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )
    bind_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        blend_shape_groups = (
            armature.data.vrm_addon_extension.vrm0.blend_shape_master.blend_shape_groups
        )
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        binds = blend_shape_groups[self.blend_shape_group_index].binds
        if len(binds) <= self.bind_index:
            return {"CANCELLED"}
        binds.remove(self.bind_index)
        return {"FINISHED"}


class VRM_OT_add_vrm0_secondary_animation_collider_group_collider(
    bpy.types.Operator  # type: ignore[misc]
):
    bl_idname = "vrm.add_vrm0_secondary_animation_collider_group_collider"
    bl_label = "Add Collider"
    bl_description = "Add VRM 0.x Collider"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    collider_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )
    bone_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        collider_groups = (
            armature.data.vrm_addon_extension.vrm0.secondary_animation.collider_groups
        )
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider = collider_groups[self.collider_group_index].colliders.add()
        obj = bpy.data.objects.new(
            name=f"{self.armature_name}_{self.bone_name}_collider", object_data=None
        )
        collider.bpy_object = obj
        obj.parent = armature
        obj.empty_display_type = "SPHERE"
        obj.empty_display_size = 0.25
        if self.bone_name:
            obj.parent_type = "BONE"
            obj.parent_bone = self.bone_name
        else:
            obj.parent_type = "OBJECT"
        context.scene.collection.objects.link(obj)
        return {"FINISHED"}


class VRM_OT_remove_vrm0_secondary_animation_collider_group_collider(
    bpy.types.Operator  # type: ignore[misc]
):
    bl_idname = "vrm.remove_vrm0_secondary_animation_collider_group_collider"
    bl_label = "Remove Collider"
    bl_description = "Remove VRM 0.x Collider"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    collider_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )
    collider_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        collider_groups = (
            armature.data.vrm_addon_extension.vrm0.secondary_animation.collider_groups
        )
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        colliders = collider_groups[self.collider_group_index].colliders
        if len(colliders) <= self.collider_index:
            return {"CANCELLED"}
        bpy_object = colliders[self.collider_index].bpy_object
        if bpy_object and bpy_object.name in context.scene.collection.objects:
            bpy_object.parent_type = "OBJECT"
            context.scene.collection.objects.unlink(bpy_object)
        colliders.remove(self.collider_index)
        return {"FINISHED"}


class VRM_OT_add_vrm0_secondary_animation_group_bone(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.add_vrm0_secondary_animation_group_bone"
    bl_label = "Add Bone"
    bl_description = "Add VRM 0.x Secondary Animation Group Bone"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    bone_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        bone_groups = (
            armature.data.vrm_addon_extension.vrm0.secondary_animation.bone_groups
        )
        if len(bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        bone_groups[self.bone_group_index].bones.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm0_secondary_animation_group_bone(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.remove_vrm0_secondary_animation_group_bone"
    bl_label = "Remove Bone"
    bl_description = "Remove VRM 0.x Secondary Animation Group Bone"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    bone_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )
    bone_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        bone_groups = (
            armature.data.vrm_addon_extension.vrm0.secondary_animation.bone_groups
        )
        if len(bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        bones = bone_groups[self.bone_group_index].bones
        if len(bones) <= self.bone_index:
            return {"CANCELLED"}
        bones.remove(self.bone_index)
        return {"FINISHED"}


class VRM_OT_add_vrm0_secondary_animation_group_collider_group(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.add_vrm0_secondary_animation_group_collider_group"
    bl_label = "Add Collider Group"
    bl_description = "Add VRM 0.x Secondary Animation Group Collider Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    bone_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        bone_groups = (
            armature.data.vrm_addon_extension.vrm0.secondary_animation.bone_groups
        )
        if len(bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        bone_groups[self.bone_group_index].collider_groups.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm0_secondary_animation_group_collider_group(
    bpy.types.Operator  # type: ignore[misc]
):
    bl_idname = "vrm.remove_vrm0_secondary_animation_group_collider_group"
    bl_label = "Remove Collider Group"
    bl_description = "Remove VRM 0.x Secondary Animation Group Collider Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    bone_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )
    collider_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        bone_groups = (
            armature.data.vrm_addon_extension.vrm0.secondary_animation.bone_groups
        )
        if len(bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        collider_groups = bone_groups[self.bone_group_index].collider_groups
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider_groups.remove(self.collider_group_index)
        return {"FINISHED"}


class VRM_OT_add_vrm0_blend_shape_group(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.add_vrm0_blend_shape_group"
    bl_label = "Add Blend Shape Group"
    bl_description = "Add VRM 0.x Blend Shape Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        blend_shape_group = (
            armature.data.vrm_addon_extension.vrm0.blend_shape_master.blend_shape_groups.add()
        )
        blend_shape_group.name = self.name
        return {"FINISHED"}


class VRM_OT_remove_vrm0_blend_shape_group(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.remove_vrm0_blend_shape_group"
    bl_label = "Remove Blend Shape Group"
    bl_description = "Remove VRM 0.x Blend Shape Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    blend_shape_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        blend_shape_groups = (
            armature.data.vrm_addon_extension.vrm0.blend_shape_master.blend_shape_groups
        )
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        blend_shape_groups.remove(self.blend_shape_group_index)
        return {"FINISHED"}


class VRM_OT_add_vrm0_secondary_animation_group(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.add_vrm0_secondary_animation_group"
    bl_label = "Add Spring Bone"
    bl_description = "Add VRM 0.x Secondary Animation Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    blend_shape_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        armature.data.vrm_addon_extension.vrm0.secondary_animation.bone_groups.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm0_secondary_animation_group(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.remove_vrm0_secondary_animation_group"
    bl_label = "Remove Spring Bone"
    bl_description = "Remove VRM 0.x Secondary Animation Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    bone_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        bone_groups = (
            armature.data.vrm_addon_extension.vrm0.secondary_animation.bone_groups
        )
        if len(bone_groups) <= self.bone_group_index:
            return {"CANCELLED"}
        bone_groups.remove(self.bone_group_index)
        return {"FINISHED"}


class VRM_OT_add_vrm0_secondary_animation_collider_group(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.add_vrm0_secondary_animation_collider_group"
    bl_label = "Add Collider Group"
    bl_description = "Add VRM 0.x Secondary Animation Collider Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        collider_group = (
            armature.data.vrm_addon_extension.vrm0.secondary_animation.collider_groups.add()
        )
        collider_group.uuid = uuid.uuid4().hex
        collider_group.refresh(armature)
        return {"FINISHED"}


class VRM_OT_remove_vrm0_secondary_animation_collider_group(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.remove_vrm0_secondary_animation_collider_group"
    bl_label = "Remove Collider Group"
    bl_description = "Remove VRM 0.x Secondary Animation Collider Group"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    collider_group_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        collider_groups = (
            armature.data.vrm_addon_extension.vrm0.secondary_animation.collider_groups
        )
        if len(collider_groups) <= self.collider_group_index:
            return {"CANCELLED"}
        collider_groups.remove(self.collider_group_index)

        for (
            bone_group
        ) in armature.data.vrm_addon_extension.vrm0.secondary_animation.bone_groups:
            bone_group.refresh(armature)
        return {"FINISHED"}


class VRM_OT_assign_vrm0_humanoid_human_bones_automatically(bpy.types.Operator):  # type: ignore[misc]
    bl_idname = "vrm.assign_vrm0_humanoid_human_bones_automatically"
    bl_label = "Automatic Bone Assignment"
    bl_description = "Assign VRM 0.x Humanoid Human Bones"
    bl_options = {"REGISTER", "UNDO"}

    armature_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            return {"CANCELLED"}
        Vrm0HumanoidPropertyGroup.fixup_human_bones(armature)
        humanoid = armature.data.vrm_addon_extension.vrm0.humanoid
        bones = armature.data.bones
        for (
            bone_name,
            vrm1_specification,
        ) in create_human_bone_mapping(armature).items():
            bone = bones.get(bone_name)
            if not bone:
                continue
            human_bone_name = vrm1_specification.vrm0_name

            for human_bone in humanoid.human_bones:
                if (
                    human_bone.bone != human_bone_name.value
                    or human_bone.node.bone_name in human_bone.node_candidates
                    or bone_name not in human_bone.node_candidates
                ):
                    continue
                human_bone.node.bone_name = bone_name
                break

        return {"FINISHED"}
