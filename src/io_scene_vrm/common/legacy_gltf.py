# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
"""Legacy glTF shader that existed before version 2.10.5.

https://github.com/saturday06/VRM-Addon-for-Blender/tree/2_10_5
"""

from typing import Final

TEXTURE_INPUT_NAMES: Final = (
    "color_texture",
    "normal",
    "emissive_texture",
    "occlusion_texture",
)
VAL_INPUT_NAMES: Final = ("metallic", "roughness", "unlit")
RGBA_INPUT_NAMES: Final = ("base_Color", "emissive_color")
