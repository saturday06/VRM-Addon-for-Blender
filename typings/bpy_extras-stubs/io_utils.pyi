# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from bpy.types import Context, Event

class ImportHelper:
    filepath: str  # ドキュメントには記載がない

    def invoke(
        self,
        context: Context,
        event: Event,
    ) -> set[str]: ...

class ExportHelper:
    filepath: str  # ドキュメントには記載がない

    def invoke(
        self,
        context: Context,
        event: Event,
    ) -> set[str]: ...
