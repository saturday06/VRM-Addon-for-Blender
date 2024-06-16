#!/usr/bin/env python3
# ruff: noqa: T201

import re
import sys
from argparse import ArgumentParser
from pathlib import Path

from bpy.types import (
    ID,
)

from io_scene_vrm import registration
from io_scene_vrm.common import convert_any


def write_property_typing(
    n: str,
    t: str,
    keywords: dict[str, object],
) -> str:
    print(f"  ==> prop={n}")
    ruff_line_len = 88
    comment = "  # type: ignore[no-redef]"
    if n == "stiffiness" or n.endswith("_ussage_name"):
        comment += "  # noqa: SC200"

    if t in ["bpy.props.StringProperty", "bpy.props.EnumProperty"]:
        line = f"        {n}: str{comment}"
    elif t == "bpy.props.FloatProperty":
        line = f"        {n}: float{comment}"
    elif t == "bpy.props.FloatVectorProperty":
        line = f"        {n}: Sequence[float]{comment}"
        if len(line) > ruff_line_len:
            line = f"        {n}: ({comment}\n            Sequence[float]\n        )"
    elif t == "bpy.props.IntProperty":
        line = f"        {n}: int{comment}"
    elif t == "bpy.props.IntVectorProperty":
        line = f"        {n}: Sequence[int]{comment}"
        if len(line) > ruff_line_len:
            line = f"        {n}: ({comment}\n            Sequence[int]\n        )"
    elif t == "bpy.props.BoolProperty":
        line = f"        {n}: bool{comment}"
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
    elif t.startswith("bpy.props."):
        line = f"        # TODO: {n} {t}"
    else:
        return ""

    line += "\n"
    return line


def update_property_typing(
    c: type,
    typing_code: str,
    *,
    more: bool,
) -> None:
    if not typing_code:
        print(" ==> NO CODE")
        return

    print(f"------------------------------------------\n{c}\n{typing_code}")

    # 該当するファイルを探す
    modules = c.__module__.split(".")
    modules.reverse()
    module = modules.pop()
    if module != "io_scene_vrm":
        print(f"Unexpected module: {module}")
        return

    path = Path(__file__).parent.parent / "src" / "io_scene_vrm"
    while modules:
        module = modules.pop()
        path = path / module
    path = path.with_suffix(".py")

    print(f"{path}")

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
                print(f"class def found {class_def_index}")
                class_def_index = line_index
            else:
                continue

        if class_def_colon_index is None:
            # : を探す
            if re.match(".*:", line.split("#")[0]):
                print(f"class colon def found {class_def_colon_index}")
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
        print(f"REMOVE: {another_def_start_index} - {class_type_checking_index}")
        for _ in range(another_def_start_index - class_type_checking_index - 1):
            if class_type_checking_index >= len(lines):
                break
            del lines[class_type_checking_index]
            another_def_start_index -= 1

    lines.insert(
        another_def_start_index - 1,
        "    if TYPE_CHECKING:\n"
        + "        # This code is auto generated.\n"
        + "        # `poetry run python tools/property_typing.py`\n"
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

    classes: list[type] = []
    searching_classes = list(registration.classes)
    while searching_classes:
        c = searching_classes.pop()
        print(f"Searching {c}")
        for b in c.__bases__:
            print(f"++ Searching {b}")
            if b not in classes and b not in searching_classes:
                searching_classes.append(b)
        if c not in classes:
            classes.append(c)
    for c in classes:
        print(f"##### {c} #####")
        code = ""

        annotations = convert_any.mapping_to_object_mapping(
            getattr(c, "__annotations__", None)
        )
        if annotations is None:
            continue
        for k, v in annotations.items():
            if not isinstance(k, str):
                raise TypeError
            function: object = getattr(v, "function", None)
            if function is None:
                continue
            function_name = getattr(function, "__qualname__", None)
            if function_name is None:
                continue

            keywords = convert_any.mapping_to_object_mapping(
                getattr(v, "keywords", None)
            )
            if keywords is None:
                continue
            typed_keywords: dict[str, object] = {
                typed_k: typed_v
                for typed_k, typed_v in keywords.items()
                if isinstance(typed_k, str)
            }
            code += write_property_typing(
                k,
                f"{function.__module__}.{function_name}",
                typed_keywords,
            )
        update_property_typing(c, code, more=more)
    return 0


if __name__ == "__main__":
    sys.exit(main())
