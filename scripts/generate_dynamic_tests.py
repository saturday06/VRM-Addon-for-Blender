#!/usr/bin/env python3

import contextlib
import importlib
import os
import re
import uuid
from pathlib import Path
from typing import Any, Optional


def to_function_component_literal(s: str) -> str:
    permitted = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(
        map(
            lambda c: c if c in permitted else "_",
            # str.lower() is locale dependent. bytes.lower() is locale independent.
            s.encode().lower().decode(),
        )
    )


test_src_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests")
for path in map(str.strip, sorted(os.listdir(test_src_dir))):
    if not path.startswith("blender_test_") or not path.endswith(".py"):
        continue
    out_path = os.path.join(
        test_src_dir, re.sub("^blender_test_", "test_GENERATED_", path)
    )
    path_without_ext = re.sub("\\.py$", "", path)
    if not re.match("^[A-Za-z0-9_]+$", path_without_ext):
        raise Exception(f"Invalid file name: {path}")
    class_name = "".join(
        word.title()
        for word in re.sub("blender_test_", "", path_without_ext).split("_")
    )
    import_exception_str: Optional[str] = None
    test_command_args_list: Any = []
    try:
        for d in ["vrm", "blend"]:
            resources_dir = os.environ.get(
                "BLENDER_VRM_TEST_RESOURCES_PATH",
                os.path.join(test_src_dir, "resources"),
            )
            if not os.path.exists(os.path.join(resources_dir, d)):
                raise Exception(f"'./tests/resources/{d}/' doesn't exist.")

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
        import_exception_str = fr"{e}".replace('"', '\\"')

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
    if import_exception_str is not None:
        content += f"""
    def test_dynamic_test_case_generation_failed(self) -> None:
        self.fail(r\"""Exception: {import_exception_str}

This error is often caused by the absence of its submodule.
If so please run `git submodule update --init`.\""")
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
