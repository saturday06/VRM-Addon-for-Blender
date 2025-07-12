# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import contextlib
from collections.abc import (
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    MutableSequence,
    Sequence,
    ValuesView,
)
from typing import Callable, Generic, TypeVar, overload

from mathutils import Color, Euler, Matrix, Quaternion, Vector
from typing_extensions import TypeAlias

class bpy_struct:
    def as_pointer(self) -> int: ...
    id_data: ID | None
    def path_from_id(self, property: str = "") -> str: ...
    def keyframe_insert(
        self,
        data_path: str,
        index: int = -1,
        frame: float = ...,
        group: str = "",
        options: set[str] = ...,
    ) -> bool: ...
    def driver_add(self, path: str, index: int = -1) -> FCurve | list[FCurve]: ...
    def driver_remove(self, path: str, index: int = -1) -> bool: ...

    bl_rna: BlenderRNA  # Does not exist in documentation. TODO: read only

__BpyPropCollectionElement = TypeVar("__BpyPropCollectionElement")

class bpy_prop_collection(Generic[__BpyPropCollectionElement]):
    def get(
        self,
        key: str,
        default: __BpyPropCollectionElement | None = None,
    ) -> __BpyPropCollectionElement | None: ...
    def __contains__(self, key: str) -> bool: ...
    def __iter__(self) -> Iterator[__BpyPropCollectionElement]: ...
    @overload
    def __getitem__(self, key: int | str) -> __BpyPropCollectionElement: ...
    @overload
    def __getitem__(
        self, index: slice[int | None, int | None, int | None]
    ) -> tuple[__BpyPropCollectionElement, ...]: ...
    def __len__(self) -> int: ...
    def keys(self) -> KeysView[str]: ...
    def values(self) -> ValuesView[__BpyPropCollectionElement]: ...
    def items(self) -> ItemsView[str, __BpyPropCollectionElement]: ...

# Does not exist in documentation
__BpyPropArrayElement = TypeVar("__BpyPropArrayElement")

class bpy_prop_array(Generic[__BpyPropArrayElement]):
    def __iter__(self) -> Iterator[__BpyPropArrayElement]: ...
    @overload
    def __getitem__(self, index: int) -> __BpyPropArrayElement: ...
    @overload
    def __getitem__(
        self, index: slice[int | None, int | None, int | None]
    ) -> tuple[__BpyPropArrayElement, ...]: ...
    def __setitem__(self, index: int, value: __BpyPropArrayElement) -> None: ...

# Custom property compatible classes. In 2.93, only ID, Bone, PoseBone
# https://docs.blender.org/api/2.93/bpy.types.bpy_struct.html#bpy.types.bpy_struct.values
class __CustomProperty:
    def __getitem__(self, key: str) -> object: ...
    def __setitem__(self, key: str, value: object) -> None: ...
    def __delitem__(self, key: str) -> None: ...
    def __contains__(self, key: str) -> bool: ...
    def get(self, key: str, default: object = None) -> object: ...
    def keys(self) -> KeysView[str]: ...
    def items(self) -> ItemsView[str, object]: ...
    def pop(self, key: str, default: object = None) -> object: ...

class ID(bpy_struct, __CustomProperty):
    name: str
    is_evaluated: bool
    users: int
    use_fake_user: bool
    use_extra_user: bool  # bpy.app.version >= (3, 2)

    def animation_data_create(self) -> AnimData | None: ...
    def animation_data_clear(self) -> None: ...
    def user_remap(self, new_id: ID) -> None: ...
    def update_tag(self, refresh: set[str] = ...) -> None: ...
    def copy(self) -> ID: ...

class Property(bpy_struct):
    @property
    def name(self) -> str: ...
    @property
    def identifier(self) -> str: ...

class PointerProperty(Property):
    @property
    def fixed_type(
        self,
    ) -> type[bpy_struct]: ...  # TODO: Need to investigate the correct definition

class FloatProperty(Property):
    @property
    def is_array(self) -> bool: ...

class IntProperty(Property):
    @property
    def is_array(self) -> bool: ...

class BoolProperty(Property):
    @property
    def is_array(self) -> bool: ...

class EnumPropertyItem(bpy_struct):
    @property
    def identifier(self) -> str: ...

class EnumProperty(Property):
    @property
    def enum_items(self) -> bpy_prop_collection[EnumPropertyItem]: ...

class StringProperty(Property): ...

class CollectionProperty(Property):
    def fixed_type(
        self,
    ) -> type: ...  # TODO: Need to investigate the correct implementation
    def add(self) -> Property: ...  # TODO: undocumented
    def __len__(self) -> int: ...  # TODO: undocumented
    def __iter__(self) -> Iterator[Property]: ...  # TODO: undocumented
    def clear(self) -> None: ...  # TODO: undocumented
    @overload
    def __getitem__(self, index: int) -> Property: ...  # TODO: undocumented
    @overload
    def __getitem__(
        self,
        index: slice[int | None, int | None, int | None],
    ) -> tuple[Property, ...]: ...  # TODO: undocumented
    def remove(self, index: int) -> None: ...  # TODO: undocumented
    def values(self) -> ValuesView[Property]: ...  # TODO: undocumented
    def move(self, from_index: int, to_index: int) -> None: ...  # TODO: undocumented

class PropertyGroup(bpy_struct):
    name: str

    # TODO: Actually a method of bpy_struct
    def get(self, key: str, default: object = None) -> object: ...
    # TODO: Actually a method of bpy_struct
    def __setitem__(self, key: str, value: object) -> None: ...
    # TODO: Actually a method of bpy_struct
    def __delitem__(self, key: str) -> None: ...
    # TODO: Probably actually a method of bpy_struct
    def __contains__(self, key: str) -> bool: ...
    # TODO: Probably actually a method of bpy_struct
    def pop(self, key: str, default: object = None) -> object: ...

class BlenderRNA(bpy_struct):
    @property
    def properties(
        self,
    ) -> bpy_prop_collection[
        Property  # TODO: verify if this matches bpy.types.Property
    ]: ...  # Does not exist in documentation.

class Gizmo(bpy_struct):
    alpha: float
    alpha_highlight: float
    color: tuple[float, float, float]
    color_highlight: tuple[float, float, float]
    matrix_basis: Matrix  # TODO: Type is Matrix?
    scale_basis: float

    def target_set_prop(
        self,
        target: str,
        data: AnyType,
        property: str,
        index: int = -1,
    ) -> None: ...

    # GIZMO_GT_move_3d
    draw_style: str
    draw_options: set[str]

class Gizmos(bpy_prop_collection[Gizmo]):
    def new(self, type: str) -> Gizmo: ...

class GizmoGroup(bpy_struct):
    @property
    def gizmos(self) -> Gizmos: ...

class ColorManagedInputColorspaceSettings(bpy_struct):
    name: str

class Event(bpy_struct):
    @property
    def type(self) -> str: ...
    @property
    def value(self) -> str: ...
    @property
    def mouse_x(self) -> int: ...
    @property
    def mouse_y(self) -> int: ...

class ImageUser(bpy_struct): ...

class PackedFile(bpy_struct):
    @property
    def data(self) -> bytes: ...  # Documentation says str, but actually bytes
    @property
    def size(self) -> int: ...

class Image(ID):
    colorspace_settings: ColorManagedInputColorspaceSettings
    size: bpy_prop_array[float]
    alpha_mode: str
    generated_color: tuple[float, float, float, float]  # Might be Vector
    depth: int
    file_format: str
    filepath: str
    filepath_raw: str
    generated_height: int
    generated_width: int
    is_dirty: bool
    bindcode: int
    source: str
    @property
    def packed_file(self) -> PackedFile | None: ...  # Seems Optional
    def filepath_from_user(self, image_user: ImageUser | None = None) -> str: ...
    def update(self) -> None: ...
    def gl_load(self, frame: int = 0) -> None: ...
    def unpack(self, method: str = "USE_LOCAL") -> None: ...
    def pack(self, data: str = "", data_len: int = 0) -> None: ...
    def reload(self) -> None: ...

class TimelineMarker(bpy_struct):
    name: str
    frame: int

class ActionPoseMarkers(bpy_prop_collection[TimelineMarker]): ...

class FCurve(bpy_struct):
    array_index: int
    auto_smoothing: str
    # color: tuple[float, float, float]  # TODO: Might be Vector
    color_mode: str
    data_path: str
    @property
    def driver(self) -> Driver | None: ...  # TODO: Is it really Optional?
    extrapolation: str
    is_valid: bool
    mute: bool

    def evaluate(self, frame: int) -> float: ...

class ActionFCurves(bpy_prop_collection[FCurve]): ...

class ActionChannelbagFCurves(bpy_prop_collection[FCurve]):
    def new(self, data_path: str, *, index: int = 0) -> FCurve: ...
    def find(self, data_path: str, *, index: int = 0) -> FCurve: ...
    def remove(self, fcurve: FCurve) -> None: ...
    def clear(self) -> None: ...

class ActionSlot(bpy_struct): ...
class ActionSlots(bpy_prop_collection[ActionSlot]): ...

class ActionChannelbag(bpy_struct):
    @property
    def fcurves(self) -> ActionChannelbagFCurves: ...

class ActionChannelbags(bpy_prop_collection[ActionChannelbag]): ...

class ActionStrip(bpy_struct):
    @property
    def type(self) -> str: ...

class ActionKeyframeStrip(ActionStrip):
    def channelbag(
        self, slot: ActionSlot, *, ensure: bool = False
    ) -> ActionChannelbag: ...

class ActionStrips(bpy_prop_collection[ActionStrip]): ...

class ActionLayer(bpy_struct):
    name: str
    @property
    def strips(self) -> ActionStrips: ...

class ActionLayers(bpy_prop_collection[ActionLayer]): ...

class Action(ID):
    @property
    def fcurves(self) -> ActionFCurves: ...
    @property
    def frame_range(self) -> Vector: ...
    @property
    def pose_markers(self) -> ActionPoseMarkers: ...
    @property
    def layers(self) -> ActionLayers: ...
    @property
    def slots(self) -> ActionSlots: ...

class Texture(ID): ...

class LayerObjects(bpy_prop_collection["Object"]):
    active: Object | None

class Space(bpy_struct):
    @property
    def type(self) -> str: ...

class View3DShading(bpy_struct):
    type: str

class SpaceView3D(Space):
    @property
    def shading(self) -> View3DShading: ...
    @staticmethod  # TODO: Verify if it's really static
    def draw_handler_add(
        callback: Callable[[], None],
        args: tuple[object, ...],
        region_type: str,
        draw_type: str,
    ) -> object: ...
    @staticmethod  # TODO: Verify if it's really static
    def draw_handler_remove(
        handler: object,
        region_type: str,
    ) -> None: ...

class Depsgraph(bpy_struct):
    def update(self) -> None: ...

class DriverTarget(bpy_struct):
    bone_target: str
    data_path: str
    id: ID
    id_type: str
    rotation_mode: str
    transform_space: str
    transform_type: str
    context_property: str  # bpy.app.version >= (3, 6)

class DriverVariable(bpy_struct):
    @property
    def is_name_valid(self) -> bool: ...
    name: str
    @property
    def targets(self) -> bpy_prop_collection[DriverTarget]: ...
    type: str

class ChannelDriverVariables(bpy_prop_collection[DriverVariable]):
    # TODO: Documentation states that it inherits from bpy_struct
    def new(self) -> DriverVariable: ...
    def remove(self, variable: DriverVariable) -> None: ...

class Driver(bpy_struct):
    expression: str
    @property
    def is_simple_expression(self) -> bool: ...
    @property
    def is_valid(
        self,
    ) -> bool: ...  # TODO: This seems readonly but the documentation says otherwise
    type: str
    use_self: bool
    @property
    def variables(self) -> ChannelDriverVariables: ...

class LayerCollection(bpy_struct):
    @property
    def collection(self) -> Collection: ...

class ViewLayer(bpy_struct):
    active_layer_collection: LayerCollection
    @property
    def objects(self) -> LayerObjects: ...
    @property
    def depsgraph(self) -> Depsgraph: ...
    def update(self) -> None: ...

class Bone(bpy_struct, __CustomProperty):
    name: str
    parent: Bone | None
    use_inherit_rotation: bool
    select: bool
    tail_radius: float

    @property
    def head(self) -> Vector: ...  # TODO: Is the type correct?
    @head.setter
    def head(self, value: Sequence[float]) -> None: ...  # TODO: Is the type correct?
    @property
    def tail(self) -> Vector: ...  # TODO: Is the type correct?
    @tail.setter
    def tail(self, value: Sequence[float]) -> None: ...  # TODO: Is the type correct?

    head_local: Vector  # TODO: Is the type correct?
    head_radius: float

    # Documentation says 3-element float array, but actually Vector
    tail_local: Vector

    def use_connect(self) -> bool: ...

    use_deform: bool

    # Documentation says 2D float array, but actually Matrix
    matrix_local: Matrix

    @property
    def length(self) -> float: ...
    @property
    def children(self) -> bpy_prop_collection[Bone]: ...
    def translate(self, vec: Vector) -> None: ...
    def convert_local_to_pose(
        self,
        matrix: Iterable[Iterable[float]],
        matrix_local: Iterable[Iterable[float]],
        parent_matrix: Iterable[Iterable[float]] = ...,
        parent_matrix_local: Iterable[Iterable[float]] = ...,
        invert: bool = False,
    ) -> Matrix: ...

class EditBone(bpy_struct):
    name: str
    @property
    def head(
        self,
    ) -> Vector: ...  # Documentation says 3-element float array, but actually Vector
    @head.setter
    def head(self, value: Iterable[float]) -> None: ...
    @property
    def tail(
        self,
    ) -> Vector: ...  # Documentation says 3-element float array, but actually Vector
    @tail.setter
    def tail(self, value: Iterable[float]) -> None: ...
    @property
    def vector(self) -> Vector: ...

    parent: EditBone | None
    length: float
    roll: float
    use_local_location: bool
    use_connect: bool
    use_deform: bool
    head_radius: float
    tail_radius: float
    envelope_distance: float
    matrix: Matrix

    @property
    def children(self) -> Sequence[EditBone]: ...
    def transform(
        self,
        matrix: Matrix,
        *,
        scale: bool = True,
        roll: bool = True,
    ) -> None: ...

class PoseBoneConstraints(bpy_prop_collection["Constraint"]):
    def new(self, type: str) -> Constraint: ...

class PoseBone(bpy_struct, __CustomProperty):
    name: str
    bbone_curveinx: float
    bbone_curveinz: float
    bbone_curveoutx: float
    bbone_curveoutz: float
    custom_shape: Object | None

    @property
    def parent(self) -> PoseBone | None: ...
    @property
    def constraints(self) -> PoseBoneConstraints: ...
    @property
    def head(
        self,
    ) -> Vector: ...  # Documentation says 3-element float array, but actually Vector
    rotation_axis_angle: Sequence[float]
    rotation_euler: Euler
    rotation_mode: str
    rotation_quaternion: Quaternion
    @property
    def bone(self) -> Bone: ...
    matrix: Matrix  # This also differs from documentation, it's Matrix
    matrix_basis: Matrix  # This also differs from documentation, it's Matrix
    @property
    def children(self) -> Sequence[PoseBone]: ...
    @property
    def location(self) -> Vector: ...  # TODO: Confirm if it's really Vector
    @location.setter
    def location(self, value: Iterable[float]) -> None: ...
    @property
    def scale(self) -> Vector: ...  # TODO: Confirm if it's really Vector
    @scale.setter
    def scale(self, value: Iterable[float]) -> None: ...

class ArmatureBones(bpy_prop_collection[Bone]):
    active: Bone | None  # TODO: Can it be None?

class OperatorProperties(bpy_struct): ...

class UILayout(bpy_struct):
    def box(self) -> UILayout: ...
    def column(
        self,
        /,
        *,
        align: bool = False,
        heading: str = "",
        heading_ctxt: str = "",
        translate: bool = True,
    ) -> UILayout: ...
    def row(
        self,
        /,
        *,
        align: bool = False,
        heading: str = "",
        heading_ctxt: str = "",
        translate: bool = True,
    ) -> UILayout: ...
    def prop(
        self,
        data: bpy_struct,  # TODO: AnyType
        property: str,
        /,
        *,
        text: str = "",
        text_ctxt: str = "",
        translate: bool = True,
        icon: str = "NONE",
        placeholder: str = "",  # bpy.app.version >= (4, 1)
        expand: bool = False,
        slider: bool = False,
        toggle: int = -1,
        icon_only: bool = False,
        event: bool = False,
        full_event: bool = False,
        emboss: bool = True,
        index: int = -1,
        icon_value: int = 0,
        invert_checkbox: bool = False,
    ) -> UILayout: ...
    def label(
        self,
        /,
        *,
        text: str = "",
        text_ctxt: str = "",
        translate: bool = True,
        icon: str = "NONE",
        icon_value: int = 0,
    ) -> None: ...
    def split(
        self,
        /,
        *,
        factor: float = 0.0,
        align: bool = False,
    ) -> UILayout: ...
    def operator(
        self,
        operator: str,
        /,
        *,
        text: str = "",
        text_ctxt: str = "",
        translate: bool = True,
        icon: str = "NONE",
        emboss: bool = True,
        depress: bool = False,
        icon_value: int = 0,
    ) -> OperatorProperties: ...
    def separator(
        self,
        /,
        *,
        factor: float = 1.0,
    ) -> None: ...
    def prop_search(
        self,
        data: AnyType,
        property: str,
        search_data: AnyType,
        search_property: str,
        /,
        *,
        text: str = "",
        text_ctxt: str = "",
        translate: bool = True,
        icon: str = "NONE",
        results_are_suggestions: bool = False,
    ) -> UILayout: ...
    def template_ID_preview(
        self,
        data: AnyType,
        property: str,
        new: str = "",
        open: str = "",
        unlink: str = "",
        rows: int = 0,
        cols: int = 0,
        filter: str = "ALL",
        hide_buttons: bool = False,
    ) -> None: ...
    def template_list(
        self,
        listtype_name: str,
        list_id: str,
        dataptr: AnyType,
        propname: str,
        active_dataptr: AnyType,
        active_propname: str,
        item_dyntip_propname: str = "",
        rows: int = 5,
        maxrows: int = 5,
        type: str = "DEFAULT",
        columns: int = 9,
        sort_reverse: bool = False,
        sort_lock: bool = False,
    ) -> None: ...

    alignment: str
    scale_x: float
    emboss: str
    enabled: bool
    alert: bool

class AddonPreferences(bpy_struct):
    layout: UILayout  # TODO: No documentation

class Addon(bpy_struct):
    module: str
    @property
    def preferences(self) -> AddonPreferences: ...

class Addons(bpy_prop_collection[Addon]): ...

class MeshUVLoop(bpy_struct):
    uv: Vector  # TODO: Check the correct type

class MeshUVLoopLayer(bpy_struct):
    name: str
    data: bpy_prop_collection[MeshUVLoop]
    active_render: bool

class UVLoopLayers(bpy_prop_collection[MeshUVLoopLayer]):
    active: MeshUVLoopLayer | None
    def new(self, name: str = "UVMap", do_init: bool = True) -> MeshUVLoopLayer: ...

class MeshLoopTriangle(bpy_struct):
    vertices: tuple[int, int, int]
    material_index: int
    split_normals: tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]  # TODO: Check the correct type
    loops: tuple[int, int, int]  # TODO: Check the correct type

class MeshLoop(bpy_struct):
    edge_index: int
    index: int
    normal: Vector
    tangent: Vector  # TODO: Check the correct type
    vertex_index: int

class MeshLoops(bpy_prop_collection[MeshLoop]): ...
class MeshLoopTriangles(bpy_prop_collection[MeshLoopTriangle]): ...

class VertexGroupElement(bpy_struct):
    weight: float
    @property
    def group(self) -> int: ...

class MeshVertex(bpy_struct):
    co: tuple[float, float, float]  # Maybe Vector?
    normal: Vector  # TODO: Check the correct type
    @property
    def groups(self) -> bpy_prop_collection[VertexGroupElement]: ...
    @property
    def index(self) -> int: ...

class MeshVertices(bpy_prop_collection[MeshVertex]): ...
class UnknownType(bpy_struct): ...

class ShapeKeyPoint(bpy_struct):
    co: Vector

class ShapeKey(bpy_struct):
    name: str
    value: float
    @property  # TODO: It's becoming UnknownType
    def data(self) -> bpy_prop_collection[ShapeKeyPoint]: ...
    def normals_split_get(self) -> Sequence[float]: ...  # TODO: Correct type

class Key(ID):
    @property
    def key_blocks(self) -> bpy_prop_collection[ShapeKey]: ...
    @property
    def reference_key(self) -> ShapeKey: ...

class MeshPolygon(bpy_struct):
    material_index: int
    use_smooth: bool
    vertices: tuple[int, int, int]  # TODO: Check the correct type
    loop_indices: Sequence[int]  # TODO: Check the correct type
    @property
    def loop_total(self) -> int: ...

class MeshPolygons(bpy_prop_collection[MeshPolygon]): ...

class MeshLoopColor(bpy_struct):
    color: Sequence[float]  # TODO: Check the correct type

class MeshLoopColorLayer(bpy_struct):
    @property
    def data(self) -> bpy_prop_collection[MeshLoopColor]: ...

class LoopColors(bpy_prop_collection[MeshLoopColorLayer]):
    def new(self, name: str = "Col", do_init: bool = True) -> MeshLoopColorLayer: ...

class Mesh(ID):
    use_auto_smooth: bool

    @property
    def materials(self) -> IDMaterials: ...
    @property
    def uv_layers(self) -> UVLoopLayers: ...
    @property
    def loops(self) -> MeshLoops: ...
    @property
    def loop_triangles(self) -> MeshLoopTriangles: ...
    @property
    def vertices(self) -> MeshVertices: ...
    @property
    def shape_keys(self) -> Key | None: ...  # Optional
    @property
    def polygons(self) -> MeshPolygons: ...
    @property
    def vertex_colors(self) -> LoopColors: ...

    has_custom_normals: bool
    def calc_tangents(self, uvmap: str = "") -> None: ...
    def calc_loop_triangles(self) -> None: ...
    def copy(self) -> Mesh: ...  # ID.copy()
    def transform(self, matrix: Matrix, shape_keys: bool = False) -> None: ...
    def calc_normals_split(self) -> None: ...
    def update(
        self,
        calc_edges: bool = False,
        calc_edges_loose: bool = False,
    ) -> None: ...
    def from_pydata(
        self,
        vertices: Iterable[Iterable[float]],
        edges: Iterable[Iterable[float]],
        faces: Iterable[Iterable[float]],
    ) -> None: ...
    def create_normals_split(self) -> None: ...
    def normals_split_custom_set_from_vertices(
        self,
        normals: Iterable[Iterable[float]],
    ) -> None: ...
    def validate(
        self,
        verbose: bool = False,
        clean_customdata: bool = True,
    ) -> bool: ...

class AnimDataDrivers(bpy_prop_collection[FCurve]):  # TODO: Type is unclear
    ...
class NlaTrack(bpy_struct): ...
class NlaTracks(bpy_prop_collection[NlaTrack]):  # TODO: Type is unclear
    ...

class AnimData(bpy_struct):
    action: Action | None
    action_blend_type: str
    action_extrapolation: str
    action_influence: float
    @property
    def drivers(self) -> AnimDataDrivers: ...
    @property
    def nla_tracks(self) -> NlaTracks: ...
    use_nla: bool
    use_pin: bool
    use_tweak_mode: bool
    def nla_tweak_strip_time_to_scene(
        self, frame: float, invert: bool = False
    ) -> float: ...

class ArmatureEditBones(bpy_prop_collection[EditBone]):
    def new(self, name: str) -> EditBone: ...
    def remove(self, bone: EditBone) -> None: ...

class Armature(ID):
    pose_position: str

    @property
    def animation_data(
        self,
    ) -> AnimData | None: ...  # TODO: Confirm if it's really Optional
    @property
    def bones(self) -> ArmatureBones: ...
    @property
    def edit_bones(self) -> ArmatureEditBones: ...

class TextLine(bpy_struct):
    body: str

class Text(ID):
    @property
    def lines(self) -> bpy_prop_collection[TextLine]: ...
    def write(self, text: str) -> None: ...

class NodeSocketInterface(bpy_struct):
    bl_socket_idname: str
    description: str
    hide_value: bool
    @property
    def identifier(self) -> str: ...
    @property
    def is_output(self) -> bool: ...
    name: str

    # bpy.app.version >= (3, 0, 0)
    attribute_domain: str
    bl_label: str

class NodeSocketInterfaceStandard(NodeSocketInterface):
    @property
    def type(self) -> str: ...

class NodeSocketInterfaceFloat(NodeSocketInterfaceStandard):
    default_value: float
    max_value: float
    min_value: float

class NodeSocketInterfaceFloatAngle(NodeSocketInterfaceStandard):
    default_value: float
    max_value: float
    min_value: float

class NodeSocketInterfaceFloatDistance(NodeSocketInterfaceStandard):
    default_value: float
    max_value: float
    min_value: float

class NodeSocketInterfaceFloatFactor(NodeSocketInterfaceStandard):
    default_value: float
    max_value: float
    min_value: float

class NodeSocketInterfaceFloatPercentage(NodeSocketInterfaceStandard):
    default_value: float
    max_value: float
    min_value: float

class NodeSocketInterfaceFloatTime(NodeSocketInterfaceStandard):
    default_value: float
    max_value: float
    min_value: float

class NodeSocketInterfaceFloatUnsigned(NodeSocketInterfaceStandard):
    default_value: float
    max_value: float
    min_value: float

class NodeSocketInterfaceColor(NodeSocketInterfaceStandard):
    default_value: tuple[float, float, float, float]  # TODO: Is this a color?

class NodeSocketInterfaceVector(NodeSocketInterfaceStandard):
    default_value: tuple[float, float, float]
    max_value: float
    min_value: float

class NodeSocketInterfaceVectorAcceleration(NodeSocketInterfaceStandard):
    default_value: tuple[float, float, float]
    max_value: float
    min_value: float

class NodeSocketInterfaceVectorDirection(NodeSocketInterfaceStandard):
    default_value: tuple[float, float, float]
    max_value: float
    min_value: float

class NodeSocketInterfaceVectorEuler(NodeSocketInterfaceStandard):
    default_value: tuple[float, float, float]
    max_value: float
    min_value: float

class NodeSocketInterfaceVectorTranslation(NodeSocketInterfaceStandard):
    default_value: tuple[float, float, float]
    max_value: float
    min_value: float

class NodeSocketInterfaceVectorVelocity(NodeSocketInterfaceStandard):
    default_value: tuple[float, float, float]
    max_value: float
    min_value: float

class NodeSocketInterfaceVectorXYZ(NodeSocketInterfaceStandard):
    default_value: tuple[float, float, float]
    max_value: float
    min_value: float

class NodeSocket(bpy_struct):
    display_shape: str
    enabled: bool
    hide: bool
    hide_value: bool
    link_limit: int
    name: str
    show_expanded: bool
    type: str
    @property
    def links(self) -> list[NodeLink]: ...
    @property
    def node(self) -> Node: ...
    @property
    def is_linked(self) -> bool: ...

class NodeSocketStandard(NodeSocket): ...

class NodeSocketBool(NodeSocketStandard):
    default_value: bool

class NodeSocketFloat(NodeSocketStandard):
    default_value: float

class NodeSocketFloatAngle(NodeSocketStandard):
    default_value: float

class NodeSocketFloatDistance(NodeSocketStandard):
    default_value: float

class NodeSocketFloatFactor(NodeSocketStandard):
    default_value: float

class NodeSocketFloatPercentage(NodeSocketStandard):
    default_value: float

class NodeSocketFloatTime(NodeSocketStandard):
    default_value: float

class NodeSocketFloatUnsigned(NodeSocketStandard):
    default_value: float

class NodeSocketInt(NodeSocketStandard):
    default_value: int

class NodeSocketIntFactor(NodeSocketStandard):
    default_value: int

class NodeSocketIntPercentage(NodeSocketStandard):
    default_value: int

class NodeSocketIntUnsigned(NodeSocketStandard):
    default_value: int

class NodeSocketString(NodeSocketStandard):
    default_value: str

class NodeSocketVector(NodeSocketStandard):
    default_value: tuple[float, float, float]  # TODO: Vector?

class NodeSocketVectorAcceleration(NodeSocketStandard):
    default_value: tuple[float, float, float]  # TODO: Vector?

class NodeSocketVectorDirection(NodeSocketStandard):
    default_value: tuple[float, float, float]  # TODO: Vector?

class NodeSocketVectorEuler(NodeSocketStandard):
    default_value: tuple[float, float, float]  # TODO: Vector?

class NodeSocketVectorTranslation(NodeSocketStandard):
    default_value: tuple[float, float, float]  # TODO: Vector?

class NodeSocketVectorVelocity(NodeSocketStandard):
    default_value: tuple[float, float, float]  # TODO: Vector?

class NodeSocketVectorXYZ(NodeSocketStandard):
    default_value: tuple[float, float, float]  # TODO: Vector?

class NodeSocketColor(NodeSocketStandard):
    default_value: tuple[float, float, float, float]  # TODO: Color?

class NodeOutputs(bpy_prop_collection[NodeSocket]): ...
class NodeInputs(bpy_prop_collection[NodeSocket]): ...

class Node(bpy_struct):
    bl_idname: str
    outputs: NodeOutputs
    inputs: NodeInputs
    color: tuple[float, float, float]  # TODO: Color?
    height: float
    hide: bool
    label: str
    location: tuple[float, float]
    mute: bool
    name: str
    parent: Node | None
    select: bool
    show_options: bool
    show_preview: bool
    show_texture: bool
    use_custom_color: bool
    width: float
    type: str

    # bpy.app.version < (4, 0):
    width_hidden: bool

class NodeInternal(Node): ...
class NodeReroute(NodeInternal): ...

class NodeFrame(NodeInternal):
    shrink: bool
    label_size: int
    text: Text

class NodeGroup(NodeInternal): ...

class NodeGroupOutput(NodeInternal):
    is_active_output: bool

class ColorRamp(bpy_struct):
    color_mode: str
    elements: object  # TODO: object

class ColorMapping(bpy_struct):
    blend_color: tuple[float, float, float]  # TODO: Color?
    blend_factor: float
    blend_type: str
    brightness: float
    color_ramp: ColorRamp
    contrast: float
    saturation: float
    use_color_ramp: bool

class TexMapping(bpy_struct):
    @property
    def translation(self) -> Vector: ...
    @translation.setter
    def translation(self, value: Iterable[float]) -> None: ...
    @property
    def scale(self) -> Vector: ...
    @scale.setter
    def scale(self, value: Iterable[float]) -> None: ...

    mapping: str
    mapping_x: str
    mapping_y: str
    mapping_z: str

class ShaderNode(NodeInternal): ...  # x
class ShaderNodeAddShader(ShaderNode): ...  # x

class ShaderNodeAmbientOcclusion(ShaderNode):
    inside: bool
    only_local: bool
    samples: int

class ShaderNodeAttribute(ShaderNode):
    attribute_name: str
    attribute_type: str

class ShaderNodeBackground(ShaderNode): ...

class ShaderNodeBevel(ShaderNode):
    samples: int

class ShaderNodeBlackbody(ShaderNode): ...
class ShaderNodeBrightContrast(ShaderNode): ...

class ShaderNodeBsdfAnisotropic(ShaderNode):
    distribution: str

class ShaderNodeBsdfDiffuse(ShaderNode): ...

class ShaderNodeBsdfGlass(ShaderNode):
    distribution: str

class ShaderNodeBsdfGlossy(ShaderNode):  # bpy.app.version < (4, 0):
    distribution: str

class ShaderNodeBsdfHair(ShaderNode):
    component: str

class ShaderNodeBsdfHairPrincipled(ShaderNode):
    parametrization: str

class ShaderNodeBsdfPrincipled(ShaderNode):
    distribution: str
    subsurface_method: str

class ShaderNodeBsdfRefraction(ShaderNode):
    distribution: str

class ShaderNodeBsdfToon(ShaderNode):
    component: str

class ShaderNodeBsdfTranslucent(ShaderNode): ...
class ShaderNodeBsdfTransparent(ShaderNode): ...
class ShaderNodeBsdfVelvet(ShaderNode): ...

class ShaderNodeBump(ShaderNode):
    invert: bool

class ShaderNodeCameraData(ShaderNode): ...

class ShaderNodeClamp(ShaderNode):
    clamp_type: str

class ShaderNodeCombineColor(ShaderNode):  # bpy.app.version >= (3, 3):
    mode: str

class ShaderNodeCombineHSV(ShaderNode): ...
class ShaderNodeCombineRGB(ShaderNode): ...
class ShaderNodeCombineXYZ(ShaderNode): ...
class ShaderNodeCustomGroup(ShaderNode): ...

class ShaderNodeDisplacement(ShaderNode):
    space: str

class ShaderNodeEeveeSpecular(ShaderNode): ...
class ShaderNodeEmission(ShaderNode): ...
class ShaderNodeFresnel(ShaderNode): ...
class ShaderNodeGamma(ShaderNode): ...

class ShaderNodeGroup(ShaderNode):
    # https://github.com/KhronosGroup/glTF-Blender-IO/issues/1797
    node_tree: NodeTree | None

class ShaderNodeHairInfo(ShaderNode): ...
class ShaderNodeHoldout(ShaderNode): ...
class ShaderNodeHueSaturation(ShaderNode): ...
class ShaderNodeInvert(ShaderNode): ...
class ShaderNodeLayerWeight(ShaderNode): ...
class ShaderNodeLightFalloff(ShaderNode): ...
class ShaderNodeLightPath(ShaderNode): ...

class ShaderNodeMapRange(ShaderNode):
    clamp: bool
    interpolation_type: str

class ShaderNodeMapping(ShaderNode):
    vector_type: str

class ShaderNodeMath(ShaderNode):
    operation: str
    use_clamp: bool

class ShaderNodeMix(ShaderNode):  # bpy.app.version >= (3, 4):
    blend_type: str
    clamp_factor: bool
    clamp_result: bool
    data_type: str
    factor_mode: str

class ShaderNodeMixRGB(ShaderNode):
    blend_type: str
    use_alpha: bool
    use_clamp: bool

class ShaderNodeMixShader(ShaderNode): ...
class ShaderNodeNewGeometry(ShaderNode): ...
class ShaderNodeNormal(ShaderNode): ...

class ShaderNodeNormalMap(ShaderNode):
    space: str
    uv_map: str

class ShaderNodeObjectInfo(ShaderNode): ...

class ShaderNodeOutputAOV(ShaderNode):
    name: str

class ShaderNodeOutputLight(ShaderNode):
    is_active_output: str
    target: str

class ShaderNodeOutputLineStyle(ShaderNode):
    blend_type: str
    is_active_output: bool
    target: str
    use_alpha: bool
    use_clamp: bool

class ShaderNodeOutputMaterial(ShaderNode):
    is_active_output: bool
    target: str

class ShaderNodeOutputWorld(ShaderNode):
    is_active_output: bool
    target: str

class ShaderNodeParticleInfo(ShaderNode): ...
class ShaderNodeRGB(ShaderNode): ...
class ShaderNodeRGBCurve(ShaderNode): ...
class ShaderNodeRGBToBW(ShaderNode): ...

class ShaderNodeScript(ShaderNode):
    bytecode: str
    bytecode_hash: str
    filepath: str
    mode: str
    script: Text
    use_auto_update: bool

class ShaderNodeSeparateColor(ShaderNode):  # bpy.app.version >= (3, 3):
    mode: str

class ShaderNodeSeparateHSV(ShaderNode): ...
class ShaderNodeSeparateRGB(ShaderNode): ...
class ShaderNodeSeparateXYZ(ShaderNode): ...
class ShaderNodeShaderToRGB(ShaderNode): ...
class ShaderNodeSqueeze(ShaderNode): ...

class ShaderNodeSubsurfaceScattering(ShaderNode):
    falloff: str

class ShaderNodeTangent(ShaderNode):
    axis: str
    direction_type: str
    uv_map: str

class ShaderNodeTexBrick(ShaderNode):
    offset: float
    offset_frequency: int
    squash: float
    squash_frequency: int

class ShaderNodeTexChecker(ShaderNode): ...

class ShaderNodeTexCoord(ShaderNode):
    from_instancer: bool
    object: Object | None

class ShaderNodeTexEnvironment(ShaderNode):
    image: Image | None
    interpolation: str
    projection: str

class ShaderNodeTexGradient(ShaderNode):
    gradient_type: str

class ShaderNodeTexIES(ShaderNode):
    filepath: str
    ies: Text
    mode: str

class ShaderNodeTexImage(ShaderNode):
    extension: str
    image: Image | None
    interpolation: str
    projection: str
    projection_blend: float
    @property
    def texture_mapping(self) -> TexMapping: ...

class ShaderNodeTexMagic(ShaderNode):
    turbulence_depth: int

class ShaderNodeTexMusgrave(ShaderNode):
    musgrave_dimensions: str
    musgrave_type: str

class ShaderNodeTexNoise(ShaderNode):
    noise_dimensions: str

class ShaderNodeTexPointDensity(ShaderNode):
    interpolation: str
    object: Object | None
    particle_color_source: str
    point_source: str
    radius: float
    resolution: int
    space: str
    vertex_attribute_name: str
    vertex_color_source: str

class ShaderNodeTexSky(ShaderNode):
    air_density: float
    altitude: float
    color_mapping: ColorMapping
    dust_density: float
    ground_albedo: float
    ozone_density: float
    sky_type: str
    sun_direction: tuple[float, float, float]  # TODO: Vector?
    turbidity: float

class ShaderNodeTexVoronoi(ShaderNode):
    color_mapping: ColorMapping
    distance: str
    feature: str
    texture_mapping: object  # TODO: Add type
    voronoi_dimensions: str

class ShaderNodeTexWave(ShaderNode):
    bands_direction: str
    color_mapping: ColorMapping
    rings_direction: str
    texture_mapping: object  # TODO: Add type
    wave_profile: str
    wave_type: str

class ShaderNodeTexWhiteNoise(ShaderNode):
    noise_dimensions: str

class ShaderNodeTree(NodeTree): ...

class ShaderNodeUVAlongStroke(ShaderNode):
    use_tips: bool

class ShaderNodeUVMap(ShaderNode):
    from_instancer: bool
    uv_map: str

class ShaderNodeValToRGB(ShaderNode): ...
class ShaderNodeValue(ShaderNode): ...
class ShaderNodeVectorCurve(ShaderNode): ...

class ShaderNodeVectorDisplacement(ShaderNode):
    space: str

class ShaderNodeVectorMath(ShaderNode):
    operation: str

class ShaderNodeVectorRotate(ShaderNode):
    invert: bool
    rotation_type: str

class ShaderNodeVectorTransform(ShaderNode):
    convert_from: str
    convert_to: str
    vector_type: str

class ShaderNodeVertexColor(ShaderNode):
    layer_name: str

class ShaderNodeVolumeAbsorption(ShaderNode): ...
class ShaderNodeVolumeInfo(ShaderNode): ...
class ShaderNodeVolumePrincipled(ShaderNode): ...
class ShaderNodeVolumeScatter(ShaderNode): ...
class ShaderNodeWavelength(ShaderNode): ...

class ShaderNodeWireframe(ShaderNode):
    use_pixel_size: bool

class GeometryNode(NodeInternal): ...

class GeometryNodeExtrudeMesh(GeometryNode):
    mode: str

class GeometryNodeDeleteGeometry(GeometryNode):
    domain: str
    mode: str

class GeometryNodeSeparateGeometry(GeometryNode):
    domain: str

# bpy.app.version >= (3, 3):
class GeometryNodeSwitch(GeometryNode):
    input_type: str

class Pose(bpy_struct):
    bones: bpy_prop_collection[PoseBone]
    @classmethod
    def apply_pose_from_action(
        cls,
        action: Action,
        evaluation_time: float = 0.0,
    ) -> None: ...

class MaterialSlot(bpy_struct):
    @property
    def name(self) -> str: ...
    material: (
        Material | None
    )  # When pressing + in material list without selecting, it becomes None

class ObjectModifiers(bpy_prop_collection["Modifier"]):
    def new(self, name: str, type: str) -> Modifier: ...
    def remove(self, modifier: Modifier) -> None: ...
    def clear(self) -> None: ...

class VertexGroup(bpy_struct):
    name: str
    def add(self, index: Sequence[int], weight: float, type: str) -> None: ...

class VertexGroups(bpy_prop_collection[VertexGroup]):
    def new(self, name: str = "Group") -> VertexGroup: ...
    def clear(self) -> None: ...
    def remove(self, vertex_group: VertexGroup) -> None: ...

class Object(ID):
    name: str
    type: str
    data: ID | None  # The document says ID, but when type is empty, it becomes None
    @property
    def mode(self) -> str: ...
    @property
    def pose(self) -> Pose: ...
    def select_set(
        self,
        state: bool,
        view_layer: ViewLayer | None = None,
    ) -> None: ...

    hide_render: bool
    hide_select: bool
    hide_viewport: bool
    @property
    def material_slots(self) -> bpy_prop_collection[MaterialSlot]: ...
    @property
    def users_collection(self) -> bpy_prop_collection[Collection]: ...
    parent: Object | None
    def visible_get(
        self,
        view_layer: ViewLayer | None = None,
        viewport: SpaceView3D | None = None,
    ) -> bool: ...
    @property
    def constraints(self) -> ObjectConstraints: ...
    parent_type: str
    parent_bone: str
    empty_display_size: float
    empty_display_type: str
    display_type: str
    show_in_front: bool

    rotation_mode: str
    rotation_quaternion: Quaternion  # TODO: Is the type correct?
    rotation_euler: Euler
    rotation_axis_angle: Sequence[float]  # Actually bpy_prop_array[float]

    @property
    def bound_box(self) -> bpy_prop_array[bpy_prop_array[float]]: ...

    # The document says 4x4 2D array, but it's actually Matrix
    matrix_basis: Matrix
    # The document says 4x4 2D array, but it's actually Matrix
    matrix_world: Matrix
    # The document says 4x4 2D array, but it's actually Matrix
    matrix_local: Matrix
    # The document says 3-element float array, but it's actually Vector
    scale: Vector

    @property
    def vertex_groups(self) -> VertexGroups: ...
    @property
    def location(
        self,
    ) -> (
        # The document says 3-element float array, but it's actually Vector
        Vector
    ): ...
    @location.setter
    def location(self, value: Iterable[float]) -> None: ...
    def evaluated_get(
        self, depsgraph: Depsgraph
    ) -> Object: ...  # Actually an ID method
    def to_mesh(
        self,
        preserve_all_data_layers: bool = False,
        depsgraph: Depsgraph | None = None,
    ) -> Mesh: ...
    def to_mesh_clear(self) -> None: ...
    @property
    def modifiers(self) -> ObjectModifiers: ...
    @property
    def animation_data(self) -> AnimData | None: ...
    def shape_key_add(self, name: str = "Key", from_mix: bool = True) -> ShapeKey: ...
    def select_get(self, view_layer: ViewLayer | None = None) -> bool: ...
    def hide_get(self, view_layer: ViewLayer | None = None) -> bool: ...
    def hide_set(self, state: bool, view_layer: ViewLayer | None = None) -> bool: ...
    @property
    def children(self) -> Sequence[Object]: ...  # The type is unclear in the document
    def copy(self) -> Object: ...  # override ID.copy

class PreferencesView:
    use_translate_interface: bool

class Preferences(bpy_struct):
    view: PreferencesView
    addons: Addons

class UIList(bpy_struct):
    layout_type: str

class NodeLink(bpy_struct):
    @property
    def from_node(self) -> Node: ...
    @property
    def from_socket(self) -> NodeSocket: ...
    @property
    def is_hidden(self) -> bool: ...
    is_muted: bool
    is_valid: bool
    @property
    def to_node(self) -> Node: ...
    @property
    def to_socket(self) -> NodeSocket: ...

class NodeLinks(bpy_prop_collection[NodeLink]):
    def new(
        self,
        input: NodeSocket,
        output: NodeSocket,
        verify_limits: bool = True,
    ) -> NodeLink: ...
    def remove(self, link: NodeLink) -> None: ...

class Nodes(bpy_prop_collection[Node]):
    def new(self, type: str) -> Node: ...
    def remove(self, node: Node) -> None: ...

class NodeTreeInputs(bpy_prop_collection[NodeSocketInterface]):
    def new(self, type: str, name: str) -> NodeSocketInterface: ...
    def remove(self, socket: NodeSocketInterface) -> None: ...

class NodeTreeOutputs(bpy_prop_collection[NodeSocketInterface]):
    def new(self, type: str, name: str) -> NodeSocketInterface: ...
    def remove(self, socket: NodeSocketInterface) -> None: ...

class NodeTreeInterfaceItem(bpy_struct):
    @property
    def item_type(self) -> str: ...

class NodeTreeInterfaceSocket(NodeTreeInterfaceItem):
    attribute_domain: str
    bl_socket_idname: str
    default_attribute_name: str
    description: str
    force_non_field: bool
    hide_in_modifier: bool
    hide_value: bool
    @property
    def identifier(self) -> str: ...
    in_out: str
    name: str
    socket_type: str

class NodeTreeInterfaceSocketFloat(NodeTreeInterfaceSocket):
    default_value: float
    max_value: float
    min_value: float

class NodeTreeInterfaceSocketFloatAngle(NodeTreeInterfaceSocket):
    default_value: float
    max_value: float
    min_value: float

class NodeTreeInterfaceSocketFloatDistance(NodeTreeInterfaceSocket):
    default_value: float
    max_value: float
    min_value: float

class NodeTreeInterfaceSocketFloatFactor(NodeTreeInterfaceSocket):
    default_value: float
    max_value: float
    min_value: float

class NodeTreeInterfaceSocketFloatPercentage(NodeTreeInterfaceSocket):
    default_value: float
    max_value: float
    min_value: float

class NodeTreeInterfaceSocketFloatTime(NodeTreeInterfaceSocket):
    default_value: float
    max_value: float
    min_value: float

class NodeTreeInterfaceSocketFloatTimeAbsolute(NodeTreeInterfaceSocket):
    default_value: float
    max_value: float
    min_value: float

class NodeTreeInterfaceSocketFloatUnsigned(NodeTreeInterfaceSocket):
    default_value: float
    max_value: float
    min_value: float

class NodeTreeInterfaceSocketColor(NodeTreeInterfaceSocket):
    default_value: tuple[float, float, float, float]

class NodeTreeInterfaceSocketVector(NodeTreeInterfaceSocket):
    default_value: tuple[float, float, float]
    max_value: float
    min_value: float

class NodeTreeInterfaceSocketVectorAcceleration(NodeTreeInterfaceSocket):
    default_value: Vector
    max_value: float
    min_value: float

class NodeTreeInterfaceSocketVectorDirection(NodeTreeInterfaceSocket):
    default_value: Vector
    max_value: float
    min_value: float

class NodeTreeInterfaceSocketVectorEuler(NodeTreeInterfaceSocket):
    default_value: Euler
    max_value: float
    min_value: float

class NodeTreeInterfaceSocketVectorTranslation(NodeTreeInterfaceSocket):
    default_value: Vector
    max_value: float
    min_value: float

class NodeTreeInterfaceSocketVectorVelocity(NodeTreeInterfaceSocket):
    default_value: Vector
    max_value: float
    min_value: float

class NodeTreeInterfaceSocketVectorXYZ(NodeTreeInterfaceSocket):
    default_value: Vector
    max_value: float
    min_value: float

class NodeTreeInterfaceSocketInt(NodeTreeInterfaceSocket):
    default_value: int
    max_value: int
    min_value: int
    subtype: str

class NodeTreeInterfaceSocketIntFactor(NodeTreeInterfaceSocket):
    default_value: int
    max_value: int
    min_value: int
    subtype: str

class NodeTreeInterfaceSocketIntPercentage(NodeTreeInterfaceSocket):
    default_value: int
    max_value: int
    min_value: int
    subtype: str

class NodeTreeInterfacePanel(NodeTreeInterfaceItem): ...

class NodeTreeInterface(bpy_struct):
    @property
    def items_tree(self) -> bpy_prop_collection[NodeTreeInterfaceItem]: ...
    def new_socket(
        self,
        name: str,
        *,  # It's not mentioned in the document that it's keyword-only?
        description: str = "",
        in_out: str = ...,
        socket_type: str = "DEFAULT",
        parent: NodeTreeInterfacePanel | None = None,
    ) -> NodeTreeInterfaceSocket: ...
    def clear(self) -> None: ...
    def remove(
        self,
        item: NodeTreeInterfaceItem,
        move_content_to_parent: bool = True,
    ) -> None: ...

class NodeTree(ID):
    @property
    def links(self) -> NodeLinks: ...
    @property
    def nodes(self) -> Nodes: ...
    @property
    def type(self) -> str: ...
    @property
    def animation_data(self) -> AnimData | None: ...

    # bpy.app.version < (4, 0)
    @property
    def inputs(self) -> NodeTreeInputs: ...
    @property
    def outputs(self) -> NodeTreeOutputs: ...

    # bpy.app.version >= (4, 0)
    @property
    def interface(self) -> NodeTreeInterface: ...
    def update(self) -> None: ...

class Material(ID):
    @property
    def animation_data(self) -> AnimData | None: ...

    blend_method: str

    @property
    def node_tree(self) -> NodeTree | None: ...

    use_nodes: bool
    alpha_threshold: float
    shadow_method: str
    use_backface_culling: bool
    show_transparent_back: bool
    alpha_method: str
    diffuse_color: bpy_prop_array[float]
    roughness: float

class IDMaterials(bpy_prop_collection[Material | None]):
    def append(
        self, value: Material
    ) -> None: ...  # TODO: does not exist in documentation

class Curve(ID):
    @property
    def materials(self) -> IDMaterials: ...

class Modifier(bpy_struct):
    name: str
    show_expanded: bool
    show_in_editmode: bool
    show_viewport: bool
    show_render: bool

    @property
    def type(self) -> str: ...

    # TODO: Actually a bpy_struct method
    def get(self, key: str, default: object = None) -> object: ...
    # TODO: Actually a bpy_struct method
    def __getitem__(self, key: str) -> object: ...
    # TODO: Actually a bpy_struct method
    def __setitem__(self, key: str, value: object) -> None: ...

class ArmatureModifier(Modifier):
    object: Object | None

class NodesModifier(Modifier):
    node_group: NodeTree | None  # Whether it becomes None needs verification

class OperatorFileListElement(PropertyGroup): ...

class Constraint(bpy_struct):
    name: str
    is_valid: bool
    mute: bool
    influence: float

class ObjectConstraints(bpy_prop_collection[Constraint]):
    def new(self, type: str) -> Constraint: ...

class DampedTrackConstraint(Constraint):
    head_tail: float
    subtarget: str
    target: Object | None
    track_axis: str

class CopyRotationConstraint(Constraint):
    euler_order: str
    target: Object | None
    mix_mode: str
    use_x: bool
    use_y: bool
    use_z: bool
    invert_x: bool
    invert_y: bool
    invert_z: bool
    owner_space: str
    target_space: str
    subtarget: str

class ViewLayers(bpy_prop_collection[ViewLayer]):
    def update(self) -> None: ...  # TODO: Not mentioned in the document

class ColorManagedViewSettings(bpy_struct):
    view_transform: str

class View3DCursor(bpy_struct):
    matrix: Matrix

class ImageFormatSettings(bpy_struct):
    file_format: str

class RenderSettings(bpy_struct):
    fps: int
    fps_base: float
    resolution_percentage: int
    resolution_x: int
    resolution_y: int
    filepath: str
    engine: str
    @property
    def image_settings(self) -> ImageFormatSettings: ...

class World(ID):
    use_nodes: bool
    color: Color

class CyclesRenderSettings(bpy_struct):
    # TODO: This class is sometimes not mentioned in the document
    samples: int
    adaptive_min_samples: int
    use_denoising: bool
    use_adaptive_sampling: bool

class SceneEEVEE(bpy_struct):
    taa_render_samples: int

class Scene(ID):
    frame_start: int
    frame_current: int
    frame_end: int

    def frame_set(self, frame: int, subframe: float = 0.0) -> None: ...
    @property
    def collection(self) -> Collection: ...
    @property
    def view_layers(self) -> ViewLayers: ...
    @property
    def view_settings(self) -> ColorManagedViewSettings: ...
    @property
    def cursor(self) -> View3DCursor: ...
    @property
    def render(self) -> RenderSettings: ...
    @property
    def eevee(self) -> SceneEEVEE: ...
    @property
    def cycles(self) -> CyclesRenderSettings: ...

    camera: Object | None
    world: World | None

class AreaSpaces(bpy_prop_collection[Space]): ...

class Area(bpy_struct):
    @property
    def x(self) -> int: ...
    @property
    def y(self) -> int: ...
    @property
    def width(self) -> int: ...
    @property
    def height(self) -> int: ...
    @property
    def spaces(self) -> AreaSpaces: ...
    @property
    def regions(self) -> bpy_prop_collection[Region]: ...
    type: str
    show_menus: bool

class Screen(ID):
    @property
    def areas(self) -> bpy_prop_collection[Area]: ...

class Window(bpy_struct):
    screen: Screen
    scene: Scene

class Timer(bpy_struct): ...

class Camera(ID):
    angle: float
    angle_x: float
    angle_y: float
    clip_end: float
    clip_start: float
    display_size: float
    lens: float
    lens_unit: str
    ortho_scale: float
    type: str
    shift_x: float
    shift_y: float

class WindowManager(ID):
    @property
    def windows(self) -> bpy_prop_collection[Window]: ...
    @classmethod
    def invoke_props_dialog(cls, operator: Operator, width: int = 300) -> set[str]: ...
    @classmethod
    def modal_handler_add(cls, operator: Operator) -> bool: ...
    def progress_begin(self, min: float, max: float) -> None: ...
    def progress_update(self, value: float) -> None: ...
    def progress_end(self) -> None: ...
    def event_timer_add(
        self,
        time_step: float,
        window: Window | None = None,
    ) -> Timer: ...

class SpaceFileBrowser(Space):
    active_operator: Operator

class View2D(bpy_struct): ...

class Region(bpy_struct):
    def alignment(self) -> str: ...
    def data(self) -> AnyType: ...
    def height(self) -> int: ...
    def type(self) -> str: ...
    def view2d(self) -> View2D: ...
    def width(self) -> int: ...
    def x(self) -> int: ...
    def y(self) -> int: ...

class RegionView3D(bpy_struct):
    # The document says 2D array, so needs confirmation
    perspective_matrix: Matrix
    # The document says 2D array, so needs confirmation
    view_matrix: Matrix
    # The document says 2D array, so needs confirmation
    window_matrix: Matrix

class Context(bpy_struct):
    def evaluated_depsgraph_get(self) -> Depsgraph: ...

    # https://docs.blender.org/api/2.93/bpy.context.html
    # https://docs.blender.org/api/2.93/bpy.types.Context.html

    # Global Context
    @property
    def area(self) -> Area: ...
    @property
    def blend_data(self) -> BlendData: ...
    @property
    def mode(self) -> str: ...
    @property
    def preferences(self) -> Preferences: ...
    @property
    def region_data(self) -> RegionView3D: ...
    @property
    def scene(self) -> Scene: ...
    @property
    def screen(self) -> Screen: ...
    @property
    def space_data(self) -> Space: ...
    @property
    def view_layer(self) -> ViewLayer: ...
    @property
    def window(self) -> Window: ...
    @property
    def window_manager(self) -> WindowManager: ...

    # Screen Context
    object: Object | None
    active_object: Object | None
    selectable_objects: Sequence[Object]
    selected_objects: Sequence[Object]

    # Buttons Context or Node Context
    material: Material | None

class CollectionObjects(bpy_prop_collection[Object]):
    def link(self, obj: Object) -> None: ...
    def unlink(self, obj: Object) -> None: ...

class CollectionChildren(bpy_prop_collection["Collection"]):
    def link(self, child: Collection) -> None: ...

class Collection(ID):
    objects: CollectionObjects
    children: CollectionChildren

class BlendDataCollections(bpy_prop_collection[Collection]):
    def new(self, name: str) -> Collection: ...
    def remove(
        self,
        collection: Collection,
        do_unlink: bool = True,
        do_id_user: bool = True,
        do_ui_user: bool = True,
    ) -> None: ...
    active: Object | None

class BlendDataObjects(bpy_prop_collection[Object]):
    def new(self, name: str, object_data: ID | None) -> Object: ...
    def remove(
        self,
        element: Object,
        do_unlink: bool = True,
        do_id_user: bool = True,
        do_ui_user: bool = True,
    ) -> None: ...

class Library(ID):
    filepath: str
    @property
    def packed_file(self) -> PackedFile | None: ...
    @property
    def library(self) -> Library | None: ...
    @property
    def version(self) -> tuple[int, int, int]: ...
    @property
    def users_id(self) -> tuple[int, ...]: ...
    def reload(self) -> None: ...

class BlendDataMaterials(bpy_prop_collection[Material]):
    def new(self, name: str) -> Material: ...
    def remove(
        self,
        material: Material,
        do_unlink: bool = True,
        do_id_user: bool = True,
        do_ui_user: bool = True,
    ) -> None: ...

class BlendDataImages(bpy_prop_collection[Image]):
    def new(
        self,
        name: str,
        width: int,
        height: int,
        alpha: bool = False,
        float_buffer: bool = False,
        stereo3d: bool = False,
        is_data: bool = False,
        tiled: bool = False,
    ) -> Image: ...
    def load(self, filepath: str, check_existing: bool = False) -> Image: ...

class BlendDataArmatures(bpy_prop_collection[Armature]):
    def new(self, name: str) -> Armature: ...

class BlendDataTexts(bpy_prop_collection[Text]):
    def new(self, name: str) -> Text: ...

class BlendDataMeshes(bpy_prop_collection[Mesh]):
    def new(self, name: str) -> Mesh: ...
    def new_from_object(
        self,
        obj: Object,
        preserve_all_data_layers: bool = False,
        depsgraph: Depsgraph | None = None,
    ) -> Mesh: ...
    def remove(
        self,
        mesh: Mesh,
        do_unlink: bool = True,
        do_id_user: bool = True,
        do_ui_user: bool = True,
    ) -> None: ...

class BlendDataLibraries(bpy_prop_collection[Library]):
    def load(
        self,
        filepath: str,
        link: bool,
    ) -> contextlib.AbstractContextManager[
        tuple[BlendData, BlendData]
    ]: ...  # Does not exist in the document
    def remove(
        self,
        library: Library,
        do_unlink: bool = True,
        do_id_user: bool = True,
        do_ui_user: bool = True,
    ) -> None: ...

class BlendDataNodeTrees(bpy_prop_collection[NodeTree]):
    def new(self, name: str, type: str) -> NodeTree: ...
    def remove(
        self,
        tree: NodeTree,
        do_unlink: bool = True,
        do_id_user: bool = True,
        do_ui_user: bool = True,
    ) -> None: ...
    def append(self, value: NodeTree) -> None: ...  # Does not exist in the document

class BlendDataActions(bpy_prop_collection[Action]):
    def new(self, name: str) -> Action: ...

class BlendDataScenes(bpy_prop_collection[Scene]):
    def new(self, name: str) -> Scene: ...
    def remove(self, scene: Scene, *, do_unlink: bool = True) -> None: ...

class VectorFont(ID): ...

class MetaElement(bpy_struct):
    co: Vector
    hide: bool
    radius: float
    rotation: Quaternion

class MetaBallElements(bpy_prop_collection[MetaElement]):
    def new(self, type: str = "BALL") -> MetaElement: ...

class MetaBall(ID):
    threshold: float
    resolution: float

    @property
    def elements(self) -> MetaBallElements: ...

class BlendDataMetaBalls(bpy_prop_collection[MetaBall]):
    def new(self, name: str) -> MetaBall: ...
    def remove(
        self,
        metaball: MetaBall,
        do_unlink: bool = True,
        do_id_user: bool = True,
        do_ui_user: bool = True,
    ) -> None: ...

class BlendDataBrushes: ...
class BlendDataCacheFiles: ...

class BlendDataCameras:
    def new(self, name: str) -> Camera: ...

class BlendDataCurves(bpy_prop_collection[Curve]):
    def remove(
        self,
        curve: Curve,
        do_unlink: bool = True,
        do_id_user: bool = True,
        do_ui_user: bool = True,
    ) -> None: ...

class BlendDataFonts(bpy_prop_collection[VectorFont]):
    def remove(
        self,
        vfont: VectorFont,
        do_unlink: bool = True,
        do_id_user: bool = True,
        do_ui_user: bool = True,
    ) -> None: ...

class BlendDataGreasePencils: ...
class BlendDataLattices: ...
class BlendDataProbes: ...

class Light(ID):
    color: Color

class BlendDataLights:
    def new(self, name: str, type: str) -> Light: ...

class BlendDataLineStyles: ...
class BlendDataMasks: ...
class BlendDataMovieClips: ...
class BlendDataPaintCurves: ...
class BlendDataPalettes: ...
class BlendDataParticles: ...
class BlendDataScreens(bpy_prop_collection[Screen]): ...
class BlendDataSounds: ...
class BlendDataSpeakers: ...
class BlendDataTextures: ...
class BlendDataVolumes: ...
class BlendDataWindowManagers(bpy_prop_collection[WindowManager]): ...
class BlendDataWorkSpaces: ...

class BlendDataWorlds:
    def new(self, name: str) -> World: ...

class BlendData:
    @property
    def actions(self) -> BlendDataActions: ...
    @property
    def armatures(self) -> BlendDataArmatures: ...
    @property
    def brushes(self) -> BlendDataBrushes: ...
    @property
    def cache_files(self) -> BlendDataCacheFiles: ...
    @property
    def cameras(self) -> BlendDataCameras: ...
    @property
    def collections(self) -> BlendDataCollections: ...
    @property
    def curves(self) -> BlendDataCurves: ...
    @property
    def filepath(self) -> str: ...
    @property
    def fonts(self) -> BlendDataFonts: ...
    @property
    def grease_pencils(self) -> BlendDataGreasePencils: ...
    @property
    def images(self) -> BlendDataImages: ...
    @property
    def is_dirty(self) -> bool: ...
    @property
    def is_saved(self) -> bool: ...
    @property
    def lattices(self) -> BlendDataLattices: ...
    @property
    def libraries(self) -> BlendDataLibraries: ...
    @property
    def lightprobes(self) -> BlendDataProbes: ...
    @property
    def lights(self) -> BlendDataLights: ...
    @property
    def linestyles(self) -> BlendDataLineStyles: ...
    @property
    def masks(self) -> BlendDataMasks: ...
    @property
    def materials(self) -> BlendDataMaterials: ...
    @property
    def meshes(self) -> BlendDataMeshes: ...
    @property
    def metaballs(self) -> BlendDataMetaBalls: ...
    @property
    def movieclips(self) -> BlendDataMovieClips: ...
    @property
    def node_groups(self) -> BlendDataNodeTrees: ...
    @property
    def objects(self) -> BlendDataObjects: ...
    @property
    def paint_curves(self) -> BlendDataPaintCurves: ...
    @property
    def palettes(self) -> BlendDataPalettes: ...
    @property
    def particles(self) -> BlendDataParticles: ...
    @property
    def scenes(self) -> BlendDataScenes: ...
    @property
    def screens(self) -> BlendDataScreens: ...
    @property
    def shape_keys(self) -> bpy_prop_collection[Key]: ...
    @property
    def sounds(self) -> BlendDataSounds: ...
    @property
    def speakers(self) -> BlendDataSpeakers: ...
    @property
    def texts(self) -> BlendDataTexts: ...
    @property
    def textures(self) -> BlendDataTextures: ...
    use_autopack: bool
    @property
    def version(self) -> Sequence[int]: ...
    @property
    def volumes(self) -> BlendDataVolumes: ...
    @property
    def window_managers(self) -> BlendDataWindowManagers: ...
    @property
    def workspaces(self) -> BlendDataWorkSpaces: ...
    @property
    def worlds(self) -> BlendDataWorlds: ...

class Operator(bpy_struct):
    bl_idname: str
    bl_label: str
    @property
    def layout(self) -> UILayout: ...

# This type is used with UILayout.prop_search, but definition is unclear due to docs
AnyType: TypeAlias = ID | BlendData | Operator | PropertyGroup

class Panel(bpy_struct):
    bl_idname: str
    @property
    def layout(self) -> UILayout: ...

class Menu(bpy_struct): ...
class Header(bpy_struct): ...
class KeyingSetInfo(bpy_struct): ...
class RenderEngine(bpy_struct): ...

class FileHandler(bpy_struct):
    bl_export_operator: str
    bl_file_extensions: str
    bl_idname: str
    bl_import_operator: str
    bl_label: str
    @classmethod
    def poll_drop(cls, context: Context) -> bool: ...

TOPBAR_MT_file_import: MutableSequence[Callable[[Operator, Context], None]]
TOPBAR_MT_file_export: MutableSequence[Callable[[Operator, Context], None]]
VIEW3D_MT_armature_add: MutableSequence[Callable[[Operator, Context], None]]
