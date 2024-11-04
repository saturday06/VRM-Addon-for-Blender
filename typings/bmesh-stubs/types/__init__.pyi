# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Iterator, Sequence
from typing import Generic, Optional, TypeVar

from bpy.types import Mesh
from mathutils import Vector

__BMElemSeqElement = TypeVar("__BMElemSeqElement")

class BMElemSeq(Generic[__BMElemSeqElement]):
    def __len__(self) -> int: ...
    def __getitem__(self, key: int) -> __BMElemSeqElement: ...
    def __iter__(self) -> Iterator[__BMElemSeqElement]: ...

class BMLoopUV:
    uv: Vector

class BMVert:
    index: int
    co: Vector

    def __getitem__(
        self,
        value: BMLoopUV,
    ) -> Vector: ...  # ドキュメントには存在しない

class BMLayerItem:
    def copy_from(self, other: BMLayerItem) -> None: ...
    @property
    def name(self) -> str: ...

class BMLayerCollection:
    def __getitem__(self, key: str) -> BMLoopUV: ...  # ドキュメントに記載はない?
    def keys(self) -> Iterator[str]: ...
    def values(self) -> Iterator[BMLayerItem]: ...
    def items(self) -> Iterator[tuple[str, BMLayerItem]]: ...

class BMLayerAccessLoop:
    uv: BMLayerCollection

class BMLayerAccessVert:
    shape: BMLayerCollection

class BMVertSeq:
    def new(
        self,
        co: Sequence[float] = (0.0, 0.0, 0.0),
        example: Optional[BMVert] = None,
    ) -> BMVert: ...
    @property
    def layers(self) -> BMLayerAccessVert: ...
    def ensure_lookup_table(self) -> None: ...
    def index_update(self) -> None: ...
    def __getitem__(self, key: int) -> BMVert: ...  # ドキュメントに記載はない?
    def __len__(self) -> int: ...  # ドキュメントに記載はない?

class BMEdge: ...

class BMEdgeSeq:
    def new(
        self,
        verts: tuple[
            BMVert,
            BMVert,
        ],  # 実際にはSequenceだと思うが、2要素チェックをしたいのでtuple
        example: Optional[BMEdge] = None,
    ) -> BMEdge: ...
    def ensure_lookup_table(self) -> None: ...

class BMLoop:
    index: int
    @property
    def face(self) -> BMFace: ...
    @property
    def vert(self) -> BMVert: ...
    def __getitem__(
        self,
        uv: BMLoopUV,
    ) -> BMLoopUV: ...  # TODO: ドキュメントに存在しない

class BMLoopSeq:
    @property
    def layers(self) -> BMLayerAccessLoop: ...

class BMFace:
    material_index: int
    @property
    def loops(self) -> BMElemSeq[BMLoop]: ...

class BMFaceSeq:
    def new(
        self,
        verts: Sequence[BMVert],
        example: Optional[BMFace] = None,
    ) -> BMFace: ...
    def __iter__(self) -> Iterator[BMFace]: ...
    def ensure_lookup_table(self) -> None: ...

class BMesh:
    @property
    def faces(self) -> BMFaceSeq: ...
    @property
    def edges(self) -> BMEdgeSeq: ...
    @property
    def verts(self) -> BMVertSeq: ...
    @property
    def loops(self) -> BMLoopSeq: ...
    def free(self) -> None: ...
    def to_mesh(self, mesh: Mesh) -> None: ...
    def from_mesh(
        self,
        mesh: Mesh,
        face_normals: bool = True,
        use_shape_key: bool = False,
        shape_key_index: int = 0,
    ) -> None: ...
    def calc_loop_triangles(self) -> list[tuple[BMLoop, ...]]: ...  # TODO: 正しい型
