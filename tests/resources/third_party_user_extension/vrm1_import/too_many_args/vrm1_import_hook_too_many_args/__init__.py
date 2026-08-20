# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

from io_scene_vrm.common.third_party_user_extension import (
    _logger as third_party_user_extension_logger,
)

bl_info = {
    "name": "Third Party User Extension Test",
    "author": "saturday06",
    "version": (1, 0, 0),
    "location": "File > Import-Export",
    "description": "Test add-on",
    "blender": (2, 93, 0),
    "warning": "",
    "support": "COMMUNITY",
    "wiki_url": "",
    "doc_url": "https://vrm-addon-for-blender.info",
    "tracker_url": "https://github.com/saturday06/VRM-Addon-for-Blender/issues",
    "category": "Import-Export",
}


_log_pattern = (
    "Failed to call post_import_hook of Vrm1ImportUserExtension from addon "
    "'vrm1_import_hook_too_many_args': "
    "the callback requires 15 arguments, but only 8 are available"
)


def register() -> None:
    third_party_user_extension_logger.clear_log_output_match_count()
    third_party_user_extension_logger.register_log_output_match(_log_pattern)


def unregister() -> None:
    pass


def assert_vrm_third_party_user_extension_state() -> None:
    count = third_party_user_extension_logger.get_log_output_match_count(_log_pattern)
    third_party_user_extension_logger.clear_log_output_match_count()
    if count == 1:
        return
    message = (
        f"'{_log_pattern}' should be logged once, but it was logged {count} times."
    )
    raise AssertionError(message)


class Vrm1ImportUserExtension:
    def post_import_hook(
        self,
        _arg1: object,
        _arg2: object,
        _arg3: object,
        _arg4: object,
        _arg5: object,
        _arg6: object,
        _arg7: object,
        _arg8: object,
        _arg9: object,
        _arg10: object,
        _arg11: object,
        _arg12: object,
        _arg13: object,
        _arg14: object,
        _arg15: object,
    ) -> None:
        pass
