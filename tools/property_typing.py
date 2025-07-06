#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import logging
import re
import sys
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

RUFF_LINE_LENGTH_LIMIT = 88
LONG_STRING_SPLIT_THRESHOLD = 89
STRING_TRUNCATION_LENGTH = 63
TYPE_IGNORE_COMMENT = "  # type: ignore[no-redef]"
SPELLCHECK_IGNORE_COMMENT = "  # noqa: SC200"


def _handle_string_property(property_name: str) -> tuple[str, str, str]:
    """Handle StringProperty and EnumProperty types."""
    comment = TYPE_IGNORE_COMMENT
    if property_name == "stiffiness" or property_name.endswith("_ussage_name"):
        comment += SPELLCHECK_IGNORE_COMMENT

    line = f"        {property_name}: str{comment}"
    return line, "str", '""'


def _handle_float_property(property_name: str) -> tuple[str, str, float]:
    """Handle FloatProperty type."""
    comment = TYPE_IGNORE_COMMENT
    if property_name == "stiffiness" or property_name.endswith("_ussage_name"):
        comment += SPELLCHECK_IGNORE_COMMENT

    line = f"        {property_name}: float{comment}"
    return line, "float", 0.0


def _handle_float_vector_property(property_name: str) -> str:
    """Handle FloatVectorProperty type."""
    comment = TYPE_IGNORE_COMMENT
    if property_name == "stiffiness" or property_name.endswith("_ussage_name"):
        comment += SPELLCHECK_IGNORE_COMMENT

    line = f"        {property_name}: Sequence[float]{comment}"
    if len(line) > RUFF_LINE_LENGTH_LIMIT:
        line = (
            f"        {property_name}: ({comment}\n"
            "            Sequence[float]\n"
            "        )"
        )
    return line


def _handle_int_property(property_name: str) -> tuple[str, str, int]:
    """Handle IntProperty type."""
    comment = TYPE_IGNORE_COMMENT
    if property_name == "stiffiness" or property_name.endswith("_ussage_name"):
        comment += SPELLCHECK_IGNORE_COMMENT

    line = f"        {property_name}: int{comment}"
    return line, "int", 0


def _handle_int_vector_property(property_name: str) -> str:
    """Handle IntVectorProperty type."""
    comment = TYPE_IGNORE_COMMENT
    if property_name == "stiffiness" or property_name.endswith("_ussage_name"):
        comment += SPELLCHECK_IGNORE_COMMENT

    line = f"        {property_name}: Sequence[int]{comment}"
    if len(line) > RUFF_LINE_LENGTH_LIMIT:
        line = (
            f"        {property_name}: ({comment}\n            Sequence[int]\n        )"
        )
    return line


def _handle_bool_property(property_name: str) -> tuple[str, str, str]:
    """Handle BoolProperty type."""
    comment = TYPE_IGNORE_COMMENT
    if property_name == "stiffiness" or property_name.endswith("_ussage_name"):
        comment += SPELLCHECK_IGNORE_COMMENT

    line = f"        {property_name}: bool{comment}"
    return line, "bool", "False"


def _handle_bool_vector_property(property_name: str) -> str:
    """Handle BoolVectorProperty type."""
    comment = TYPE_IGNORE_COMMENT
    if property_name == "stiffiness" or property_name.endswith("_ussage_name"):
        comment += SPELLCHECK_IGNORE_COMMENT

    line = f"        {property_name}: Sequence[bool]{comment}"
    if len(line) > RUFF_LINE_LENGTH_LIMIT:
        line = (
            f"        {property_name}: ({comment}\n"
            "            Sequence[bool]\n"
            "        )"
        )
    return line


def _handle_pointer_property(property_name: str, keywords: dict[str, object]) -> str:
    """Handle PointerProperty type."""
    target_type = keywords.get("type")
    if not isinstance(target_type, type):
        message = (
            f"Unexpected keywords for PointerProperty '{property_name}': {keywords}"
        )
        raise TypeError(message)

    if issubclass(target_type, ID):
        target_name = f"Optional[{target_type.__name__}]"
    else:
        target_name = target_type.__name__

    comment = TYPE_IGNORE_COMMENT
    if property_name == "stiffiness" or property_name.endswith("_ussage_name"):
        comment += SPELLCHECK_IGNORE_COMMENT

    line = f"        {property_name}: {target_name}{comment}"
    if len(line) > RUFF_LINE_LENGTH_LIMIT:
        line = (
            f"        {property_name}: ({comment}\n"
            + f"            {target_name}\n"
            + "        )"
        )
    return line


def _handle_collection_property(
    property_name: str, keywords: dict[str, object]
) -> tuple[str, str, Optional[object], str]:
    """Handle CollectionProperty type."""
    target_type = keywords.get("type")
    if not isinstance(target_type, type):
        message = (
            f"Unexpected keywords for CollectionProperty '{property_name}': {keywords}"
        )
        raise TypeError(message)

    if issubclass(target_type, ID):
        target_name = f"Optional[{target_type.__name__}]"
    else:
        target_name = target_type.__name__

    comment = TYPE_IGNORE_COMMENT
    if property_name == "stiffiness" or property_name.endswith("_ussage_name"):
        comment += SPELLCHECK_IGNORE_COMMENT

    line = (
        f"        {property_name}: CollectionPropertyProtocol[{comment}\n"
        + f"            {target_name}\n"
        + "        ]"
    )
    arg_type = "Optional[Sequence[Mapping[str, Union[str, int, float, bool]]]]"
    arg_default = None
    arg_call_line = (
        f"{property_name}={property_name} if {property_name} is not None else " + "[]"
    )

    return line, arg_type, arg_default, arg_call_line


def write_property_typing(
    property_name: str,
    property_type: str,
    keywords: dict[str, object],
) -> tuple[str, Optional[str], Optional[str]]:
    """Generate type annotations for Blender property types.

    Args:
        property_name: Name of the property
        property_type: Full qualified name of the property type
        keywords: Property configuration keywords

    Returns:
        Tuple of (type_annotation_line, argument_line, argument_call_line)
    """
    arg_line = None
    arg_call_line = None
    arg_type = None
    arg_default: object = None

    logger.info("  ==> prop=%s", property_name)

    if property_type in ["bpy.props.StringProperty", "bpy.props.EnumProperty"]:
        line, arg_type, arg_default = _handle_string_property(property_name)
    elif property_type == "bpy.props.FloatProperty":
        line, arg_type, arg_default = _handle_float_property(property_name)
    elif property_type == "bpy.props.FloatVectorProperty":
        line = _handle_float_vector_property(property_name)
    elif property_type == "bpy.props.IntProperty":
        line, arg_type, arg_default = _handle_int_property(property_name)
    elif property_type == "bpy.props.IntVectorProperty":
        line = _handle_int_vector_property(property_name)
    elif property_type == "bpy.props.BoolProperty":
        line, arg_type, arg_default = _handle_bool_property(property_name)
    elif property_type == "bpy.props.BoolVectorProperty":
        line = _handle_bool_vector_property(property_name)
    elif property_type == "bpy.props.PointerProperty":
        line = _handle_pointer_property(property_name, keywords)
    elif property_type == "bpy.props.CollectionProperty":
        line, arg_type, arg_default, arg_call_line = _handle_collection_property(
            property_name, keywords
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
                total_length = (
                    len(property_name) + len(arg_type) + len(arg_default) + 12
                )
                if total_length < LONG_STRING_SPLIT_THRESHOLD:
                    arg_default = f'"{arg_default}"'
                else:
                    truncated_part = arg_default[:STRING_TRUNCATION_LENGTH]
                    remaining_part = arg_default[STRING_TRUNCATION_LENGTH:]
                    arg_default = f'"{truncated_part}" "{remaining_part}"'
        arg_line = f"    {property_name}: {arg_type} = {arg_default},"

    return (line, arg_line, arg_call_line)


def update_property_typing(
    class_type: type,
    typing_code: str,
    *,
    more: bool,
) -> None:
    """Update the type annotations in the source file for the given class.

    Args:
        class_type: The class to update type annotations for
        typing_code: The generated type annotation code
        more: Whether to add additional type checking blocks
    """
    if not typing_code:
        logger.info(" ==> NO CODE")
        return

    logger.info(
        "------------------------------------------\n%s\n%s",
        class_type,
        typing_code,
    )

    # Find the corresponding source file
    module_path = _find_source_file_path(class_type)
    if module_path is None:
        return

    logger.info("%s", module_path)

    lines = module_path.read_text(encoding="UTF-8").splitlines()

    # Find class definition and insertion points
    class_indices = _find_class_definition_indices(lines, class_type.__name__)
    if class_indices is None:
        return

    class_def_colon_index, class_type_checking_index, another_def_start_index = (
        class_indices
    )

    if class_type_checking_index is not None:
        _remove_existing_type_checking_block(
            lines, class_type_checking_index, another_def_start_index
        )
        class_indices = _find_class_definition_indices(lines, class_type.__name__)
        if class_indices is None:
            return
        class_def_colon_index, _, another_def_start_index = class_indices

    _insert_type_checking_block(lines, another_def_start_index, typing_code)

    if more:
        _insert_additional_type_checking_block(
            lines, class_def_colon_index, typing_code
        )

    module_path.write_bytes(str.join("\n", lines).encode())


def _find_source_file_path(class_type: type) -> Optional[Path]:
    """Find the source file path for the given class."""
    modules = class_type.__module__.split(".")
    modules.reverse()
    module = modules.pop()
    if module != "io_scene_vrm":
        logger.info("Unexpected module: %s", module)
        return None

    path = Path(__file__).parent.parent / "src" / "io_scene_vrm"
    while modules:
        module = modules.pop()
        path = path / module
    return path.with_suffix(".py")


def _find_class_definition_indices(
    lines: list[str], class_name: str
) -> Optional[tuple[int, Optional[int], int]]:
    """Find indices for class definition, TYPE_CHECKING block, and next definition."""
    class_def_index = None
    class_def_colon_index = None
    class_type_checking_index = None
    another_def_start_index = None

    for line_index, line in enumerate(lines):
        if class_def_index is None:
            # Find class definition
            pattern = "^class " + class_name + "[^a-zA-Z0-9_]"
            if re.match(pattern, line):
                logger.info("class def found %s", line_index)
                class_def_index = line_index
                continue

        if class_def_colon_index is None and re.match(".*:", line.split("#")[0]):
            # Find colon ending class definition
            logger.info("class colon def found %s", line_index)
            class_def_colon_index = line_index
            continue

        if re.match("^    if TYPE_CHECKING:", line):
            class_type_checking_index = line_index
        elif class_type_checking_index is not None and re.match("^    [a-zA-Z#]", line):
            # Reset TYPE_CHECKING if something else is found after it
            class_type_checking_index = None

        if re.match(r"^\S", line):
            another_def_start_index = line_index
            break

    if class_def_colon_index is None:
        message = f"Class definition colon not found for {class_name}"
        raise AssertionError(message)

    if another_def_start_index is None:
        another_def_start_index = len(lines) + 1

    return class_def_colon_index, class_type_checking_index, another_def_start_index


def _remove_existing_type_checking_block(
    lines: list[str], class_type_checking_index: int, another_def_start_index: int
) -> None:
    """Remove existing TYPE_CHECKING block from the lines."""
    logger.info("REMOVE: %s - %s", another_def_start_index, class_type_checking_index)
    removal_count = another_def_start_index - class_type_checking_index - 1
    for _ in range(removal_count):
        if class_type_checking_index >= len(lines):
            break
        del lines[class_type_checking_index]


def _insert_type_checking_block(
    lines: list[str], another_def_start_index: int, typing_code: str
) -> None:
    """Insert the main TYPE_CHECKING block."""
    type_checking_block = (
        "    if TYPE_CHECKING:\n"
        + "        # This code is auto generated.\n"
        + "        # To regenerate, run the"
        + " `uv run tools/property_typing.py` command.\n"
        + typing_code
    )
    lines.insert(another_def_start_index - 1, type_checking_block)


def _insert_additional_type_checking_block(
    lines: list[str], class_def_colon_index: int, typing_code: str
) -> None:
    """Insert additional TYPE_CHECKING block when 'more' option is enabled."""
    additional_block = "    if TYPE_CHECKING:\n" + typing_code.replace(
        "# type: ignore[no-redef]", ""
    )
    lines.insert(class_def_colon_index + 1, additional_block)


def _collect_all_classes() -> list[type]:
    """Collect all classes including base classes from registration."""
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

    return classes


def _generate_operator_code(
    class_type: type, ops_dir: Path
) -> tuple[Optional[Path], str, list[str]]:
    """Generate operator code for Blender operators."""
    ops_path = None
    ops_code = ""
    ops_params: list[str] = []

    if not issubclass(class_type, Operator):
        return ops_path, ops_code, ops_params

    logger.info("##### ops #####")
    bl_idname = convert_any.to_object(getattr(class_type, "bl_idname", None))

    if not isinstance(bl_idname, str):
        return ops_path, ops_code, ops_params

    identifier_parts = bl_idname.split(".")
    method_name = identifier_parts.pop()
    ops_path = ops_dir / Path(*identifier_parts).with_suffix(".py")
    logger.info("%s", ops_path)

    ops_code = (
        "# This code is auto generated.\n"
        + "# To regenerate, run the"
        + " `uv run tools/property_typing.py` command.\n"
        + f"def {method_name}(\n"
        + '    execution_context: str = "EXEC_DEFAULT",\n'
    )

    return ops_path, ops_code, ops_params


def _process_class_annotations(
    class_type: type,
    ops_path: Optional[Path],
    ops_code: str,
    ops_params: list[str],
) -> tuple[str, str, list[str]]:
    """Process annotations for a class and its base classes."""
    class_hierarchy: list[type] = []
    searching_classes: list[type] = [class_type]

    while searching_classes:
        current_class = searching_classes.pop()
        if current_class in class_hierarchy:
            continue
        class_hierarchy.append(current_class)
        searching_classes.extend(current_class.__bases__)

    processed_properties: list[str] = []
    type_annotation_code = ""
    ops_code_separator_added = False

    for hierarchy_class in class_hierarchy:
        annotations = convert.mapping_or_none(
            getattr(hierarchy_class, "__annotations__", None)
        )
        if annotations is None:
            continue

        for property_name, property_value in annotations.items():
            if not isinstance(property_name, str):
                error_message = (
                    f"Property name must be string, got {type(property_name).__name__}"
                )
                raise TypeError(error_message)

            if property_name in processed_properties:
                continue

            function = getattr(property_value, "function", None)
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
                key: value for key, value in keywords.items() if isinstance(key, str)
            }

            code_line, ops_arg_line, ops_call_line = write_property_typing(
                property_name,
                f"{function.__module__}.{function_name}",
                typed_keywords,
            )

            if class_type == hierarchy_class:
                type_annotation_code += code_line

            if ops_path is not None and ops_arg_line is not None:
                if not ops_code_separator_added:
                    ops_code += "    /,\n"
                    ops_code += "    *,\n"
                    ops_code_separator_added = True

                if ops_call_line is None:
                    ops_params.append(f"{property_name}={property_name}")
                else:
                    ops_params.append(ops_call_line)

                ops_code += ops_arg_line + "\n"

            processed_properties.append(property_name)

    return type_annotation_code, ops_code, ops_params


def _finalize_operator_code(
    ops_path: Optional[Path],
    ops_code: str,
    ops_params: list[str],
    bl_idname: str,
) -> None:
    """Finalize and write operator code to file."""
    if ops_path is None:
        return

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
        header_content = (
            "# This code is auto generated.\n"
            + "# To regenerate, run the"
            + " `uv run tools/property_typing.py` command.\n\n"
            + "from collections.abc import Mapping, Sequence\n"
            + "from typing import Optional, Union\n\n"
            + "import bpy\n\n\n"
        )
        ops_path.write_text(header_content)

    ops_path.write_text(ops_path.read_text() + ops_code)


def main() -> int:
    """Generate type annotations for VRM addon classes."""
    argument_parser = ArgumentParser()
    argument_parser.add_argument("--more", action="store_true", dest="more")
    args = argument_parser.parse_args()
    more: bool = args.more

    ops_dir = Path(__file__).parent.parent / "src" / "io_scene_vrm" / "common" / "ops"
    for generated_py_path in ops_dir.glob("*.py"):
        if generated_py_path.name != "__init__.py":
            generated_py_path.unlink()

    classes = _collect_all_classes()

    for class_type in classes:
        logger.info("##### %s #####", class_type)

        ops_path, ops_code, ops_params = _generate_operator_code(class_type, ops_dir)

        type_annotation_code, ops_code, ops_params = _process_class_annotations(
            class_type, ops_path, ops_code, ops_params
        )

        if ops_path is not None:
            bl_idname = convert_any.to_object(getattr(class_type, "bl_idname", ""))
            if isinstance(bl_idname, str):
                _finalize_operator_code(ops_path, ops_code, ops_params, bl_idname)

        update_property_typing(class_type, type_annotation_code, more=more)

    return 0


if __name__ == "__main__":
    sys.exit(main())
