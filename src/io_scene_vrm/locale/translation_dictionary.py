# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import sys
from typing import Final

from . import ja_jp as __ja_jp
from . import zh_hans as __zh_hans

translation_dictionary: Final = {
    locale_key: {
        # Use sys.intern for the strings returned here to prevent them from being
        # garbage collected. This is because EnumProperty item strings must be retained
        # until Blender exits.
        # https://docs.blender.org/api/2.93/bpy.props.html#bpy.props.EnumProperty
        translation_key: sys.intern(translated_text)
        for translation_key, translated_text in translation_dictionary.items()
    }
    for locale_key, translation_dictionary in {
        __ja_jp.locale_key: __ja_jp.translation_dictionary,
        __zh_hans.locale_key: __zh_hans.translation_dictionary,
    }.items()
}
