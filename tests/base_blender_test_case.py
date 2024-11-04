# SPDX-License-Identifier: MIT OR GPL-3.0-or-later
import contextlib
import importlib.util
import os
import subprocess
import sys
import tempfile
from base64 import urlsafe_b64decode
from copy import deepcopy
from os import environ
from pathlib import Path
from typing import Optional
from unittest import TestCase

import bpy


class BaseBlenderTestCase(TestCase):
    def __init__(self, *args: str, **kwargs: str) -> None:
        # https://stackoverflow.com/a/19102520
        super().__init__(*args, **kwargs)

        if sys.platform == "win32":
            self.exeext = ".exe"
        else:
            self.exeext = ""

        self.repository_root_dir = Path(__file__).resolve(strict=True).parent.parent
        repository_addon_dir = self.repository_root_dir / "src" / "io_scene_vrm"
        self.user_scripts_dir = Path(tempfile.mkdtemp(prefix="blender_vrm_"))
        (self.user_scripts_dir / "addons").mkdir(parents=True, exist_ok=True)
        self.addons_pythonpath = self.user_scripts_dir / "addons"
        addon_dir = self.addons_pythonpath / "io_scene_vrm"
        if sys.platform == "win32":
            import _winapi

            _winapi.CreateJunction(str(repository_addon_dir), str(addon_dir))
        else:
            addon_dir.symlink_to(repository_addon_dir)

        blender_path = self.find_blender_path()
        if not blender_path:
            self.major_minor = f"{bpy.app.version[0]}.{bpy.app.version[1]}"
            return

        command = [str(blender_path), "--version"]
        completed_process = subprocess.run(
            command,
            check=False,
            capture_output=True,
        )
        stdout_str = self.process_output_to_str(completed_process.stdout)
        stderr_str = self.process_output_to_str(completed_process.stderr)
        output = (
            "\n  ".join(command)
            + "\n===== stdout =====\n"
            + stdout_str
            + "===== stderr =====\n"
            + stderr_str
            + "=================="
        )
        if completed_process.returncode != 0:
            raise RuntimeError("Failed to execute command:\n" + output)

        for line in stdout_str.splitlines():
            if not line.startswith("Blender"):
                continue
            self.major_minor = ".".join(line.split(" ")[1].split(".")[:2])
            return

        message = f"Failed to detect Blender Version:\n---\n{stdout_str}\n---"
        raise RuntimeError(message)

    @staticmethod
    def process_output_to_str(process_output: Optional[bytes]) -> str:
        if process_output is None:
            return ""
        output = ""
        for line_bytes in process_output.splitlines():
            line = None
            if sys.platform == "win32":
                with contextlib.suppress(UnicodeDecodeError):
                    line = line_bytes.decode("ansi")
            if line is None:
                line = line_bytes.decode()
            output += str.rstrip(line) + "\n"
        return output

    def find_blender_path(self) -> Optional[Path]:
        bpy_binary_path_str = bpy.app.binary_path
        if bpy_binary_path_str:
            bpy_binary_path = Path(bpy_binary_path_str)
            if bpy_binary_path.exists():
                return bpy_binary_path

        env_blender_path_str = environ.get("BLENDER_VRM_TEST_BLENDER_PATH")
        if not env_blender_path_str:
            return None

        env_blender_path = Path(env_blender_path_str)
        if env_blender_path.exists():
            return env_blender_path

        message = (
            f'Failed to discover blender executable in "{env_blender_path}"'
            + ' specified by environment variable "BLENDER_VRM_TEST_BLENDER_PATH"'
        )
        raise RuntimeError(message)

    def run_script(self, encoded_script_name: str, *encoded_args: str) -> None:
        script_path = (
            self.repository_root_dir
            / "tests"
            / Path(urlsafe_b64decode(encoded_script_name).decode()).name
        )
        args = [urlsafe_b64decode(encoded_arg).decode() for encoded_arg in encoded_args]

        pythonpath = environ.get("PYTHONPATH", "")
        if not any(
            path == str(self.addons_pythonpath) for path in pythonpath.split(os.pathsep)
        ):
            if pythonpath:
                pythonpath += os.pathsep
            pythonpath += str(self.addons_pythonpath)

        additional_env: dict[str, str] = {
            "BLENDER_USER_SCRIPTS": str(self.user_scripts_dir),
            "BLENDER_VRM_AUTOMATIC_LICENSE_CONFIRMATION": "true",
            "BLENDER_VRM_BLENDER_MAJOR_MINOR_VERSION": self.major_minor,
            "PYTHONPATH": pythonpath,
        }

        blender_path = self.find_blender_path()
        if blender_path is None:
            spec = importlib.util.spec_from_file_location("__main__", script_path)
            if spec is None:
                return
            mod = importlib.util.module_from_spec(spec)
            if spec.loader is None:
                return

            bpy.ops.preferences.addon_enable(module="io_scene_vrm")
            if bpy.context.view_layer.objects.active:
                bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="SELECT")
            bpy.ops.object.delete()
            while bpy.context.blend_data.collections:
                bpy.context.blend_data.collections.remove(
                    bpy.context.blend_data.collections[0]
                )
            bpy.ops.outliner.orphans_purge(do_recursive=True)
            bpy.context.view_layer.update()

            old_environ = deepcopy(environ)
            try:
                environ.update(additional_env)
                old_argv = deepcopy(sys.argv)
                try:
                    sys.argv = [str(script_path), "--", *args]
                    spec.loader.exec_module(mod)
                finally:
                    sys.argv = old_argv
            finally:
                environ.clear()
                environ.update(old_environ)
            return

        error_exit_code = 1
        command = [
            str(blender_path),
            "-noaudio",
            "--factory-startup",
            "--addons",
            "io_scene_vrm",
            "--python-exit-code",
            str(error_exit_code),
            "--background",
            "--python-expr",
            "import bpy; bpy.ops.preferences.addon_enable(module='io_scene_vrm')",
            "--python",
            str(script_path),
            "--",
            *args,
        ]

        env = environ.copy()
        env.update(additional_env)

        completed_process = subprocess.run(
            command,
            check=False,
            capture_output=True,
            cwd=self.repository_root_dir,
            env=env,
        )

        stdout_str = self.process_output_to_str(completed_process.stdout)
        stderr_str = self.process_output_to_str(completed_process.stderr)
        output = (
            "\n  ".join(command)
            + "\n===== stdout =====\n"
            + stdout_str
            + "===== stderr =====\n"
            + stderr_str
            + "=================="
        )
        self.assertEqual(
            completed_process.returncode,
            0,
            f"Failed to execute command code={completed_process.returncode}:\n"
            + output,
        )
