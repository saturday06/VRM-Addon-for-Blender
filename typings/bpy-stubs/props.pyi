# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Sequence
from typing import Callable, TypeVar

from bpy.types import AddonPreferences, Context, Operator, PropertyGroup
from mathutils import Vector

__PointerPropertyTarget = TypeVar("__PointerPropertyTarget", bound=type)
__CollectionPropertyElement = TypeVar("__CollectionPropertyElement", bound=type)
__CallbackSelf = TypeVar(
    "__CallbackSelf", bound=AddonPreferences | Operator | PropertyGroup
)

def BoolProperty(
    *,
    name: str = "",
    description: str = "",
    default: bool = False,
    options: set[str] = ...,
    override: set[str] = ...,
    tags: set[str] = ...,  # TODO: Type unknown
    subtype: str = "NONE",
    update: Callable[[__CallbackSelf, Context], None] | None = None,
    get: Callable[[__CallbackSelf], bool] | None = None,
    set: Callable[[__CallbackSelf, bool], None] | None = None,
) -> bool: ...
def CollectionProperty(
    *,
    type: __CollectionPropertyElement,
    name: str = "",
    description: str = "",
    options: set[str] = ...,
    override: set[str] = ...,
    tags: set[str] = ...,
) -> __CollectionPropertyElement: ...
def EnumProperty(
    *,
    items: Sequence[tuple[str, str, str, int]]
    | Sequence[tuple[str, str, str, str, int]],
    name: str = "",
    description: str = "",
    default: str
    | int
    | None = None,  # set can also be accepted, but the specification could not be read
    options: set[str] = ...,
    override: set[str] = ...,
    tags: set[str] = ...,
    update: Callable[[__CallbackSelf, Context], None] | None = None,
    get: Callable[[__CallbackSelf], int] | None = None,
    set: Callable[[__CallbackSelf, int], None] | None = None,
) -> str: ...
def FloatProperty(
    *,
    name: str = "",
    description: str = "",
    default: float = 0.0,
    min: float = ...,
    max: float = ...,
    soft_min: float = ...,
    soft_max: float = ...,
    step: int = 3,
    precision: int = 2,
    options: set[str] = ...,
    override: set[str] = ...,
    tags: set[str] = ...,
    subtype: str = "NONE",
    unit: str = "NONE",
    update: Callable[[__CallbackSelf, Context], None] | None = None,
    get: Callable[[__CallbackSelf], float] | None = None,
    set: Callable[[__CallbackSelf, float], None] | None = None,
) -> float: ...
def FloatVectorProperty(
    *,
    name: str = "",
    description: str = "",
    default: tuple[float, ...] = (0.0, 0.0, 0.0),
    min: float = ...,
    max: float = ...,
    soft_min: float = ...,
    soft_max: float = ...,
    step: int = 3,
    precision: int = 2,
    options: set[str] = ...,
    override: set[str] = ...,
    tags: set[str] = ...,
    subtype: str = "NONE",
    unit: str = "NONE",
    size: int = 3,
    update: Callable[[__CallbackSelf, Context], None] | None = None,
    get: Callable[[__CallbackSelf], tuple[float, ...]] | None = None,
    set: Callable[[__CallbackSelf, Sequence[float]], None] | None = None,
) -> Vector: ...  # TODO: I think Vector was returned, but I'm not confident
def IntProperty(
    *,
    name: str = "",
    description: str = "",
    default: int = 0,
    min: int = ...,
    max: int = ...,
    soft_min: int = ...,
    soft_max: int = ...,
    step: int = 1,
    options: set[str] = ...,
    override: set[str] = ...,
    tags: set[str] = ...,
    subtype: str = "NONE",
    update: Callable[[__CallbackSelf, Context], None] | None = None,
    get: Callable[[__CallbackSelf], int] | None = None,
    set: Callable[[__CallbackSelf, int], None] | None = None,
) -> int: ...
def IntVectorProperty(
    *,
    name: str = "",
    description: str = "",
    translation_context: str = "*",
    default: tuple[int, ...] = (0, 0, 0),
    min: int = ...,
    max: int = ...,
    soft_min: int = ...,
    soft_max: int = ...,
    step: int = 1,
    options: set[str] = ...,
    override: set[str] = ...,
    tags: set[str] = ...,
    subtype: str = "NONE",
    size: int = ...,
    update: Callable[[__CallbackSelf, Context], None] | None = None,
    get: Callable[[__CallbackSelf], tuple[int, ...]] | None = None,
    set: Callable[[__CallbackSelf, Sequence[int]], None] | None = None,
) -> Vector: ...  # TODO: I think Vector was returned, but I'm not confident
def PointerProperty(
    *,
    type: __PointerPropertyTarget,
    name: str = "",
    description: str = "",
    options: set[str] = ...,
    override: set[str] = ...,
    tags: set[str] = ...,  # TODO: Type unknown
    poll: Callable[[__CallbackSelf, object], bool] | None = None,
    update: Callable[[__CallbackSelf, Context], None] | None = None,
) -> __PointerPropertyTarget: ...
def StringProperty(
    *,
    name: str = "",
    description: str = "",
    default: str = "",
    maxlen: int = 0,
    options: set[str] = ...,
    override: set[str] = ...,
    tags: set[str] = ...,  # TODO: Type unknown
    subtype: str = "NONE",
    update: Callable[[__CallbackSelf, Context], None] | None = None,
    get: Callable[[__CallbackSelf], str] | None = None,
    set: Callable[[__CallbackSelf, str], None] | None = None,
) -> str: ...
