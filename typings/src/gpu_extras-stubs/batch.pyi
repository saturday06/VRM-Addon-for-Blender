# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from gpu.types import GPUBatch, GPUShader

def batch_for_shader(
    shader: GPUShader,
    type: str,
    content: object,
    indices: object = None,
) -> GPUBatch: ...
