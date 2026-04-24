# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

import sys
import unittest

from mathutils import Matrix

from io_scene_vrm.exporter.vrm1_exporter import is_identity_matrix


class TestVrm1Exporter(unittest.TestCase):
    def test_is_identity_matrix(self) -> None:
        # Exact identity matrix
        self.assertTrue(is_identity_matrix(Matrix()))

        # All zeros matrix
        zero_matrix = Matrix.Diagonal((0.0, 0.0, 0.0, 0.0))
        self.assertFalse(is_identity_matrix(zero_matrix))

        # Non-identity matrix
        non_identity = Matrix()
        non_identity[0][1] = 2.0
        self.assertFalse(is_identity_matrix(non_identity))

        # Within epsilon
        # Note: mathutils.Matrix uses single-precision float (float32) internally,
        # while the function checks against sys.float_info.epsilon (float64 epsilon).
        # float32 can represent values much smaller than sys.float_info.epsilon;
        # the important detail is that near 1.0, float32 spacing is much larger
        # (~1e-7), so adding epsilon / 2 to a diagonal 1.0 rounds back to 1.0.
        # For an off-diagonal entry near 0.0, epsilon / 2 may still be stored as a
        # nonzero float32 value, but it remains far below the function's tolerance.
        epsilon = sys.float_info.epsilon
        almost_identity = Matrix()
        # The diagonal entry remains exactly 1.0 after float32 rounding, and the
        # off-diagonal entry stays within the tolerance checked by the function.
        almost_identity[0][0] = 1.0 + epsilon / 2.0
        almost_identity[1][2] = epsilon / 2.0
        self.assertTrue(is_identity_matrix(almost_identity))

        # Outside epsilon (diagonal)
        # To store a different value, diff must > float32 epsilon (~1e-7).
        not_identity_diagonal = Matrix()
        not_identity_diagonal[0][0] = 1.0 + 1e-6
        self.assertFalse(is_identity_matrix(not_identity_diagonal))

        # Outside epsilon (off-diagonal)
        not_identity_off_diagonal = Matrix()
        not_identity_off_diagonal[1][2] = 1e-6
        self.assertFalse(is_identity_matrix(not_identity_off_diagonal))
