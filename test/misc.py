import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import vrm_types  # noqa: E402

for arg, expected in [
    ([1, 0, 0, 0], [1, 0, 0, 0]),
    ([2, 0, 0, 0], [1, 0, 0, 0]),
    ([1, 3, 0, 0], [0.25, 0.75, 0, 0]),
    ([2, 2, 2, 2], [0.25, 0.25, 0.25, 0.25]),
    ([0, 0, 0, sys.float_info.epsilon], [0, 0, 0, 1]),
    ([0, sys.float_info.epsilon, 0, sys.float_info.epsilon], [0, 0.5, 0, 0.5]),
]:
    actual = vrm_types.normalize_weights_compatible_with_gl_float(arg)
    assert expected == actual, f"Expected: {expected}, Actual: {actual}"

print("OK")
