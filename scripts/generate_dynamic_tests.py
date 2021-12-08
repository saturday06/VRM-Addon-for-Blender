#!/usr/bin/env python3

import contextlib
import importlib
import os
import re
import uuid
from pathlib import Path
from typing import Any, Optional


def to_function_component_literal(s: str) -> str:
    ascii_lower = "abcdefghijklmnopqrstuvwxyz0123456789"
    ascii_upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    # str.lower() is locale dependent
    # https://stackoverflow.com/questions/19030948/python-utf-8-lowercase-turkish-specific-letter
    ascii_upper_to_lower = dict(zip(ascii_upper, ascii_lower))
    return "".join(
        map(
            lambda c: c
            if c in ascii_lower
            else ascii_upper_to_lower[c]
            if c in ascii_upper
            else "_",
            s,
        )
    )


test_src_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests")
for path in sorted(os.listdir(test_src_dir)):
    if not path.startswith("blender_test_") or not path.endswith(".py"):
        continue
    out_path = os.path.join(
        test_src_dir, re.sub("^blender_test_", "test_GENERATED_", path)
    )
    path_without_ext = re.sub("\\.py$", "", path)
    class_name = "".join(
        word.title()
        for word in re.sub("blender_test_", "", path_without_ext).split("_")
    )
    import_exception: Optional[BaseException] = None
    test_command_args_list: Any = []
    try:
        # pylint: disable=no-value-for-parameter,deprecated-method
        m = importlib.machinery.SourceFileLoader(
            "blender_vrm_addon_base_blender_test_case_generate_blender_test_case__"
            + path_without_ext,
            os.path.join(test_src_dir, path),
        ).load_module()
        # pylint: enable=no-value-for-parameter,deprecated-method
        with contextlib.suppress(AttributeError):
            func = getattr(m, "get_test_command_args")  # noqa: B009
            if callable(func):
                test_command_args_list = func()
    except BaseException as e:
        import_exception = e

    content = f"""#
# This source file is machine generated. Please don't edit it
#

from .base_blender_test_case import BaseBlenderTestCase


class Blender{class_name}TestCase(BaseBlenderTestCase):
    def __init__(self, *args: str, **kwargs: str) -> None:
        # https://stackoverflow.com/a/19102520
        super().__init__(*args, **kwargs)

    def test_health_check(self) -> None:
        self.assertTrue(True)
"""
    if import_exception is not None:
        content += f"""
##### ERROR #####
# {import_exception}
"""
    elif test_command_args_list:
        existing_method_names = []
        for args in test_command_args_list:
            default_method_name = "_".join(map(to_function_component_literal, args))
            method_name = default_method_name
            for index in range(1000000):
                if index > 0:
                    method_name = f"{default_method_name}_{index}"
                if method_name not in existing_method_names:
                    break
            if method_name in existing_method_names:
                raise Exception(f"Test method name {method_name}_index is duplicated")
            existing_method_names.append(method_name)

            escaped = list(map(lambda a: fr"{a}", [path] + args))
            args_str = '"' + '", "'.join(escaped) + '"'
            content += f"""
    def test_{method_name}(self) -> None:
        self.run_script({args_str})
"""
    else:
        content += f"""
    def test_main(self) -> None:
        self.run_script("{path}")
"""

    content_bytes = content.replace("\r\n", "\n").encode()
    if os.path.exists(out_path) and content_bytes == Path(out_path).read_bytes():
        continue

    # It should be an atomic operation
    temp_out_path = f"{out_path}.{uuid.uuid4().hex}.temp"
    Path(temp_out_path).write_bytes(content_bytes)
    os.replace(temp_out_path, out_path)
