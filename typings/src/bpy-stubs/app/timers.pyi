# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from typing import Callable

def register(
    function: Callable[[], float | None],
    first_interval: float = 0,
    persistent: bool = False,
) -> None: ...
def is_registered(function: Callable[[], float | None]) -> bool: ...
