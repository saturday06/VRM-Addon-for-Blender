from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Sequence, Union

import bpy


class AbstractBaseVrmExporter(ABC):
    def __init__(
        self,
        context: bpy.types.Context,
    ) -> None:
        self.context = context

    @abstractmethod
    def export_vrm(self) -> Optional[bytes]:
        pass


def assign_dict(
    target: Dict[str, Any],
    key: str,
    value: Union[int, float, Dict[str, Any], Sequence[Any], None],
    default_value: Any = None,
) -> bool:
    if value is None or value == default_value:
        return False
    target[key] = value
    return True
