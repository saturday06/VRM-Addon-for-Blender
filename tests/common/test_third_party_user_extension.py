# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from types import ModuleType
from unittest import TestCase

from io_scene_vrm.common.third_party_user_extension import (
    _logger,
    get_third_party_user_extension_name,
    trigger_third_party_user_extension_hook,
)


class TestThirdPartyUserExtension(TestCase):
    def test_get_version_of_module_without_file(self) -> None:
        module = ModuleType("test_module_without_file")

        self.assertIsNone(get_third_party_user_extension_name(module))

    def test_hook_with_too_few_arguments(self) -> None:
        class UserExtension:
            def hook(self, first: object, second: object) -> None:
                del first, second
                raise AssertionError

        pattern = "the callback requires 2 arguments, but only 1 is available"
        _logger.clear_log_output_match_count()
        _logger.register_log_output_match(pattern)
        try:
            trigger_third_party_user_extension_hook([UserExtension()], "hook", object())
            self.assertEqual(_logger.get_log_output_match_count(pattern), 1)
        finally:
            _logger.clear_log_output_match_count()

    def test_hook_ignores_extra_arguments(self) -> None:
        received_args: list[object] = []

        class UserExtension:
            def hook(self, arg: object) -> None:
                received_args.append(arg)

        first_arg = object()
        trigger_third_party_user_extension_hook(
            [UserExtension()], "hook", first_arg, object()
        )

        self.assertEqual(received_args, [first_arg])
