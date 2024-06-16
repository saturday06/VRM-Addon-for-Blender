import sys
from unittest import TestCase


class TestExporter(TestCase):
    def test_normalize_weights_compatible_with_gl_float(self) -> None:
        from io_scene_vrm.exporter import vrm0_exporter

        for arg, expected in [
            ([1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]),
            ([2.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]),
            ([1.0, 3.0, 0.0, 0.0], [0.25, 0.75, 0.0, 0.0]),
            ([2.0, 2.0, 2.0, 2.0], [0.25, 0.25, 0.25, 0.25]),
            ([0.0, 0.0, 0.0, sys.float_info.epsilon], [0, 0, 0, 1]),
            (
                [0.0, sys.float_info.epsilon, 0, sys.float_info.epsilon],
                [0, 0.5, 0, 0.5],
            ),
        ]:
            with self.subTest(arg):
                actual = vrm0_exporter.normalize_weights_compatible_with_gl_float(arg)
                self.assertEqual(
                    expected, actual, f"Expected: {expected}, Actual: {actual}"
                )
