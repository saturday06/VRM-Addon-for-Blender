# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import secrets
import string
from abc import ABC, abstractmethod
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional, TypeVar, Union

import bmesh
from bpy.types import Armature, Constraint, Context, Mesh, NodesModifier, Object
from mathutils import Vector

from ..common import shader
from ..common.convert import Json
from ..common.deep import make_json
from ..common.logger import get_logger
from ..common.vrm0 import human_bone as vrm0_human_bone
from ..common.vrm1 import human_bone as vrm1_human_bone
from ..common.workspace import save_workspace
from ..editor.extension_accessor import get_armature_extension, get_material_extension
from ..editor.property_group import BonePropertyGroup, BonePropertyGroupType
from ..editor.search import MESH_CONVERTIBLE_OBJECT_TYPES
from ..external import io_scene_gltf2_support

HumanBoneSpecification = TypeVar(
    "HumanBoneSpecification",
    vrm0_human_bone.HumanBoneSpecification,
    vrm1_human_bone.HumanBoneSpecification,
)


_logger = get_logger(__name__)


@dataclass(frozen=True)
class FlexibleHierarchyBoneSetup:
    original_bone_settings: Mapping[str, tuple[Optional[str], bool]]
    pose_bone_name_and_muted_constraint_name: list[tuple[str, str]]


class AbstractBaseVrmExporter(ABC):
    def __init__(
        self,
        context: Context,
        export_objects: Sequence[Object],
        armature: Object,
    ) -> None:
        self.context = context
        self.export_objects = export_objects
        self.armature = armature
        self.export_id = "BlenderVrmAddonExport" + (
            "".join(secrets.choice(string.digits) for _ in range(10))
        )
        self.gltf2_addon_export_settings = (
            io_scene_gltf2_support.create_export_settings()
        )

        armature_data = self.armature.data
        if not isinstance(armature_data, Armature):
            message = f"{type(armature_data)} is not an Armature"
            raise TypeError(message)

    @abstractmethod
    def export(self) -> Optional[bytes]:
        pass

    @staticmethod
    def enter_clear_blend_shape_proxy_previews(
        context: Context,
        armature_data: Armature,
    ) -> tuple[Sequence[float], Mapping[str, float], Mapping[str, Mapping[str, float]]]:
        saved_key_block_values: dict[str, Mapping[str, float]] = {}
        for mesh in context.blend_data.meshes:
            shape_keys = mesh.shape_keys
            if not shape_keys:
                continue
            saved_key_block_values[mesh.name] = {
                key_block.name: key_block.value for key_block in shape_keys.key_blocks
            }

        ext = get_armature_extension(armature_data)

        saved_vrm1_previews: dict[str, float] = {}
        for (
            name,
            expression,
        ) in ext.vrm1.expressions.all_name_to_expression_dict().items():
            saved_vrm1_previews[name] = expression.preview
            expression.preview = 0

        saved_vrm0_previews: list[float] = []
        for blend_shape_group in ext.vrm0.blend_shape_master.blend_shape_groups:
            saved_vrm0_previews.append(blend_shape_group.preview)
            blend_shape_group.preview = 0

        return saved_vrm0_previews, saved_vrm1_previews, saved_key_block_values

    @staticmethod
    def leave_clear_blend_shape_proxy_previews(
        context: Context,
        armature_data: Armature,
        saved_vrm0_previews: Sequence[float],
        saved_vrm1_previews: Mapping[str, float],
        saved_key_block_values: Mapping[str, Mapping[str, float]],
    ) -> None:
        ext = get_armature_extension(armature_data)

        for blend_shape_group, blend_shape_preview in reversed(
            list(
                zip(ext.vrm0.blend_shape_master.blend_shape_groups, saved_vrm0_previews)
            )
        ):
            blend_shape_group.preview = blend_shape_preview

        for (
            name,
            expression,
        ) in ext.vrm1.expressions.all_name_to_expression_dict().items():
            expression_preview = saved_vrm1_previews.get(name)
            if expression_preview is not None:
                expression.preview = expression_preview

        for mesh_name, key_block_name_to_values in reversed(
            list(saved_key_block_values.items())
        ):
            mesh = context.blend_data.meshes.get(mesh_name)
            if not mesh:
                continue

            shape_keys = mesh.shape_keys
            if not shape_keys:
                continue

            for key_block in shape_keys.key_blocks:
                shape_key_value = key_block_name_to_values.get(key_block.name)
                if shape_key_value is not None:
                    key_block.value = shape_key_value

    @contextmanager
    def clear_blend_shape_proxy_previews(
        self, context: Context, armature_data: Armature
    ) -> Generator[None]:
        saved_vrm0_previews, saved_vrm1_previews, saved_key_block_values = (
            self.enter_clear_blend_shape_proxy_previews(context, armature_data)
        )
        try:
            yield
            # After yield, native bpy objects may be deleted or frames may advance,
            # becoming invalid. Accessing them in this state causes crashes, so
            # be careful not to access potentially invalid native objects after yield
        finally:
            self.leave_clear_blend_shape_proxy_previews(
                context,
                armature_data,
                saved_vrm0_previews,
                saved_vrm1_previews,
                saved_key_block_values,
            )

    def enter_enable_deform_for_all_referenced_bones(
        self, armature_data: Armature
    ) -> list[str]:
        ext = get_armature_extension(armature_data)
        modified_non_deform_bone_names = list[str]()
        for (
            bone_property_group,
            bone_property_group_type,
        ) in BonePropertyGroup.get_all_bone_property_groups(armature_data):
            bone = armature_data.bones.get(bone_property_group.bone_name)
            if not bone or bone.use_deform:
                continue
            if (
                ext.is_vrm0()
                and BonePropertyGroupType.is_vrm0(bone_property_group_type)
            ) or (
                ext.is_vrm1()
                and BonePropertyGroupType.is_vrm1(bone_property_group_type)
            ):
                bone.use_deform = True
                modified_non_deform_bone_names.append(bone.name)
        return modified_non_deform_bone_names

    def leave_enable_deform_for_all_referenced_bones(
        self, armature_data: Armature, modified_non_deform_bone_names: list[str]
    ) -> None:
        for modified_non_deform_bone_name in reversed(modified_non_deform_bone_names):
            bone = armature_data.bones.get(modified_non_deform_bone_name)
            if bone and bone.use_deform:
                bone.use_deform = False

    @contextmanager
    def enable_deform_for_all_referenced_bones(
        self, armature_data: Armature
    ) -> Generator[None]:
        modified_non_deform_bone_names = (
            self.enter_enable_deform_for_all_referenced_bones(armature_data)
        )
        try:
            yield
        finally:
            self.leave_enable_deform_for_all_referenced_bones(
                armature_data, modified_non_deform_bone_names
            )

    @staticmethod
    def enter_hide_mtoon1_outline_geometry_nodes(
        context: Context,
    ) -> dict[str, list[tuple[str, bool, bool]]]:
        object_name_to_modifiers: dict[str, list[tuple[str, bool, bool]]] = {}
        for obj in context.blend_data.objects:
            for modifier in obj.modifiers:
                if not modifier.show_viewport:
                    continue
                if modifier.type != "NODES":
                    continue
                if not isinstance(modifier, NodesModifier):
                    continue
                node_group = modifier.node_group
                if (
                    not node_group
                    or node_group.name != shader.OUTLINE_GEOMETRY_GROUP_NAME
                ):
                    continue
                modifiers = object_name_to_modifiers.get(obj.name)
                if modifiers is None:
                    modifiers = []
                    object_name_to_modifiers[obj.name] = modifiers
                modifiers = object_name_to_modifiers[obj.name]
                modifiers.append(
                    (
                        modifier.name,
                        modifier.show_render,
                        modifier.show_viewport,
                    )
                )
                if modifier.show_render:
                    modifier.show_render = False
                if modifier.show_viewport:
                    modifier.show_viewport = False
        return object_name_to_modifiers

    @staticmethod
    def exit_hide_mtoon1_outline_geometry_nodes(
        context: Context,
        object_name_to_modifiers: dict[str, list[tuple[str, bool, bool]]],
    ) -> None:
        for object_name, modifiers in reversed(list(object_name_to_modifiers.items())):
            for modifier_name, render, viewport in reversed(modifiers):
                obj = context.blend_data.objects.get(object_name)
                if not obj:
                    continue
                modifier = obj.modifiers.get(modifier_name)
                if (
                    not modifier
                    or modifier.type != "NODES"
                    or not isinstance(modifier, NodesModifier)
                ):
                    continue
                node_group = modifier.node_group
                if (
                    not node_group
                    or node_group.name != shader.OUTLINE_GEOMETRY_GROUP_NAME
                ):
                    continue
                if modifier.show_render != render:
                    modifier.show_render = render
                if modifier.show_viewport != viewport:
                    modifier.show_viewport = viewport

    @staticmethod
    @contextmanager
    def hide_mtoon1_outline_geometry_nodes(context: Context) -> Generator[None]:
        object_name_to_modifier_names = (
            AbstractBaseVrmExporter.enter_hide_mtoon1_outline_geometry_nodes(context)
        )
        try:
            yield
            # After yield, native bpy objects may be deleted or frames may advance,
            # becoming invalid. Accessing them in this state causes crashes, so
            # be careful not to access potentially invalid native objects after yield
        finally:
            AbstractBaseVrmExporter.exit_hide_mtoon1_outline_geometry_nodes(
                context, object_name_to_modifier_names
            )

    @staticmethod
    def create_child_bone_name_to_parent_bone_name(
        armature_data: Armature,
        assigned_human_bone_specification_to_bone_name: Mapping[
            HumanBoneSpecification, str
        ],
        all_human_bone_specifications: Sequence[HumanBoneSpecification],
    ) -> Mapping[str, str]:
        assigned_bone_names = set(
            assigned_human_bone_specification_to_bone_name.values()
        )
        child_bone_name_to_parent_bone_name: dict[str, str] = {}
        for human_bone_specification in all_human_bone_specifications:
            child_bone_name = assigned_human_bone_specification_to_bone_name.get(
                human_bone_specification
            )
            if not child_bone_name:
                continue
            child_bone = armature_data.bones.get(child_bone_name)
            if not child_bone:
                continue
            ancestor = human_bone_specification.parent
            while ancestor:
                ancestor_bone_name = assigned_human_bone_specification_to_bone_name.get(
                    ancestor
                )
                if not ancestor_bone_name:
                    if ancestor.requirement:
                        break
                    ancestor = ancestor.parent
                    continue

                search_bone = child_bone.parent
                while search_bone:
                    if search_bone.name in assigned_bone_names:
                        break
                    search_bone = search_bone.parent
                if search_bone and search_bone.name == ancestor_bone_name:
                    break

                child_bone_name_to_parent_bone_name[child_bone_name] = (
                    ancestor_bone_name
                )
                break

        return child_bone_name_to_parent_bone_name

    @staticmethod
    def reparent_edit_bones(
        context: Context,
        armature_object: Object,
        assigned_bone_names: Mapping[HumanBoneSpecification, str],
        child_bone_name_to_parent_bone_name: Mapping[str, str],
    ) -> Mapping[str, tuple[Optional[str], bool]]:
        if not isinstance(armature_data := armature_object.data, Armature):
            return {}
        original_bone_settings: dict[str, tuple[Optional[str], bool]] = {}
        with save_workspace(context, armature_object, mode="EDIT"):
            for bone_name in assigned_bone_names.values():
                edit_bone = armature_data.edit_bones.get(bone_name)
                if not edit_bone:
                    continue
                original_bone_settings[bone_name] = (
                    edit_bone.parent.name if edit_bone.parent else None,
                    edit_bone.use_connect,
                )
                edit_bone.use_connect = False

            for (
                child_bone_name,
                ancestor_bone_name,
            ) in child_bone_name_to_parent_bone_name.items():
                child_edit_bone = armature_data.edit_bones.get(child_bone_name)
                parent_edit_bone = armature_data.edit_bones.get(ancestor_bone_name)
                if not child_edit_bone or not parent_edit_bone:
                    continue
                child_edit_bone.parent = parent_edit_bone

        return original_bone_settings

    @staticmethod
    def enter_setup_flexible_hierarchy_bones(
        _context: Context,
        _armature_object: Object,
        _export_objects: Sequence[Object],
    ) -> Optional[FlexibleHierarchyBoneSetup]:
        """Build the flexible hierarchy setup when a subclass supports it.

        Subclasses can override this to build the assigned-bone map and call
        ``reparent_edit_bones``. The default returns ``None``.
        """
        return None

    @staticmethod
    def leave_setup_flexible_hierarchy_bones(
        context: Context,
        armature_object: Object,
        flexible_hierarchy_bone_setup: FlexibleHierarchyBoneSetup,
    ) -> None:
        """Restore bone parents to the saved state.

        Use the state recorded by ``enter_setup_flexible_hierarchy_bones``.
        """
        armature_data = armature_object.data
        if not isinstance(armature_data, Armature):
            return

        with save_workspace(context, armature_object, mode="EDIT"):
            for (
                bone_name
            ) in flexible_hierarchy_bone_setup.original_bone_settings.keys():
                edit_bone = armature_data.edit_bones.get(bone_name)
                if edit_bone:
                    edit_bone.parent = None
                    edit_bone.use_connect = False

            for bone_name, (
                parent_name,
                use_connect,
            ) in flexible_hierarchy_bone_setup.original_bone_settings.items():
                edit_bone = armature_data.edit_bones.get(bone_name)
                if not edit_bone:
                    continue
                if parent_name:
                    parent_edit_bone = armature_data.edit_bones.get(parent_name)
                    if parent_edit_bone:
                        edit_bone.parent = parent_edit_bone
                edit_bone.use_connect = use_connect

        for pose_bone_name, muted_constraint_name in reversed(
            flexible_hierarchy_bone_setup.pose_bone_name_and_muted_constraint_name
        ):
            pose_bone = armature_object.pose.bones.get(pose_bone_name)
            if not pose_bone:
                continue
            constraint = pose_bone.constraints.get(muted_constraint_name)
            if isinstance(constraint, Constraint) and constraint.mute:
                constraint.mute = False

    @classmethod
    @contextmanager
    def setup_flexible_hierarchy_bones(
        cls,
        context: Context,
        armature: Object,
        export_objects: Sequence[Object],
    ) -> Generator[None]:
        flexible_hierarchy_bone_setup = cls.enter_setup_flexible_hierarchy_bones(
            context,
            armature,
            export_objects,
        )
        try:
            yield
        finally:
            if flexible_hierarchy_bone_setup is not None:
                cls.leave_setup_flexible_hierarchy_bones(
                    context,
                    armature,
                    flexible_hierarchy_bone_setup,
                )

    @staticmethod
    def setup_mtoon_gltf_fallback_nodes(context: Context, *, is_vrm0: bool) -> None:
        """Reflect MToon node values to nodes used for glTF fallback values.

        When MToon nodes are directly edited, glTF fallback values are not
        automatically set. Therefore, we explicitly set values during export.
        """
        for material in context.blend_data.materials:
            mtoon1 = get_material_extension(material).mtoon1
            if not mtoon1.enabled:
                continue
            mtoon1.pbr_metallic_roughness.base_color_factor = (
                mtoon1.pbr_metallic_roughness.base_color_factor
            )
            mtoon1.emissive_factor = mtoon1.emissive_factor
            mtoon1.normal_texture.scale = mtoon1.normal_texture.scale
            mtoon1.extensions.khr_materials_emissive_strength.emissive_strength = (
                mtoon1.extensions.khr_materials_emissive_strength.emissive_strength
            )
            for texture in mtoon1.all_textures(downgrade_to_mtoon0=is_vrm0):
                texture.source = texture.get_connected_node_image()


def assign_dict(
    target: dict[str, Json],
    key: str,
    value: Union[Json, tuple[float, float, float], tuple[float, float, float, float]],
    default_value: Json = None,
) -> bool:
    if value is None or value == default_value:
        return False
    target[key] = make_json(value)
    return True


def generate_evaluated_mesh(context: Context, obj: Object) -> Optional[Mesh]:
    obj_data = obj.data
    if obj_data is None:
        return None

    # https://docs.blender.org/api/2.80/Depsgraph.html
    # TODO: Shape keys may sometimes break
    depsgraph = context.evaluated_depsgraph_get()
    evaluated_obj = obj.evaluated_get(depsgraph)
    evaluated_temporary_mesh = evaluated_obj.to_mesh(
        preserve_all_data_layers=True, depsgraph=depsgraph
    )
    if not evaluated_temporary_mesh:
        return None

    # The documentation says to use BlendDataMeshes.new_from_object(), but
    # that doesn't preserve shape keys.
    if isinstance(obj_data, Mesh):
        evaluated_mesh = obj_data.copy()
    else:
        _logger.error(
            "Unexpected object type: %s name=%s",
            type(obj_data),
            obj_data.name,
        )
        evaluated_mesh = context.blend_data.meshes.new(name=obj_data.name)

    bm = bmesh.new()
    bm.from_mesh(evaluated_temporary_mesh)
    bm.to_mesh(evaluated_mesh)
    bm.free()

    evaluated_obj.to_mesh_clear()
    return evaluated_mesh


def force_apply_modifiers(context: Context, obj: Object) -> Optional[Mesh]:
    if obj.type not in MESH_CONVERTIBLE_OBJECT_TYPES:
        return None

    key_block_name_to_value: dict[str, float] = {}
    if isinstance(mesh_data := obj.data, Mesh) and (shape_keys := mesh_data.shape_keys):
        for key_block in shape_keys.key_blocks:
            key_block_name_to_value[key_block.name] = key_block.value
            key_block.value = 0

        context.view_layer.update()

    evaluated_mesh_data: Optional[Mesh] = None
    try:
        evaluated_mesh_data = generate_evaluated_mesh(context, obj)
        if evaluated_mesh_data is None:
            return None

        obj_data = obj.data
        if obj_data is None:
            return evaluated_mesh_data

        if not isinstance(obj_data, Mesh):
            return evaluated_mesh_data

        shape_keys = obj_data.shape_keys
        if not shape_keys:
            return evaluated_mesh_data

        evaluated_mesh_data_shape_keys = evaluated_mesh_data.shape_keys
        if not evaluated_mesh_data_shape_keys:
            return evaluated_mesh_data

        # If the mesh has shape keys, reproduce them as much as possible
        for key_block in shape_keys.key_blocks:
            evaluated_key_block = evaluated_mesh_data_shape_keys.key_blocks.get(
                key_block.name
            )
            if not evaluated_key_block:
                continue

            if key_block.name == shape_keys.reference_key.name:
                continue

            key_block.value = 1.0
            context.view_layer.update()

            depsgraph = context.evaluated_depsgraph_get()
            baked_key_block_obj = obj.evaluated_get(depsgraph)
            baked_key_block_mesh = baked_key_block_obj.to_mesh(
                preserve_all_data_layers=True, depsgraph=depsgraph
            )
            if baked_key_block_mesh:
                evaluated_key_block_data = evaluated_key_block.data
                baked_key_block_mesh_vertices = baked_key_block_mesh.vertices

                # TODO: If the number of vertices is different, we should use advanced
                # graph matching algorithm.
                for i in range(
                    min(
                        len(evaluated_key_block_data),
                        len(baked_key_block_mesh_vertices),
                    )
                ):
                    evaluated_key_block_data[i].co = Vector(
                        baked_key_block_mesh_vertices[i].co
                    )

                baked_key_block_obj.to_mesh_clear()
            key_block.value = 0.0

        return evaluated_mesh_data
    finally:
        for mesh_data in [obj.data, evaluated_mesh_data]:
            if not isinstance(mesh_data, Mesh):
                continue

            shape_keys = mesh_data.shape_keys
            if not shape_keys:
                continue

            for shape_key_name, shape_key_value in key_block_name_to_value.items():
                key_block = shape_keys.key_blocks.get(shape_key_name)
                if key_block:
                    key_block.value = shape_key_value
        context.view_layer.update()

    return evaluated_mesh_data
