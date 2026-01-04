# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from . import ja_jp, zh_hans

translation_dictionary = {
    ja_jp.locale_key: ja_jp.translation_dictionary,
    zh_hans.locale_key: zh_hans.translation_dictionary,
}
