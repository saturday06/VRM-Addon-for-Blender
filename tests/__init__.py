def generate_dynamic_tests() -> None:
    import importlib.util
    from os.path import dirname, join

    spec = importlib.util.spec_from_file_location(
        "blender_vrm_addon_run_scripts_generate_dynamic_tests",
        join(dirname(dirname(__file__)), "scripts", "generate_dynamic_tests.py"),
    )
    if spec is None:
        return
    mod = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        return
    spec.loader.exec_module(mod)


generate_dynamic_tests()
