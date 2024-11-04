# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import contextlib
from collections.abc import Sequence
from typing import Optional, Union

from mathutils import Matrix

class GPUOffScreen:
    def __init__(self, width: int, height: int) -> None: ...
    def bind(self) -> contextlib.AbstractContextManager[None]: ...
    color_texture: int

class GPUIndexBuf:
    def __init__(self, type: str, seq: object) -> None: ...

class GPUVertBuf:
    def __init__(self, len: int, format: object) -> None: ...

class GPUBatch:
    def __init__(
        self,
        type: str,
        buf: GPUVertBuf,
        elem: Optional[GPUIndexBuf] = None,
    ) -> None: ...

class GPUShader:
    def __init__(
        self,
        vertexcode: str,
        fragcode: str,
        geocode: Optional[str] = None,
        libcode: Optional[str] = None,
        defines: Optional[str] = None,
    ) -> None: ...
    def uniform_float(
        self,
        name: str,
        # どうやらMatrixも直接渡せるようだが、要確認
        value: Union[float, Sequence[float], Matrix],
    ) -> None: ...
    def bind(self) -> None: ...
    def uniform_int(self, name: str, seq: Union[int, Sequence[int]]) -> None: ...
