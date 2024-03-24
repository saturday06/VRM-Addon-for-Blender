def io_scene_vrm_tests_generate_dynamic_tests() -> None:
    import importlib.util
    import os
    import platform
    import subprocess
    from pathlib import Path

    if (
        platform.machine() == "aarch64"
        and os.getenv("BLENDER_VRM_DEVCONTAINER_SPECIAL_WORKAROUNDS") == "yes"
    ):
        # aarch64のLinuxは単体のbpyが無いので、Blenderを直接起動する。
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
