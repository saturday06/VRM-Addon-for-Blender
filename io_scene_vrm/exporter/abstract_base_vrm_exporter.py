from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class AbstractBaseVrmExporter(ABC):
    @abstractmethod
    def export_vrm(self) -> Optional[bytes]:
        pass


def assign_dict(
    target: Dict[str, Any],
    key: str,
    value: Optional[Union[int, float, Dict[str, Any], List[Any]]],
    default_value: Any = None,
) -> bool:
    if value is None or value == default_value:
        return False
    target[key] = value
    return True
