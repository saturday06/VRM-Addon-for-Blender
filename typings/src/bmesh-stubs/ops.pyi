# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
from bmesh.types import BMesh, BMFaceSeq

def recalc_face_normals(
    bm: BMesh,
    /,
    *,
    faces: BMFaceSeq = ...,
) -> set[str]: ...
