from typing import Set

import bpy


class VRM_OT_add_vrm1_meta_author(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm1_meta_author"
    bl_label = "Add Author"
    bl_description = "Add VRM 1.0 Meta Author"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if not isinstance(armature, bpy.types.Armature):
            return {"CANCELLED"}
        armature.vrm_addon_extension.vrm1.meta.authors.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm1_meta_author(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_vrm1_meta_author"
    bl_label = "Remove Author"
    bl_description = "Remove VRM 1.0 Meta Author"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    author_index: bpy.props.IntProperty()  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if not isinstance(armature, bpy.types.Armature):
            return {"CANCELLED"}
        authors = armature.vrm_addon_extension.vrm1.meta.authors
        if len(authors) <= self.author_index:
            return {"CANCELLED"}
        authors.remove(self.author_index)
        return {"FINISHED"}


class VRM_OT_add_vrm1_meta_reference(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm1_meta_reference"
    bl_label = "Add Reference"
    bl_description = "Add VRM 1.0 Meta Reference"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if not isinstance(armature, bpy.types.Armature):
            return {"CANCELLED"}
        armature.vrm_addon_extension.vrm1.meta.references.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm1_meta_reference(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_vrm1_meta_reference"
    bl_label = "Remove Reference"
    bl_description = "Remove VRM 1.0 Meta Reference"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    reference_index: bpy.props.IntProperty()  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if not isinstance(armature, bpy.types.Armature):
            return {"CANCELLED"}
        references = armature.vrm_addon_extension.vrm1.meta.references
        if len(references) <= self.reference_index:
            return {"CANCELLED"}
        references.remove(self.reference_index)
        return {"FINISHED"}


class VRM_OT_add_vrm1_expressions_custom_expression(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm1_expressions_custom_expression"
    bl_label = "Add Custom Expression"
    bl_description = "Add VRM 1.0 Custom Expression"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    custom_expression_name: bpy.props.StringProperty()  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if not isinstance(armature, bpy.types.Armature):
            return {"CANCELLED"}
        custom_expression = armature.vrm_addon_extension.vrm1.expressions.custom.add()
        custom_expression.custom_name = self.custom_expression_name
        return {"FINISHED"}


class VRM_OT_remove_vrm1_expressions_custom_expression(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_vrm1_expressions_custom_expression"
    bl_label = "Remove Custom Expression"
    bl_description = "Remove VRM 1.0 Custom Expression"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    custom_expression_name: bpy.props.StringProperty()  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if not isinstance(armature, bpy.types.Armature):
            return {"CANCELLED"}
        for custom_index, custom_expression in enumerate(
            list(armature.vrm_addon_extension.vrm1.expressions.custom.values())
        ):
            if custom_expression.custom_name == self.custom_expression_name:
                armature.vrm_addon_extension.vrm1.expressions.custom.remove(
                    custom_index
                )
                return {"FINISHED"}
        return {"CANCELLED"}


class VRM_OT_add_vrm1_first_person_mesh_annotation(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm1_first_person_mesh_annotation"
    bl_label = "Add Mesh Annotation"
    bl_description = "Add VRM 1.0 First Person Mesh Annotation"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if armature is None:
            return {"CANCELLED"}
        armature.vrm_addon_extension.vrm1.first_person.mesh_annotations.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm1_first_person_mesh_annotation(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_vrm1_first_person_mesh_annotation"
    bl_label = "Remove Mesh Annotation"
    bl_description = "Remove VRM 1.0 First Person Mesh Annotation"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    mesh_annotation_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if armature is None:
            return {"CANCELLED"}
        mesh_annotations = (
            armature.vrm_addon_extension.vrm1.first_person.mesh_annotations
        )
        if len(mesh_annotations) <= self.mesh_annotation_index:
            return {"CANCELLED"}
        mesh_annotations.remove(self.mesh_annotation_index)
        return {"FINISHED"}


class VRM_OT_add_vrm1_material_value_bind(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm1_material_value_bind"
    bl_label = "Add material value bind"
    bl_description = "Add VRM 0.x BlendShape Material Value Bind"
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
            armature.data.vrm_addon_extension.vrm1.blend_shape_master.blend_shape_groups
        )
        if len(blend_shape_groups) <= self.blend_shape_group_index:
            return {"CANCELLED"}
        blend_shape_groups[self.blend_shape_group_index].material_values.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm1_material_value_bind(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_vrm1_material_value_bind"
    bl_label = "Remove material value bind"
    bl_description = "Remove VRM 0.x BlendShape Material Value Bind"
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
            armature.data.vrm_addon_extension.vrm1.blend_shape_master.blend_shape_groups
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


class VRM_OT_add_vrm1_material_value_bind_target_value(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm1_material_value_bind_target_value"
    bl_label = "Add value"
    bl_description = "Add VRM 0.x BlendShape Material Value Bind"
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
            armature.data.vrm_addon_extension.vrm1.blend_shape_master.blend_shape_groups
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


class VRM_OT_remove_vrm1_material_value_bind_target_value(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_vrm1_material_value_bind_target_value"
    bl_label = "Remove value"
    bl_description = "Remove VRM 0.x BlendShape Material Value Bind"
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
            armature.data.vrm_addon_extension.vrm1.blend_shape_master.blend_shape_groups
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


class VRM_OT_add_vrm1_expression_morph_target_bind(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm1_expression_morph_target_bind"
    bl_label = "Add Morph Target Bind"
    bl_description = "Add VRM 1.0 Expression Morph Target Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    expression_name: bpy.props.StringProperty()  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if armature is None:
            return {"CANCELLED"}
        expressions = armature.vrm_addon_extension.vrm1.expressions
        expression = expressions.all_name_to_expression_dict().get(self.expression_name)
        if expression is None:
            return {"CANCELLED"}
        expression.morph_target_binds.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm1_expression_morph_target_bind(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_vrm1_expression_morph_target_bind"
    bl_label = "Remove Morph Target Bind"
    bl_description = "Remove VRM 1.0 Expression Morph Target Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    expression_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    bind_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if armature is None:
            return {"CANCELLED"}
        expressions = armature.vrm_addon_extension.vrm1.expressions
        expression = expressions.all_name_to_expression_dict().get(self.expression_name)
        if expression is None:
            return {"CANCELLED"}
        if len(expression.morph_target_binds) <= self.bind_index:
            return {"CANCELLED"}
        expression.morph_target_binds.remove(self.bind_index)
        return {"FINISHED"}


class VRM_OT_add_vrm1_expression_material_color_bind(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm1_expression_material_color_bind"
    bl_label = "Add Material Color Bind"
    bl_description = "Add VRM 1.0 Expression Material Value Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    expression_name: bpy.props.StringProperty()  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if armature is None:
            return {"CANCELLED"}
        expression = armature.vrm_addon_extension.vrm1.expressions.all_name_to_expression_dict().get(
            self.expression_name
        )
        if expression is None:
            return {"CANCELLED"}
        expression.material_color_binds.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm1_expression_material_color_bind(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_vrm1_expression_material_color_bind"
    bl_label = "Remove Material Color Bind"
    bl_description = "Remove VRM 1.0 Expression Material Color Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    expression_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    bind_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if armature is None:
            return {"CANCELLED"}
        expression = armature.vrm_addon_extension.vrm1.expressions.all_name_to_expression_dict().get(
            self.expression_name
        )
        if expression is None:
            return {"CANCELLED"}
        if len(expression.material_color_binds) <= self.bind_index:
            return {"CANCELLED"}
        expression.material_color_binds.remove(self.bind_index)
        return {"FINISHED"}


class VRM_OT_add_vrm1_expression_texture_transform_bind(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.add_vrm1_expression_texture_transform_bind"
    bl_label = "Add Texture Transform Bind"
    bl_description = "Add VRM 1.0 Expression Texture Transform Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    expression_name: bpy.props.StringProperty()  # type: ignore[valid-type]

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if armature is None:
            return {"CANCELLED"}
        expression = armature.vrm_addon_extension.vrm1.expressions.all_name_to_expression_dict().get(
            self.expression_name
        )
        if expression is None:
            return {"CANCELLED"}
        expression.texture_transform_binds.add()
        return {"FINISHED"}


class VRM_OT_remove_vrm1_expression_texture_transform_bind(bpy.types.Operator):  # type: ignore[misc] # noqa: N801
    bl_idname = "vrm.remove_vrm1_expression_texture_transform_bind"
    bl_label = "Remove Texture Transform Bind"
    bl_description = "Remove VRM 1.0 Expression Texture Transform Bind"
    bl_options = {"REGISTER", "UNDO"}

    armature_data_name: bpy.props.StringProperty(  # type: ignore[valid-type]
        options={"HIDDEN"}  # noqa: F821
    )
    expression_name: bpy.props.StringProperty()  # type: ignore[valid-type]
    bind_index: bpy.props.IntProperty(  # type: ignore[valid-type]
        min=0, options={"HIDDEN"}  # noqa: F821
    )

    def execute(self, _context: bpy.types.Context) -> Set[str]:
        armature = bpy.data.armatures.get(self.armature_data_name)
        if armature is None:
            return {"CANCELLED"}
        expression = armature.vrm_addon_extension.vrm1.expressions.all_name_to_expression_dict().get(
            self.expression_name
        )
        if expression is None:
            return {"CANCELLED"}
        if len(expression.texture_transform_binds) <= self.bind_index:
            return {"CANCELLED"}
        expression.texture_transform_binds.remove(self.bind_index)
        return {"FINISHED"}
