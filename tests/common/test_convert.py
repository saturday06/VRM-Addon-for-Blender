# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import math
from unittest import TestCase

from io_scene_vrm.common import convert


class TestConvert(TestCase):
    def test_iterator_or_none(self) -> None:
        self.assertIsNone(convert.iterator_or_none(None))
        self.assertIsNone(convert.iterator_or_none(1))
        self.assertIsNone(convert.iterator_or_none(True))

        iterator = convert.iterator_or_none([1, 2, 3])
        self.assertIsNotNone(iterator)
        if iterator is not None:
            self.assertEqual(list(iterator), [1, 2, 3])

        iterator = convert.iterator_or_none("abc")
        self.assertIsNotNone(iterator)
        if iterator is not None:
            self.assertEqual(list(iterator), ["a", "b", "c"])

    def test_sequence_or_none(self) -> None:
        self.assertIsNone(convert.sequence_or_none(None))
        self.assertIsNone(convert.sequence_or_none(1))

        self.assertEqual(convert.sequence_or_none([1, 2, 3]), [1, 2, 3])
        self.assertEqual(convert.sequence_or_none((1, 2, 3)), [1, 2, 3])
        self.assertEqual(convert.sequence_or_none("abc"), ["a", "b", "c"])

    def test_mapping_or_none(self) -> None:
        self.assertIsNone(convert.mapping_or_none(None))
        self.assertIsNone(convert.mapping_or_none([1, 2]))

        self.assertEqual(convert.mapping_or_none({"a": 1}), {"a": 1})

    def test_vrm_json_vector3_to_tuple(self) -> None:
        self.assertIsNone(convert.vrm_json_vector3_to_tuple(None))
        self.assertIsNone(convert.vrm_json_vector3_to_tuple([]))

        self.assertEqual(convert.vrm_json_vector3_to_tuple({}), (0.0, 0.0, 0.0))
        self.assertEqual(
            convert.vrm_json_vector3_to_tuple({"x": 1, "y": 2, "z": 3}), (1.0, 2.0, 3.0)
        )
        self.assertEqual(
            convert.vrm_json_vector3_to_tuple({"x": 1.5, "y": 2.5, "z": 3.5}),
            (1.5, 2.5, 3.5),
        )
        self.assertEqual(convert.vrm_json_vector3_to_tuple({"x": "a"}), (0.0, 0.0, 0.0))

    def test_vrm_json_curve_to_list(self) -> None:
        self.assertIsNone(convert.vrm_json_curve_to_list(None))
        self.assertIsNone(convert.vrm_json_curve_to_list({}))

        self.assertEqual(
            convert.vrm_json_curve_to_list([]),
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        )
        self.assertEqual(
            convert.vrm_json_curve_to_list([1, 2, 3]),
            [1.0, 2.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        )
        self.assertEqual(
            convert.vrm_json_curve_to_list([1, 2, 3, 4, 5, 6, 7, 8]),
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        )
        self.assertEqual(
            convert.vrm_json_curve_to_list([1, 2, 3, 4, 5, 6, 7, 8, 9]),
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        )
        self.assertEqual(
            convert.vrm_json_curve_to_list(["a", 2]),
            [0.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        )

    def test_vrm_json_array_to_float_vector(self) -> None:
        self.assertEqual(
            convert.vrm_json_array_to_float_vector(None, [1.0, 2.0]), [1.0, 2.0]
        )
        self.assertEqual(
            convert.vrm_json_array_to_float_vector({}, [1.0, 2.0]), [1.0, 2.0]
        )

        self.assertEqual(
            convert.vrm_json_array_to_float_vector([], [1.0, 2.0]), [1.0, 2.0]
        )
        self.assertEqual(
            convert.vrm_json_array_to_float_vector([3.0], [1.0, 2.0]), [3.0, 2.0]
        )
        self.assertEqual(
            convert.vrm_json_array_to_float_vector([3.0, 4.0, 5.0], [1.0, 2.0]),
            [3.0, 4.0],
        )
        self.assertEqual(
            convert.vrm_json_array_to_float_vector(["a", 4.0], [1.0, 2.0]), [1.0, 4.0]
        )

    def test_mtoon_shading_toony_1_to_0(self) -> None:
        self.assertAlmostEqual(
            convert.mtoon_shading_toony_1_to_0(0.5, 0.0), 0.33333333, places=5
        )
        self.assertAlmostEqual(
            convert.mtoon_shading_toony_1_to_0(1.0, 0.0), 1.0, places=5
        )
        self.assertAlmostEqual(
            convert.mtoon_shading_toony_1_to_0(0.0, 0.5), 0.2, places=5
        )

        # Test zero division avoidance
        self.assertAlmostEqual(
            convert.mtoon_shading_toony_1_to_0(2.0, 0.0), 0.9, places=5
        )

        # Test negative output clamping to 0
        self.assertEqual(convert.mtoon_shading_toony_1_to_0(-0.5, -0.5), 0.0)

        # Test output > 1 clamping to 1
        self.assertEqual(convert.mtoon_shading_toony_1_to_0(1.5, 0.5), 1.0)

        # Test another regular case
        self.assertAlmostEqual(
            convert.mtoon_shading_toony_1_to_0(0.2, 0.3), 0.2380952, places=5
        )

    def test_mtoon_shading_shift_1_to_0(self) -> None:
        self.assertEqual(convert.mtoon_shading_shift_1_to_0(0.5, 0.0), -0.5)
        self.assertEqual(convert.mtoon_shading_shift_1_to_0(1.0, 0.5), -0.5)
        self.assertEqual(convert.mtoon_shading_shift_1_to_0(0.0, 0.0), -1.0)
        self.assertEqual(convert.mtoon_shading_shift_1_to_0(2.0, -1.0), 1.0)

    def test_mtoon_gi_equalization_to_intensity(self) -> None:
        self.assertEqual(convert.mtoon_gi_equalization_to_intensity(0.0), 1.0)
        self.assertEqual(convert.mtoon_gi_equalization_to_intensity(0.5), 0.5)
        self.assertEqual(convert.mtoon_gi_equalization_to_intensity(1.0), 0.0)
        self.assertEqual(convert.mtoon_gi_equalization_to_intensity(1.5), 0.0)
        self.assertEqual(convert.mtoon_gi_equalization_to_intensity(-0.5), 1.0)

    def test_mtoon_shading_toony_0_to_1(self) -> None:
        self.assertAlmostEqual(
            convert.mtoon_shading_toony_0_to_1(0.5, 0.0), 0.75, places=5
        )
        self.assertAlmostEqual(
            convert.mtoon_shading_toony_0_to_1(1.0, 0.0), 1.0, places=5
        )
        self.assertAlmostEqual(
            convert.mtoon_shading_toony_0_to_1(0.0, 0.5), 0.75, places=5
        )

    def test_mtoon_shading_shift_0_to_1(self) -> None:
        self.assertAlmostEqual(
            convert.mtoon_shading_shift_0_to_1(0.5, 0.0), -0.25, places=5
        )
        self.assertAlmostEqual(
            convert.mtoon_shading_shift_0_to_1(1.0, 0.0), 0.0, places=5
        )
        self.assertAlmostEqual(
            convert.mtoon_shading_shift_0_to_1(0.0, 0.5), -0.75, places=5
        )

    def test_mtoon_intensity_to_gi_equalization(self) -> None:
        self.assertEqual(convert.mtoon_intensity_to_gi_equalization(0.0), 1.0)
        self.assertEqual(convert.mtoon_intensity_to_gi_equalization(0.5), 0.5)
        self.assertEqual(convert.mtoon_intensity_to_gi_equalization(1.0), 0.0)

    def test_get_shading_range_0x(self) -> None:
        self.assertEqual(convert._get_shading_range_0x(0.5, 0.0), (0.0, 0.5))
        self.assertEqual(convert._get_shading_range_0x(1.0, 0.0), (0.0, 0.0))
        self.assertEqual(convert._get_shading_range_0x(0.0, 0.5), (0.5, 1.0))

    def test_float_or_none(self) -> None:
        self.assertEqual(convert.float_or_none(1.5), 1.5)
        self.assertEqual(convert.float_or_none(1), 1.0)
        self.assertEqual(convert.float_or_none(True), 1.0)
        self.assertEqual(convert.float_or_none(False), 0.0)
        self.assertIsNone(convert.float_or_none(math.nan))
        self.assertIsNone(convert.float_or_none("1.5"))
        self.assertIsNone(convert.float_or_none(None))

        self.assertEqual(convert.float_or_none(10.0, max_value=5.0), 5.0)
        self.assertEqual(convert.float_or_none(-10.0, min_value=-5.0), -5.0)

    def test_float_or(self) -> None:
        self.assertEqual(convert.float_or(1.5, 0.0), 1.5)
        self.assertEqual(convert.float_or(None, 2.5), 2.5)
        self.assertEqual(convert.float_or("a", 3.5), 3.5)

        with self.assertLogs("io_scene_vrm.common.convert", level="WARNING") as cm:
            self.assertEqual(convert.float_or(None, 10.0, max_value=5.0), 5.0)
        self.assertEqual(len(cm.output), 1)

    def test_float4_or_none(self) -> None:
        self.assertEqual(convert.float4_or_none([1, 2, 3, 4]), (1.0, 2.0, 3.0, 4.0))
        self.assertIsNone(convert.float4_or_none(None))
        self.assertIsNone(convert.float4_or_none([1, 2, 3]))
        self.assertIsNone(convert.float4_or_none([1, 2, 3, 4, 5]))
        self.assertIsNone(convert.float4_or_none([1, "a", 3, 4]))

    def test_float4_or(self) -> None:
        self.assertEqual(
            convert.float4_or([1, 2, 3, 4], (0.0, 0.0, 0.0, 0.0)), (1.0, 2.0, 3.0, 4.0)
        )
        self.assertEqual(
            convert.float4_or(None, (1.0, 2.0, 3.0, 4.0)), (1.0, 2.0, 3.0, 4.0)
        )

    def test_float3_or_none(self) -> None:
        self.assertEqual(convert.float3_or_none([1, 2, 3]), (1.0, 2.0, 3.0))
        self.assertIsNone(convert.float3_or_none(None))
        self.assertIsNone(convert.float3_or_none([1, 2]))
        self.assertIsNone(convert.float3_or_none([1, 2, 3, 4]))
        self.assertIsNone(convert.float3_or_none([1, "a", 3]))

    def test_float3_or(self) -> None:
        self.assertEqual(convert.float3_or([1, 2, 3], (0.0, 0.0, 0.0)), (1.0, 2.0, 3.0))
        self.assertEqual(convert.float3_or(None, (1.0, 2.0, 3.0)), (1.0, 2.0, 3.0))

    def test_float2_or_none(self) -> None:
        self.assertEqual(convert.float2_or_none([1, 2]), (1.0, 2.0))
        self.assertIsNone(convert.float2_or_none(None))
        self.assertIsNone(convert.float2_or_none([1]))
        self.assertIsNone(convert.float2_or_none([1, 2, 3]))
        self.assertIsNone(convert.float2_or_none([1, "a"]))

    def test_axis_blender_to_gltf(self) -> None:
        self.assertEqual(convert.axis_blender_to_gltf([1, 2, 3]), (-1.0, 3.0, 2.0))
        self.assertEqual(
            convert.axis_blender_to_gltf((1.0, 2.0, 3.0)), (-1.0, 3.0, 2.0)
        )

    def test_linear_to_srgb(self) -> None:
        self.assertEqual(convert.linear_to_srgb([]), [])

        srgb_short = convert.linear_to_srgb([0.5])
        self.assertAlmostEqual(srgb_short[0], 0.72974005, places=5)

        srgb_3 = convert.linear_to_srgb([0.5, 0.5, 0.5])
        self.assertAlmostEqual(srgb_3[0], 0.72974005, places=5)
        self.assertAlmostEqual(srgb_3[1], 0.72974005, places=5)
        self.assertAlmostEqual(srgb_3[2], 0.72974005, places=5)

        self.assertEqual(
            convert.linear_to_srgb([0.0, 0.0, 0.0, 0.5]), [0.0, 0.0, 0.0, 0.5]
        )
        self.assertEqual(
            convert.linear_to_srgb([1.0, 1.0, 1.0, 1.0]), [1.0, 1.0, 1.0, 1.0]
        )
        srgb = convert.linear_to_srgb([0.5, 0.5, 0.5, 0.5])
        self.assertAlmostEqual(srgb[0], 0.72974005, places=5)
        self.assertAlmostEqual(srgb[1], 0.72974005, places=5)
        self.assertAlmostEqual(srgb[2], 0.72974005, places=5)
        self.assertEqual(srgb[3], 0.5)

        srgb_5 = convert.linear_to_srgb([0.5, 0.5, 0.5, 0.5, 0.5])
        self.assertAlmostEqual(srgb_5[0], 0.72974005, places=5)
        self.assertAlmostEqual(srgb_5[1], 0.72974005, places=5)
        self.assertAlmostEqual(srgb_5[2], 0.72974005, places=5)
        self.assertEqual(srgb_5[3], 0.5)
        self.assertEqual(srgb_5[4], 0.5)

    def test_srgb_to_linear(self) -> None:
        self.assertEqual(convert.srgb_to_linear([]), [])

        linear_short = convert.srgb_to_linear([0.5])
        self.assertAlmostEqual(linear_short[0], 0.21763764, places=5)

        linear_3 = convert.srgb_to_linear([0.5, 0.5, 0.5])
        self.assertAlmostEqual(linear_3[0], 0.21763764, places=5)
        self.assertAlmostEqual(linear_3[1], 0.21763764, places=5)
        self.assertAlmostEqual(linear_3[2], 0.21763764, places=5)

        self.assertEqual(
            convert.srgb_to_linear([0.0, 0.0, 0.0, 0.5]), [0.0, 0.0, 0.0, 0.5]
        )
        self.assertEqual(
            convert.srgb_to_linear([1.0, 1.0, 1.0, 1.0]), [1.0, 1.0, 1.0, 1.0]
        )
        linear = convert.srgb_to_linear([0.5, 0.5, 0.5, 0.5])
        self.assertAlmostEqual(linear[0], 0.21763764, places=5)
        self.assertAlmostEqual(linear[1], 0.21763764, places=5)
        self.assertAlmostEqual(linear[2], 0.21763764, places=5)
        self.assertEqual(linear[3], 0.5)

        linear_5 = convert.srgb_to_linear([0.5, 0.5, 0.5, 0.5, 0.5])
        self.assertAlmostEqual(linear_5[0], 0.21763764, places=5)
        self.assertAlmostEqual(linear_5[1], 0.21763764, places=5)
        self.assertAlmostEqual(linear_5[2], 0.21763764, places=5)
        self.assertEqual(linear_5[3], 0.5)
        self.assertEqual(linear_5[4], 0.5)
