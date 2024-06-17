"""Any型や、Any型を型引数に持つの変数のAny部分をobjectとして読み直す関数を提供する.

どうしてもAny型の変数が発生することがあり、そのような変数はmypyやpyrightはそのまま扱うことができない。
公式にはcastを使ってどうにかするっぽいが、castは使い始めると収拾がつかなくなる。
そのため、このモジュールでのみ例外的にAnyを許可し、objectに変換することで利用可能な変数に変換する。

pyrightでUnknownをobject扱いするIssueが出ている。
https://github.com/microsoft/pyright/issues/3650
"""

from collections.abc import Iterator
from typing import (
    Any,  # Anyはここのモジュールのみで利用を許可する。
    Optional,
)


def to_object(  # type: ignore[misc]
    any_object: Any,  # noqa: ANN401  # Anyはここのモジュールのみで利用を許可する。
) -> object:
    if not isinstance(any_object, object):
        raise TypeError  # typing.assert_never()
    return any_object


def iterator_to_object_iterator(  # type: ignore[misc]
    any_iterator: Any,  # noqa: ANN401  # Anyはここのモジュールのみで利用を許可する。
) -> Optional[Iterator[object]]:
    any_iterator_without_type_narrowing = any_iterator
    if not isinstance(any_iterator_without_type_narrowing, Iterator):
        return None
    return map(to_object, any_iterator)
