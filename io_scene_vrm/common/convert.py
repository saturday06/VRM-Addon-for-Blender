import os
import tempfile
from collections import abc
from typing import Any, List, Optional, Tuple

import bpy

from .char import INTERNAL_NAME_PREFIX


def vrm_json_vector3_to_tuple(
    value: Any,
) -> Optional[Tuple[float, float, float]]:
    if not isinstance(value, dict):
        return None
    x = value.get("x")
    y = value.get("y")
    z = value.get("z")
    if not isinstance(x, (int, float)):
        x = 0
    if not isinstance(y, (int, float)):
        y = 0
    if not isinstance(z, (int, float)):
        z = 0
    return (float(x), float(y), float(z))


def vrm_json_curve_to_list(curve: Any) -> Optional[List[float]]:
    if not isinstance(curve, abc.Iterable):
        return None
    values = [float(v) if isinstance(v, (int, float)) else 0 for v in curve]
    while len(values) < 8:
        values.append(0)
    while len(values) > 8:
        values.pop()
    return values


def vrm_json_array_to_float_vector(json: Any, defaults: List[float]) -> List[float]:
    if not isinstance(json, abc.Iterable):
        return defaults

    input_values = list(json)
    output_values = []
    for index, default in enumerate(defaults):
        if index < len(input_values) and isinstance(input_values[index], (int, float)):
            output_values.append(float(input_values[index]))
        else:
            output_values.append(float(default))

    return output_values


BPY_TRACK_AXIS_TO_VRM_AIM_AXIS = {
    "TRACK_X": "PositiveX",
    "TRACK_Y": "PositiveY",
    "TRACK_Z": "PositiveZ",
    "TRACK_NEGATIVE_X": "NegativeX",
    "TRACK_NEGATIVE_Y": "NegativeY",
    "TRACK_NEGATIVE_Z": "NegativeZ",
}

VRM_AIM_AXIS_TO_BPY_TRACK_AXIS = {
    v: k for k, v in BPY_TRACK_AXIS_TO_VRM_AIM_AXIS.items()
}


def image_to_image_bytes(image: bpy.types.Image) -> Tuple[bytes, str]:
    if (
        image.source == "FILE"
        and not image.is_dirty
        and image.file_format in ["PNG", "JPEG"]
    ):
        mime = "image/" + image.file_format.lower()
        if image.packed_file is not None:
            return (image.packed_file.data, mime)
        with open(image.filepath_from_user(), "rb") as f:
            return (f.read(), mime)

    mime = "image/png"
    with tempfile.TemporaryDirectory() as temp_dir:
        export_image: Optional[bpy.types.Image] = None
        try:
            if image.size[0] > 0 and image.size[1] > 0:
                export_image = image.copy()
                # https://github.com/KhronosGroup/glTF-Blender-IO/issues/894#issuecomment-579094775
                export_image.update()
                # https://github.com/KhronosGroup/glTF-Blender-IO/commit/0ea9e74c40977a36bbccb7b823fe8bf5955fc528
                export_image.pixels = image.pixels[:]
            else:
                print('Failed to load image "{image.name}"')
                export_image = bpy.data.images.new(
                    INTERNAL_NAME_PREFIX + "TempVrmExport-" + image.name,
                    width=1,
                    height=1,
                )
            filepath = os.path.join(temp_dir, "image.png")
            export_image.filepath_raw = filepath
            export_image.file_format = "PNG"
            export_image.save()
        finally:
            if export_image is not None:
                bpy.data.images.remove(export_image)
        with open(filepath, "rb") as f:
            return (f.read(), mime)
