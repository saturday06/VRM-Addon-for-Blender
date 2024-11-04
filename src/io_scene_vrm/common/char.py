# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from typing import Final

INTERNAL_NAME_PREFIX: Final = "\N{FULLWIDTH BROKEN BAR}"
"""
The letter to be prefixed when naming internal invisible objects. It was chosen so that
the sort order would be backward and also so that it would be easy to identify the
object as internal.
"""

DISABLE_TRANSLATION: Final = "\N{ZERO WIDTH SPACE}"
