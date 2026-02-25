#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import logging
import re
import shutil
import sys
import tempfile
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional

from bpy.types import (
    ID,
    Operator,
)

from io_scene_vrm import registration
from io_scene_vrm.common import convert, convert_any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def write_property_typing(
    property_name: str,
    property_type: str,
    keywords: dict[str, object],
) -> tuple[str, Optional[str], Optional[str]]:
    arg_line = None
    arg_call_line = None
    arg_type = None
    arg_default: object = None

    logger.info("  ==> prop=%s", property_name)
    ruff_line_len = 88
    comment = "  # type: ignore[no-redef]"
    if property_name == "stiffiness" or property_name.endswith("_ussage_name"):
        comment += "  # noqa: SC200"

    if property_type in ["bpy.props.StringProperty", "bpy.props.EnumProperty"]:
        line = f"        {property_name}: str{comment}"
        arg_type = "str"
        arg_default = '""'
    elif property_type == "bpy.props.FloatProperty":
        line = f"        {property_name}: float{comment}"
        arg_type = "float"
        arg_default = 0.0
    elif property_type == "bpy.props.FloatVectorProperty":
        line = f"        {property_name}: Sequence[float]{comment}"
        if len(line) > ruff_line_len:
            line = (
                f"        {property_name}: ({comment}\n"
                "            Sequence[float]\n        )"
            )
    elif property_type == "bpy.props.IntProperty":
        line = f"        {property_name}: int{comment}"
        arg_type = "int"
        arg_default = 0
    elif property_type == "bpy.props.IntVectorProperty":
        line = f"        {property_name}: Sequence[int]{comment}"
        if len(line) > ruff_line_len:
            line = (
                f"        {property_name}: ({comment}\n"
                "            Sequence[int]\n        )"
            )
    elif property_type == "bpy.props.BoolProperty":
        line = f"        {property_name}: bool{comment}"
        arg_type = "bool"
        arg_default = "False"
    elif property_type == "bpy.props.BoolVectorProperty":
        line = f"        {property_name}: Sequence[bool]{comment}"
        if len(line) > ruff_line_len:
            line = (
                f"        {property_name}: ({comment}\n"
                "            Sequence[bool]\n        )"
            )
    elif property_type == "bpy.props.PointerProperty":
        target_type = keywords.get("type")
        if not isinstance(target_type, type):
            message = f"Unexpected {keywords}"
            raise AssertionError(message)
        if issubclass(target_type, ID):
            target_name = f"Optional[{target_type.__name__}]"
        else:
            target_name = target_type.__name__
        line = f"        {property_name}: {target_name}{comment}"
        if len(line) > ruff_line_len:
            line = (
                f"        {property_name}: ({comment}\n"
                + f"            {target_name}\n"
                + "        )"
            )
    elif property_type == "bpy.props.CollectionProperty":
        target_type = keywords.get("type")
        if not isinstance(target_type, type):
            message = f"Unexpected {keywords}"
            raise AssertionError(message)
        if issubclass(target_type, ID):
            target_name = f"Optional[{target_type.__name__}]"
        else:
            target_name = target_type.__name__
        line = (
            f"        {property_name}: CollectionPropertyProtocol[{comment}\n"
            + f"            {target_name}\n"
            + "        ]"
        )
        arg_type = "Optional[Sequence[Mapping[str, Union[str, int, float, bool]]]]"
        arg_default = None
        arg_call_line = (
            f"{property_name}={property_name} if {property_name} is not None else []"
        )
    elif property_type.startswith("bpy.props."):
        line = f"        # TODO: {property_name} {property_type}"
    else:
        return ("", None, None)

    line += "\n"

    if arg_type is not None and property_name != "armature_name":
        arg_default_param = keywords.get("default")
        if arg_default_param is not None:
            arg_default = arg_default_param
            if isinstance(arg_default, str):
                if len(property_name) + len(arg_type) + len(arg_default) + 12 < 89:
                    arg_default = f'"{arg_default}"'
                else:
                    arg_default = f'"{arg_default[:63]}" "{arg_default[63:]}"'
        arg_line = f"    {property_name}: {arg_type} = {arg_default},"

    return (line, arg_line, arg_call_line)


def update_property_typing(
    current_class: type,
    typing_code: str,
    output_folder_path: Path,
    *,
    more: bool,
) -> None:
    if not typing_code:
        logger.info(" ==> NO CODE")
        return

    logger.info(
        "------------------------------------------\n%s\n%s",
        current_class,
        typing_code,
    )

    # Find the corresponding file
    modules = current_class.__module__.split(".")
    if any(not module.isidentifier() for module in modules):
        message = f"Unexpected module: {current_class.__module__}"
        raise AssertionError(message)
    if modules[0] != "io_scene_vrm":
        logger.info("Skipping module: %s", modules[0])
        return

    relative_path = Path(*modules).with_suffix(".py")
    input_path = Path(__file__).parent.parent / "src" / relative_path
    output_path = output_folder_path / relative_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("%s -> %s", input_path, output_path)

    # Find the definition location of the corresponding class
    lines = input_path.read_text(encoding="UTF-8").splitlines()
    # Skip to the definition of the corresponding class

    class_def_index: Optional[int] = None
    class_def_colon_index: Optional[int] = None
    class_type_checking_index: Optional[int] = None
    another_def_start_index: Optional[int] = None
    for line_index, line in enumerate(lines):
        if class_def_index is None:
            # Find class definition
            pattern = "^class " + current_class.__name__ + "[^a-zA-Z0-9_]"
            if re.search(pattern, line):
                logger.info("class def found %s", class_def_index)
                class_def_index = line_index
            else:
                continue

        if class_def_colon_index is None:
            # Find colon
            if ":" in line.split("#")[0]:
                logger.info("class colon def found %s", class_def_colon_index)
                class_def_colon_index = line_index
                continue
            continue

        # Find `if TYPE_CHECKING:`
        if re.search("^    if TYPE_CHECKING:", line):
            class_type_checking_index = line_index
        elif class_type_checking_index is not None and re.search(
            "^    [a-zA-Z#]", line
        ):
            # Reset `if TYPE_CHECKING:` if something else is found after it
            class_type_checking_index = None

        if re.search(r"^\S", line):
            another_def_start_index = line_index
            break

    if not class_def_colon_index:
        message = "Not found"
        raise AssertionError(message)

    if not another_def_start_index:
        another_def_start_index = len(lines) + 1

    if class_type_checking_index is not None:
        logger.info(
            "REMOVE: %s - %s", another_def_start_index, class_type_checking_index
        )
        for _ in range(another_def_start_index - class_type_checking_index - 1):
            if class_type_checking_index >= len(lines):
                break
            del lines[class_type_checking_index]
            another_def_start_index -= 1

    lines.insert(
        another_def_start_index - 1,
        "    if TYPE_CHECKING:\n"
        + "        # This code is auto generated.\n"
        + "        # To regenerate, run the"
        + " `uv run tools/property_typing.py` command.\n"
        + typing_code,
    )

    if more:
        lines.insert(
            class_def_colon_index + 1,
            "    if TYPE_CHECKING:\n"
            + typing_code.replace("# type: ignore[no-redef]", ""),
        )

    output_path.write_bytes(str.join("\n", lines).encode().strip() + b"\n")


def generate_property_typing_code(output_folder_path: Path, *, more: bool) -> int:
    ops_folder_path = output_folder_path / "io_scene_vrm" / "common" / "ops"

    classes = list(registration.classes)
    searching_classes = list(registration.classes)
    while searching_classes:
        current_class = searching_classes.pop()
        logger.info("Searching %s", current_class)
        for base_class in current_class.__bases__:
            logger.info("++ Searching %s", base_class)
            if base_class not in classes and base_class not in searching_classes:
                searching_classes.append(base_class)
        if current_class not in classes:
            classes.append(current_class)
    for current_class in classes:
        logger.info("##### %s #####", current_class)
        ops_path = None
        ops_code = ""
        ops_code_sep = False
        bl_idname: object = ""
        if issubclass(current_class, Operator):
            logger.info("##### ops #####")
            bl_idname = convert_any.to_object(getattr(current_class, "bl_idname", None))
            if isinstance(bl_idname, str):
                modules = bl_idname.split(".")
                if any(not module.isidentifier() for module in modules):
                    message = f"Unexpected bl_idname: {bl_idname}"
                    raise AssertionError(message)
                method = modules.pop()
                ops_path = ops_folder_path / Path(*modules).with_suffix(".py")
                logger.info("%s", ops_path)
                ops_code = (
                    "# This code is auto generated.\n"
                    + "# To regenerate, run the"
                    + " `uv run tools/property_typing.py` command.\n"
                    + f"def {method}(\n"
                    + '    execution_context: str = "EXEC_DEFAULT",\n'
                )
        ops_params: list[str] = []
        code = ""

        collected_classes: list[type] = []
        searching_hierarchy_classes: list[type] = [current_class]
        while searching_hierarchy_classes:
            current_hierarchy_class = searching_hierarchy_classes.pop()
            if current_hierarchy_class in collected_classes:
                continue
            collected_classes.append(current_hierarchy_class)
            searching_hierarchy_classes.extend(current_hierarchy_class.__bases__)

        processed_keys: list[str] = []
        for inspected_class in collected_classes:
            annotations = convert.mapping_or_none(
                getattr(inspected_class, "__annotations__", None)
            )
            if annotations is None:
                continue
            for property_key, property_value in annotations.items():
                if not isinstance(property_key, str):
                    raise TypeError
                if property_key in processed_keys:
                    continue
                function: object = getattr(property_value, "function", None)
                if function is None:
                    continue
                function_name = getattr(function, "__qualname__", None)
                if function_name is None:
                    continue

                keywords = convert.mapping_or_none(
                    getattr(property_value, "keywords", None)
                )
                if keywords is None:
                    continue
                typed_keywords: dict[str, object] = {
                    keyword_key: keyword_value
                    for keyword_key, keyword_value in keywords.items()
                    if isinstance(keyword_key, str)
                }
                code_line, ops_arg_line, ops_call_line = write_property_typing(
                    property_key,
                    f"{function.__module__}.{function_name}",
                    typed_keywords,
                )
                if current_class == inspected_class:
                    code += code_line
                if ops_path is not None and ops_arg_line is not None:
                    if not ops_code_sep:
                        ops_code += "    /,\n"
                        ops_code += "    *,\n"
                        ops_code_sep = True
                    if ops_call_line is None:
                        ops_params.append(f"{property_key}={property_key}")
                    else:
                        ops_params.append(ops_call_line)
                    ops_code += ops_arg_line + "\n"
                processed_keys.append(property_key)
        if ops_path is not None:
            ops_code += ") -> set[str]:\n"
            ops_code += (
                f"    return bpy.ops.{bl_idname}("
                + "  # type: ignore[attr-defined, no-any-return]\n"
                + "        execution_context,\n"
            )
            for param in ops_params:
                ops_code += f"        {param},\n"
            ops_code += "    )\n\n\n"
            logger.info("%s", ops_code)
            if not ops_path.exists():
                ops_path.parent.mkdir(parents=True, exist_ok=True)
                ops_code = (
                    "# This code is auto generated.\n"
                    + "# To regenerate, run the"
                    + " `uv run tools/property_typing.py` command.\n\n"
                    + "from collections.abc import Mapping, Sequence\n"
                    + "from typing import Optional, Union\n\n"
                    + "import bpy\n\n\n"
                ) + ops_code
            if ops_path.exists():
                ops_code = ops_path.read_text() + ops_code
            ops_path.write_text(ops_code)
        update_property_typing(current_class, code, output_folder_path, more=more)
    return 0


def main() -> int:
    argument_parser = ArgumentParser()
    argument_parser.add_argument("--more", action="store_true", dest="more")
    args = argument_parser.parse_args()
    more: bool = args.more

    with tempfile.TemporaryDirectory() as temp_folder_path_str:
        output_folder_path = Path(temp_folder_path_str) / "output"
        code_generation_result = generate_property_typing_code(
            output_folder_path, more=more
        )
        if code_generation_result != 0:
            return code_generation_result

        src_folder_path = Path(__file__).parent.parent / "src"
        ops_folder_path = src_folder_path / "io_scene_vrm" / "common" / "ops"
        for ops_py_path in ops_folder_path.glob("*.py"):
            if ops_py_path.name != "__init__.py":
                ops_py_path.unlink()

        shutil.copytree(output_folder_path, src_folder_path, dirs_exist_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
