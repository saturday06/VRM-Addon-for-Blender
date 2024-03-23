def io_scene_vrm_tests_generate_dynamic_tests() -> None:
    import importlib.util
    import os
    import subprocess
    from pathlib import Path

    if os.getenv("BLENDER_VRM_DEVCONTAINER_TEST_GENERATION_USING_SUBPROCESS") == "yes":
        subprocess.run(
            [
                "/usr/bin/blender",
                "--background",
                "-noaudio",
                "--python-exit-code",
                "1",
                "--python",
                str(
                    Path(__file__).parent.parent / "tools" / "generate_dynamic_tests.py"
                ),
            ],
            check=True,
        )
        return

    spec = importlib.util.spec_from_file_location(
        "blender_vrm_addon_run_scripts_generate_dynamic_tests",
        Path(__file__).parent.parent / "tools" / "generate_dynamic_tests.py",
    )
    if spec is None:
        return
    mod = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        return
    spec.loader.exec_module(mod)


io_scene_vrm_tests_generate_dynamic_tests()
