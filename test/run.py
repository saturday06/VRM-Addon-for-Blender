#!/usr/bin/env python3

import os
import subprocess
import tempfile

repository_root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

with tempfile.TemporaryDirectory() as user_scripts_dir:
    os.mkdir(os.path.join(user_scripts_dir, "addons"))
    os.symlink(
        repository_root_dir,
        os.path.join(user_scripts_dir, "addons", "io_scene_vrm_saturday06"),
    )

    env = os.environ.copy()
    env["BLENDER_USER_SCRIPTS"] = user_scripts_dir
    subprocess.run(
        [
            "blender",
            "-noaudio",  # sound system to None (less output on stdout)
            "--background",  # run UI-less
            "--factory-startup",  # factory settings
            "--addons",
            "io_scene_vrm_saturday06",  # enable the addon
            "--python-exit-code",
            "1",
            "--python",
            os.path.join(repository_root_dir, "test", "stub.py"),  # run the test script
        ],
        env=env,
        check=True,
    )
