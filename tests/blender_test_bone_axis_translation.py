# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import math

from mathutils import Matrix, Vector

from io_scene_vrm.editor.extension import VrmAddonBoneExtensionPropertyGroup


def assert_axis_translation(
    in_point: tuple[float, float, float],
    out_point: tuple[float, float, float],
    axis_translation: str,
) -> None:
    in_vec = Vector(in_point)
    in_mat = Matrix()
    actual_out_mat = VrmAddonBoneExtensionPropertyGroup.translate_axis(
        in_mat, axis_translation
    )
    actual_out_vec = in_vec @ actual_out_mat
    expected_out_vec = Vector(out_point)

    float_tolerance = 0.000001
    if (
        math.fabs(expected_out_vec[0] - actual_out_vec[0]) < float_tolerance
        and math.fabs(expected_out_vec[1] - actual_out_vec[1]) < float_tolerance
        and math.fabs(expected_out_vec[2] - actual_out_vec[2]) < float_tolerance
    ):
        return

    raise AssertionError(
        f"\n  in_vec={in_vec[:]}\n"
        + f"  expected_out_vec={expected_out_vec[:]}\n"
        + f"    actual_out_vec={actual_out_vec[:]}\n"
        + f"  axis_translation={axis_translation}\n"
        + f"            in_mat=\n{in_mat}\n"
        + f"    actual_out_mat=\n{actual_out_mat}\n"
    )


def test() -> None:
    assert_axis_translation(
        (1, 2, 3),
        (1, 2, 3),
        VrmAddonBoneExtensionPropertyGroup.AXIS_TRANSLATION_NONE.identifier,
    )
    assert_axis_translation(
        (1, 2, 3),
        (-2, 1, 3),
        VrmAddonBoneExtensionPropertyGroup.AXIS_TRANSLATION_X_TO_Y.identifier,
    )
    assert_axis_translation(
        (1, 2, 3),
        (2, -1, 3),
        VrmAddonBoneExtensionPropertyGroup.AXIS_TRANSLATION_MINUS_X_TO_Y.identifier,
    )
    assert_axis_translation(
        (1, 2, 3),
        (-1, -2, 3),
        VrmAddonBoneExtensionPropertyGroup.AXIS_TRANSLATION_MINUS_Y_TO_Y_AROUND_Z.identifier,
    )
    assert_axis_translation(
        (1, 2, 3),
        (1, 3, -2),
        VrmAddonBoneExtensionPropertyGroup.AXIS_TRANSLATION_Z_TO_Y.identifier,
    )
    assert_axis_translation(
        (1, 2, 3),
        (1, -3, 2),
        VrmAddonBoneExtensionPropertyGroup.AXIS_TRANSLATION_MINUS_Z_TO_Y.identifier,
    )


if __name__ == "__main__":
    test()
