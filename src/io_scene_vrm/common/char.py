# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from collections.abc import Mapping
from typing import Final

INTERNAL_NAME_PREFIX: Final = "\N{FULLWIDTH BROKEN BAR}"
"""
The letter to be prefixed when naming internal invisible objects. It was chosen so that
the sort order would be backward and also so that it would be easy to identify the
object as internal.
"""

DISABLE_TRANSLATION: Final = "\N{ZERO WIDTH SPACE}"

FULLWIDTH_ASCII_TO_ASCII_MAP: Final[Mapping[str, str]] = {
    chr(ascii_char + 0x0000_FEE0): chr(ascii_char) for ascii_char in range(0x21, 0x7E)
}
