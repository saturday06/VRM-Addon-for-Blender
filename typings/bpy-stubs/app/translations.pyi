# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

locale: str

def pgettext(msgid: str, msgctxt: str | None = None) -> str: ...
def unregister(module_name: str) -> None: ...
def register(
    module_name: str,
    dictionary: dict[str, dict[tuple[str, str], str]],
) -> None: ...
