# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import secrets
import string
from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Optional, Union

import bmesh
from bpy.types import Armature, Context, Mesh, NodesModifier, Object

from ..common import shader
from ..common.convert import Json
from ..common.deep import make_json
from ..common.logger import get_logger
from ..editor.extension import get_armature_extension, get_material_extension
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

    @contextmanager
    def clear_blend_shape_proxy_previews(
        self, armature_data: Armature
    ) -> Iterator[None]:
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

        try:
            yield
        finally:
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
        finally:
            AbstractBaseVrmExporter.exit_hide_mtoon1_outline_geometry_nodes(
                context, object_name_to_modifier_names
            )

    @staticmethod
    def setup_mtoon_gltf_fallback_nodes(context: Context, *, is_vrm0: bool) -> None:
        """MToonのノードの値を、glTFのフォールバック値に使われるノードに反映する.

        MToonのノードを直接編集した場合、glTFのフォールバック値は自動で設定されない。
        そのためエクスポート時に明示的に値を設定する。
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
    context: Context, obj: Object, *, persistent: bool
) -> Optional[Mesh]:
    if obj.type not in MESH_CONVERTIBLE_OBJECT_TYPES:
        return None
    obj_data = obj.data
    if obj_data is None:
        return None

    # https://docs.blender.org/api/2.80/Depsgraph.html
    # TODO: シェイプキーが壊れることがあるらしい
    depsgraph = context.evaluated_depsgraph_get()
    evaluated_obj = obj.evaluated_get(depsgraph)
    evaluated_temporary_mesh = evaluated_obj.to_mesh(
        preserve_all_data_layers=True, depsgraph=depsgraph
    )
    if not evaluated_temporary_mesh:
        return None

    if not persistent:
        return evaluated_temporary_mesh.copy()

    # ドキュメントにはBlendDataMeshes.new_from_object()を使うべきと書いてあるが、
    # それだとシェイプキーが保持されない。
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
    return evaluated_mesh
