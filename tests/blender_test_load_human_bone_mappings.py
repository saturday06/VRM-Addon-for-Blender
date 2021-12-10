import json
import tempfile

import bpy


def test() -> None:
    bpy.ops.icyp.make_basic_armature()

    head_name = "ModifiedHead"
    with tempfile.NamedTemporaryFile(delete=False) as file:
        file.write(json.dumps({"head": head_name}).encode())
        file.close()
        bpy.ops.vrm.load_human_bone_mappings(filepath=file.name)

    data = bpy.context.active_object.data
    assert (
        data["head"] == head_name
    ), f'head is expected to {head_name} but {data["head"]}'


if __name__ == "__main__":
    test()
