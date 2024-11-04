# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from typing import Callable, Optional

def register(
    function: Callable[[], Optional[float]],
    first_interval: float = 0,
    persistent: bool = False,
) -> None: ...
def is_registered(function: Callable[[], Optional[float]]) -> bool: ...
