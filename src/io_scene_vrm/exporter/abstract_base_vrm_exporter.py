# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import secrets
import string
from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import Optional, Union

import bmesh
from bpy.types import Armature, Context, Mesh, NodesModifier, Object
from mathutils import Vector

from ..common import shader
from ..common.convert import Json
from ..common.deep import make_json
from ..common.logger import get_logger
from ..editor.extension import get_armature_extension, get_material_extension
from ..editor.property_group import BonePropertyGroup, BonePropertyGroupType
from ..editor.search import MESH_CONVERTIBLE_OBJECT_TYPES
from ..external import io_scene_gltf2_support

logger = get_logger(__name__)


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
    def export_vrm(self) -> Optional[bytes]:
        pass

    @staticmethod
    def enter_clear_blend_shape_proxy_previews(
        armature_data: Armature,
    ) -> tuple[Sequence[float], Mapping[str, float]]:
        ext = get_armature_extension(armature_data)

        saved_vrm0_previews: list[float] = []
        for blend_shape_group in ext.vrm0.blend_shape_master.blend_shape_groups:
            saved_vrm0_previews.append(blend_shape_group.preview)
            blend_shape_group.preview = 0

        saved_vrm1_previews: dict[str, float] = {}
        for (
            name,
            expression,
        ) in ext.vrm1.expressions.all_name_to_expression_dict().items():
            saved_vrm1_previews[name] = expression.preview
            expression.preview = 0

        return saved_vrm0_previews, saved_vrm1_previews

    @staticmethod
    def leave_clear_blend_shape_proxy_previews(
        armature_data: Armature,
        saved_vrm0_previews: Sequence[float],
        saved_vrm1_previews: Mapping[str, float],
    ) -> None:
        ext = get_armature_extension(armature_data)

        for blend_shape_group, blend_shape_preview in zip(
            ext.vrm0.blend_shape_master.blend_shape_groups, saved_vrm0_previews
        ):
            blend_shape_group.preview = blend_shape_preview

        for (
            name,
            expression,
        ) in ext.vrm1.expressions.all_name_to_expression_dict().items():
            expression_preview = saved_vrm1_previews.get(name)
            if expression_preview is not None:
                expression.preview = expression_preview

    @contextmanager
    def clear_blend_shape_proxy_previews(
        self, armature_data: Armature
    ) -> Iterator[None]:
        saved_vrm0_previews, saved_vrm1_previews = (
            self.enter_clear_blend_shape_proxy_previews(armature_data)
        )
        try:
            yield
            # After yield, native bpy objects may be deleted or frames may advance,
            # becoming invalid. Accessing them in this state causes crashes, so
            # be careful not to access potentially invalid native objects after yield
        finally:
            self.leave_clear_blend_shape_proxy_previews(
                armature_data, saved_vrm0_previews, saved_vrm1_previews
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
        for modified_non_deform_bone_name in modified_non_deform_bone_names:
            bone = armature_data.bones.get(modified_non_deform_bone_name)
            if bone and bone.use_deform:
                bone.use_deform = False

    @contextmanager
    def enable_deform_for_all_referenced_bones(
        self, armature_data: Armature
    ) -> Iterator[None]:
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
        for object_name, modifiers in object_name_to_modifiers.items():
            for modifier_name, render, viewport in modifiers:
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
    def hide_mtoon1_outline_geometry_nodes(context: Context) -> Iterator[None]:
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


def force_apply_modifiers(
    context: Context, obj: Object, *, preserve_shape_keys: bool
) -> Optional[Mesh]:
    if obj.type not in MESH_CONVERTIBLE_OBJECT_TYPES:
        return None
    obj_data = obj.data
    if obj_data is None:
        return None

    if isinstance(obj_data, Mesh):
        obj_data.calc_loop_triangles()

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
        logger.error(
            "Unexpected object type: %s name=%s",
            type(obj_data),
            obj_data.name,
        )
        evaluated_mesh = context.blend_data.meshes.new(name=obj_data.name)

    bm = bmesh.new()
    try:
        bm.from_mesh(evaluated_temporary_mesh)
        bm.to_mesh(evaluated_mesh)
    finally:
        bm.free()

    evaluated_obj.to_mesh_clear()

    if not preserve_shape_keys:
        return evaluated_mesh

    if not isinstance(obj_data, Mesh):
        return evaluated_mesh

    shape_keys = obj_data.shape_keys
    if not shape_keys:
        return evaluated_mesh

    evaluated_mesh_shape_keys = evaluated_mesh.shape_keys
    if not evaluated_mesh_shape_keys:
        return evaluated_mesh

    # If the mesh has shape keys, reproduce them as much as possible
    for shape_key in shape_keys.key_blocks:
        evaluated_mesh_shape_key = evaluated_mesh_shape_keys.key_blocks.get(
            shape_key.name
        )
        if not evaluated_mesh_shape_key:
            continue

        if shape_key.name == shape_keys.reference_key.name:
            continue

        shape_key.value = 1.0
        context.view_layer.update()

        depsgraph = context.evaluated_depsgraph_get()
        baked_shape_key_obj = obj.evaluated_get(depsgraph)
        baked_shape_key_mesh = baked_shape_key_obj.to_mesh(
            preserve_all_data_layers=True, depsgraph=depsgraph
        )
        if baked_shape_key_mesh:
            evaluated_mesh_shape_key_data = evaluated_mesh_shape_key.data
            baked_shape_key_mesh_vertices = baked_shape_key_mesh.vertices

            # TODO: If the number of vertices is different, we should use advanced graph
            # matching algorithm.
            for i in range(
                min(
                    len(evaluated_mesh_shape_key_data),
                    len(baked_shape_key_mesh_vertices),
                )
            ):
                evaluated_mesh_shape_key_data[i].co = Vector(
                    baked_shape_key_mesh_vertices[i].co
                )

        shape_key.value = 0.0
        baked_shape_key_obj.to_mesh_clear()

    context.view_layer.update()
    return evaluated_mesh
