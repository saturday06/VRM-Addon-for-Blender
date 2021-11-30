import importlib
from os.path import dirname, join

# pylint: disable=no-value-for-parameter,deprecated-method
importlib.machinery.SourceFileLoader(
    "blender_vrm_addon_run_scripts_generate_dynamic_tests",
    join(dirname(dirname(__file__)), "scripts", "generate_dynamic_tests.py"),
).load_module()
# pylint: enable=no-value-for-parameter,deprecated-method
