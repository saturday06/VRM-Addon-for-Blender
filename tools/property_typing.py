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


def write_property_typing(
    n: str,
    t: str,
    keywords: dict[str, object],
) -> tuple[str, Optional[str], Optional[str]]:
    arg_line = None
    arg_call_line = None
    arg_type = None
    arg_default: object = None

    logger.info("  ==> prop=%s", n)
    ruff_line_len = 88
    comment = "  # type: ignore[no-redef]"
    if n == "stiffiness" or n.endswith("_ussage_name"):
        comment += "  # noqa: SC200"

    if t in ["bpy.props.StringProperty", "bpy.props.EnumProperty"]:
        line = f"        {n}: str{comment}"
        arg_type = "str"
        arg_default = '""'
    elif t == "bpy.props.FloatProperty":
        line = f"        {n}: float{comment}"
        arg_type = "float"
        arg_default = 0.0
    elif t == "bpy.props.FloatVectorProperty":
        line = f"        {n}: Sequence[float]{comment}"
        if len(line) > ruff_line_len:
            line = f"        {n}: ({comment}\n            Sequence[float]\n        )"
    elif t == "bpy.props.IntProperty":
        line = f"        {n}: int{comment}"
        arg_type = "int"
        arg_default = 0
    elif t == "bpy.props.IntVectorProperty":
        line = f"        {n}: Sequence[int]{comment}"
        if len(line) > ruff_line_len:
            line = f"        {n}: ({comment}\n            Sequence[int]\n        )"
    elif t == "bpy.props.BoolProperty":
        line = f"        {n}: bool{comment}"
        arg_type = "bool"
        arg_default = "False"
    elif t == "bpy.props.BoolVectorProperty":
        line = f"        {n}: Sequence[bool]{comment}"
        if len(line) > ruff_line_len:
            line = f"        {n}: ({comment}\n            Sequence[bool]\n        )"
    elif t == "bpy.props.PointerProperty":
        target_type = keywords.get("type")
        if not isinstance(target_type, type):
            message = f"Unexpected {keywords}"
            raise AssertionError(message)
        if issubclass(target_type, ID):
            target_name = f"Optional[{target_type.__name__}]"
        else:
            target_name = target_type.__name__
        line = f"        {n}: {target_name}{comment}"
        if len(line) > ruff_line_len:
            line = (
                f"        {n}: ({comment}\n"
                + f"            {target_name}\n"
                + "        )"
            )
    elif t == "bpy.props.CollectionProperty":
        target_type = keywords.get("type")
        if not isinstance(target_type, type):
            message = f"Unexpected {keywords}"
            raise AssertionError(message)
        if issubclass(target_type, ID):
            target_name = f"Optional[{target_type.__name__}]"
        else:
            target_name = target_type.__name__
        line = (
            f"        {n}: CollectionPropertyProtocol[{comment}\n"
            + f"            {target_name}\n"
            + "        ]"
        )
        arg_type = "Optional[Sequence[Mapping[str, Union[str, int, float, bool]]]]"
        arg_default = None
        arg_call_line = f"{n}={n} if {n} is not None else " + "[]"
    elif t.startswith("bpy.props."):
        line = f"        # TODO: {n} {t}"
    else:
        return ("", None, None)

    line += "\n"

    if arg_type is not None:
        arg_default_param = keywords.get("default")
        if arg_default_param is not None:
            arg_default = arg_default_param
            if isinstance(arg_default, str):
                if len(n) + len(arg_type) + len(arg_default) + 12 < 89:
                    arg_default = f'"{arg_default}"'
                else:
                    arg_default = f'"{arg_default[:63]}" "{arg_default[63:]}"'
        arg_line = f"    {n}: {arg_type} = {arg_default},"

    return (line, arg_line, arg_call_line)


def update_property_typing(
    c: type,
    typing_code: str,
    *,
    more: bool,
) -> None:
    if not typing_code:
        logger.info(" ==> NO CODE")
        return

    logger.info(
        "------------------------------------------\n%s\n%s",
        c,
        typing_code,
    )

    # 該当するファイルを探す
    modules = c.__module__.split(".")
    modules.reverse()
    module = modules.pop()
    if module != "io_scene_vrm":
        logger.info("Unexpected module: %s", module)
        return

    path = Path(__file__).parent.parent / "src" / "io_scene_vrm"
    while modules:
        module = modules.pop()
        path = path / module
    path = path.with_suffix(".py")

    logger.info("%s", path)

    # 該当するクラスの定義の場所を探す
    lines = path.read_text(encoding="UTF-8").splitlines()
    # 該当するクラスの定義まで飛ばす

    class_def_index = None
    class_def_colon_index = None
    class_type_checking_index = None
    another_def_start_index = None
    for line_index, line in enumerate(lines):
        if class_def_index is None:
            # クラス定義を探す
            pattern = "^class " + c.__name__ + "[^a-zA-Z0-9_]"
            if re.match(pattern, line):
                logger.info("class def found %s", class_def_index)
                class_def_index = line_index
            else:
                continue

        if class_def_colon_index is None:
            # : を探す
            if re.match(".*:", line.split("#")[0]):
                logger.info("class colon def found %s", class_def_colon_index)
                class_def_colon_index = line_index
                continue
            continue

        # if TYPE_CHECKING: を探す
        if re.match("^    if TYPE_CHECKING:", line):
            class_type_checking_index = line_index
        elif class_type_checking_index is not None and re.match("^    [a-zA-Z#]", line):
            # if TYPE_CHECKING:が発見されたが、その後何かがあったら無かったことにする
            class_type_checking_index = None

        if re.match(r"^\S", line):
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

    path.write_bytes(str.join("\n", lines).encode())


def main() -> int:
    argument_parser = ArgumentParser()
    argument_parser.add_argument("--more", action="store_true", dest="more")
    args = argument_parser.parse_args()
    more: bool = args.more

    ops_dir = Path(__file__).parent.parent / "src" / "io_scene_vrm" / "common" / "ops"
    for generated_py_path in ops_dir.glob("*.py"):
        if generated_py_path.name != "__init__.py":
            generated_py_path.unlink()

    classes = list(registration.classes)
    searching_classes = list(registration.classes)
    while searching_classes:
        c = searching_classes.pop()
        logger.info("Searching %s", c)
        for b in c.__bases__:
            logger.info("++ Searching %s", b)
            if b not in classes and b not in searching_classes:
                searching_classes.append(b)
        if c not in classes:
            classes.append(c)
    for c in classes:
        logger.info("##### %s #####", c)
        ops_path = None
        ops_code = ""
        ops_code_sep = False
        bl_idname: object = ""
        if issubclass(c, Operator):
            logger.info("##### ops #####")
            bl_idname = convert_any.to_object(getattr(c, "bl_idname", None))
            if isinstance(bl_idname, str):
                dirs = bl_idname.split(".")
                method = dirs.pop()
                ops_path = ops_dir / Path(*dirs).with_suffix(".py")
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

        cs: list[type] = []
        searching_cs: list[type] = [c]
        while searching_cs:
            cc = searching_cs.pop()
            if cc in cs:
                continue
            cs.append(cc)
            searching_cs.extend(cc.__bases__)

        ks: list[str] = []
        for c2 in cs:
            annotations = convert.mapping_or_none(getattr(c2, "__annotations__", None))
            if annotations is None:
                continue
            for k, v in annotations.items():
                if not isinstance(k, str):
                    raise TypeError
                if k in ks:
                    continue
                function: object = getattr(v, "function", None)
                if function is None:
                    continue
                function_name = getattr(function, "__qualname__", None)
                if function_name is None:
                    continue

                keywords = convert.mapping_or_none(getattr(v, "keywords", None))
                if keywords is None:
                    continue
                typed_keywords: dict[str, object] = {
                    typed_k: typed_v
                    for typed_k, typed_v in keywords.items()
                    if isinstance(typed_k, str)
                }
                code_line, ops_arg_line, ops_call_line = write_property_typing(
                    k,
                    f"{function.__module__}.{function_name}",
                    typed_keywords,
                )
                if c == c2:
                    code += code_line
                if ops_path is not None and ops_arg_line is not None:
                    if not ops_code_sep:
                        ops_code += "    /,\n"
                        ops_code += "    *,\n"
                        ops_code_sep = True
                    if ops_call_line is None:
                        ops_params.append(f"{k}={k}")
                    else:
                        ops_params.append(ops_call_line)
                    ops_code += ops_arg_line + "\n"
                ks.append(k)
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
                ops_path.write_text(
                    "# This code is auto generated.\n"
                    + "# To regenerate, run the"
                    + " `uv run tools/property_typing.py` command.\n\n"
                    + "from collections.abc import Mapping, Sequence\n"
                    + "from typing import Optional, Union\n\n"
                    + "import bpy\n\n\n"
                )
            ops_path.write_text(ops_path.read_text() + ops_code)
        update_property_typing(c, code, more=more)
    return 0


if __name__ == "__main__":
    sys.exit(main())
