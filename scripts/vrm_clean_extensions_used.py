#!/usr/bin/env python3

import glob
import sys

from io_scene_vrm.common import gltf


def clean(path: str) -> None:
    with open(path, "rb") as f:
        input_bin = f.read()

    json_dict, binary_chunk = gltf.parse_glb(input_bin)

    extensions_used = json_dict.get("extensionsUsed")
    if not isinstance(extensions_used, list):
        extensions_used = []
        json_dict["extensionsUsed"] = extensions_used

    extensions_used.clear()
    extensions_used.append("VRM")

    for some_dicts in [
        json_dict.get("materials"),
        json_dict.get("textures"),
    ]:
        if not isinstance(some_dicts, list):
            continue
        for some_dict in some_dicts:
            if not isinstance(some_dict, dict):
                continue
            extensions_dict = some_dict.get("extensions")
            if not isinstance(extensions_dict, dict):
                continue
            for key in extensions_dict:
                if key in extensions_used:
                    continue
                extensions_used.append(key)

    extensions_used.sort()

    output_bin = gltf.pack_glb(json_dict, binary_chunk)

    with open(path, "wb") as f:
        f.write(output_bin)


def main() -> int:
    for path in glob.glob("**/*.vrm", recursive=True):
        print(f"===== {path} =====")
        clean(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
