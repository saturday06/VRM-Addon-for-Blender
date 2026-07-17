# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
"""Public VRM 1.0 import/export extension hooks for third-party add-ons.

Third parties register callbacks here to read or write root glTF extensions such as
``VRMXT_*`` after the stock VRM 1.0 importer or exporter has built node index maps.

Hooks are process-global. They are not cleared when this add-on is disabled. Callers
must unregister their own callbacks from their ``unregister()``.

Import and export callbacks must not insert, remove, or reorder existing indexed glTF
entries in a way that invalidates built-in VRM references. Appending new indexed
entries on export is allowed when buffer views and ``byteLength`` stay consistent.
"""

from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, Protocol, TypeVar

from bpy.types import Context, Image, Material, Object

from .common.convert import Json

_K = TypeVar("_K")
_V = TypeVar("_V")


@dataclass(frozen=True)
class Vrm1ImportExtensionContext:
    """Read-only snapshot available after VRM 1.0 extension loading finishes."""

    context: Context
    armature: Object
    json_dict: Mapping[str, Json]
    node_index_to_object_name: Mapping[int, str]
    node_index_to_bone_name: Mapping[int, str]
    image_index_to_image: Mapping[int, Image]
    material_index_to_material: Mapping[int, Material]
    mesh_index_to_object: Mapping[int, Object]
    mesh_node_index_to_object_name: Mapping[int, str]


@dataclass(frozen=True)
class Vrm1ExportExtensionContext:
    """Mutable glTF document available after stock VRM 1.0 extensions are written."""

    context: Context
    armature: Object
    json_dict: dict[str, Json]
    buffer0: bytearray
    bone_name_to_node_index: Mapping[str, int]
    object_name_to_node_index: Mapping[str, int]
    image_name_to_index: MutableMapping[str, int]
    material_name_to_index: Mapping[str, int]
    mesh_object_name_to_node_index: Mapping[str, int]
    mesh_object_name_to_morph_target_names: Mapping[str, Sequence[str]]


class Vrm1ImportExtensionHook(Protocol):
    def __call__(self, context: Vrm1ImportExtensionContext) -> None: ...


class Vrm1ExportExtensionHook(Protocol):
    def __call__(self, context: Vrm1ExportExtensionContext) -> None: ...


@dataclass
class _State:
    import_hooks: Final[list[Vrm1ImportExtensionHook]] = field(
        default_factory=list[Vrm1ImportExtensionHook]
    )
    export_hooks: Final[list[Vrm1ExportExtensionHook]] = field(
        default_factory=list[Vrm1ExportExtensionHook]
    )


_state: Final = _State()


def register_vrm1_import_extension_hook(hook: Vrm1ImportExtensionHook) -> None:
    if hook not in _state.import_hooks:
        _state.import_hooks.append(hook)


def unregister_vrm1_import_extension_hook(hook: Vrm1ImportExtensionHook) -> None:
    try:
        _state.import_hooks.remove(hook)
    except ValueError:
        return


def register_vrm1_export_extension_hook(hook: Vrm1ExportExtensionHook) -> None:
    if hook not in _state.export_hooks:
        _state.export_hooks.append(hook)


def unregister_vrm1_export_extension_hook(hook: Vrm1ExportExtensionHook) -> None:
    try:
        _state.export_hooks.remove(hook)
    except ValueError:
        return


def clear_vrm1_extension_hooks() -> None:
    """Clear all registered hooks. Intended for tests."""
    _state.import_hooks.clear()
    _state.export_hooks.clear()


def _frozen_mapping(mapping: Mapping[_K, _V]) -> Mapping[_K, _V]:
    return MappingProxyType(dict(mapping))


def invoke_vrm1_import_extension_hooks(
    context: Vrm1ImportExtensionContext,
) -> None:
    for hook in tuple(_state.import_hooks):
        hook(context)


def invoke_vrm1_export_extension_hooks(
    context: Vrm1ExportExtensionContext,
) -> None:
    for hook in tuple(_state.export_hooks):
        hook(context)


def create_vrm1_import_extension_context(
    *,
    context: Context,
    armature: Object,
    json_dict: Mapping[str, Json],
    node_index_to_object_name: Mapping[int, str],
    node_index_to_bone_name: Mapping[int, str],
    image_index_to_image: Mapping[int, Image],
    material_index_to_material: Mapping[int, Material],
    mesh_index_to_object: Mapping[int, Object],
    mesh_node_index_to_object_name: Mapping[int, str],
) -> Vrm1ImportExtensionContext:
    return Vrm1ImportExtensionContext(
        context=context,
        armature=armature,
        json_dict=_frozen_mapping(json_dict),
        node_index_to_object_name=_frozen_mapping(node_index_to_object_name),
        node_index_to_bone_name=_frozen_mapping(node_index_to_bone_name),
        image_index_to_image=_frozen_mapping(image_index_to_image),
        material_index_to_material=_frozen_mapping(material_index_to_material),
        mesh_index_to_object=_frozen_mapping(mesh_index_to_object),
        mesh_node_index_to_object_name=_frozen_mapping(mesh_node_index_to_object_name),
    )
