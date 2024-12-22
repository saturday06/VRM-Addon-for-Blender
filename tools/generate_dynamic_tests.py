#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import re
import sys
import uuid
from base64 import urlsafe_b64encode
from importlib.util import module_from_spec, spec_from_file_location
from os import environ
from pathlib import Path

# This is not necessary if executed from uv
sys.path.append(str(Path(__file__).parent.parent / "src"))


from io_scene_vrm.common import convert, convert_any


def to_function_component_literal(s: object) -> str:
    if not isinstance(s, str):
        return "_invalid_str_error_"
    permitted = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(
        c if c in permitted else "_"
        # str.lower() is locale dependent. bytes.lower() is locale independent.
        for c in s.encode().lower().decode()
    )


def render_single_test(path: str) -> str:
    path = urlsafe_b64encode(path.encode()).decode()
    return f"""
    def test_main(self) -> None:
        self.run_script("{path}")
"""


def render_multiple_test(method_name: str, args_str: str) -> str:
    return f"""
    def test_{method_name}(self) -> None:
        self.run_script({args_str})
"""


def render_missing_required_directory_test(name: str) -> str:
    return f"""
    def test_dynamic_test_case_generation_failed(self) -> None:
        self.fail(r\"Missing required directory: '{name}'.\")
"""


def render_generation_failed_test(e: Exception) -> str:
    import_exception_str = rf"{e}".replace('"', '\\"')
    return f"""
    def test_dynamic_test_case_generation_failed(self) -> None:
        self.fail(r"Exception: {import_exception_str}")
"""


def render_test_header(class_name: str) -> str:
    return f"""#
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


def render_body(test_src_dir: Path, path: str, path_without_ext: str) -> str:
    for d in ["vrm", "blend"]:
        resources_dir = Path(
            environ.get(
                "BLENDER_VRM_TEST_RESOURCES_PATH",
                str(Path(test_src_dir, "resources")),
            )
        )
        if not (resources_dir / d).exists():
            return render_missing_required_directory_test("./tests/resources/{d}/")

    test_command_args_list: object = None
    try:
        spec = spec_from_file_location(
            "blender_vrm_addon_base_blender_test_case_generate_blender_test_case__"
            + path_without_ext,
            test_src_dir / path,
        )
        if spec is None:
            return render_generation_failed_test(
                AssertionError("Failed to create module spec")
            )
        mod = module_from_spec(spec)
        if spec.loader is None:
            return render_generation_failed_test(
                AssertionError("Failed to create module spec loader")
            )
        spec.loader.exec_module(mod)

        func: object = getattr(mod, "get_test_command_args", None)
        if callable(func):
            test_command_args_list = convert_any.to_object(func())
    except Exception as e:  # noqa: BLE001
        return render_generation_failed_test(e)

    test_command_args_list = convert.sequence_or_none(test_command_args_list)
    if test_command_args_list is None:
        return render_single_test(path)

    existing_method_names: list[str] = []
    content = ""
    for args_object in test_command_args_list:
        args = convert.sequence_or_none(args_object)
        if args is None:
            continue

        default_method_name = "_".join(map(to_function_component_literal, args))
        method_name = default_method_name
        for index in range(1000000):
            if index > 0:
                method_name = f"{default_method_name}_{index}"
            if method_name not in existing_method_names:
                break
        if method_name in existing_method_names:
            message = f"Test method name {method_name}_index is duplicated"
            raise ValueError(message)
        existing_method_names.append(method_name)

        escaped = [urlsafe_b64encode(str(a).encode()).decode() for a in [path, *args]]
        args_str = "\n" + "".join(f'            "{e}",\n' for e in escaped) + "        "
        content += render_multiple_test(method_name, args_str)
    return content


def generate_dynamic_test(test_src_dir: Path, path: str) -> None:
    if not path.startswith("blender_test_") or not path.endswith(".py"):
        return
    out_path = test_src_dir / re.sub("^blender_test_", "test_generated_", path)
    path_without_ext = re.sub("\\.py$", "", path)
    if not re.match("^[A-Za-z0-9_]+$", path_without_ext):
        message = f"Invalid file name: {path}"
        raise ValueError(message)
    class_name = "".join(
        word.title()
        for word in re.sub("blender_test_", "", path_without_ext).split("_")
    )
    content = render_test_header(class_name) + render_body(
        test_src_dir, path, path_without_ext
    )
    content_bytes = content.replace("\r\n", "\n").encode()
    if out_path.exists() and content_bytes == out_path.read_bytes():
        return

    # It should be an atomic operation
    temp_out_path = out_path.with_name(out_path.name + f".{uuid.uuid4().hex}.temp")
    temp_out_path.write_bytes(content_bytes)
    Path.replace(temp_out_path, out_path)


def generate_dynamic_tests() -> None:
    test_src_dir = Path(__file__).parent.parent / "tests"
    for path in sorted(test_src_dir.iterdir()):
        generate_dynamic_test(test_src_dir, path.name)


if __name__ in ["__main__", "blender_vrm_addon_run_scripts_generate_dynamic_tests"]:
    generate_dynamic_tests()
    if __name__ == "__main__":
        sys.exit(0)
