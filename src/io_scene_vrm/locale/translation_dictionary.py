# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from . import ja_jp, zh_hans


def build_translation_dictionary() -> dict[str, dict[tuple[str, str], str]]:
    return {
        ja_jp.LOCALE_KEY: dict(ja_jp.TRANSLATION_DICTIONARY),
        zh_hans.LOCALE_KEY: dict(zh_hans.TRANSLATION_DICTIONARY),
    }
