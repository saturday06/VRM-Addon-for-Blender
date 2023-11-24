import contextlib
import os
import subprocess
import sys
import tempfile
from base64 import urlsafe_b64decode
from os import environ
from pathlib import Path
from typing import Optional
from unittest import TestCase


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

        command = [str(self.find_blender_command()), "--version"]
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

    def find_blender_command(self) -> Path:
        try:
            import bpy

            bpy_binary_path_str = str(bpy.app.binary_path)
            if bpy_binary_path_str:
                bpy_binary_path = Path(bpy_binary_path_str)
                if bpy_binary_path.exists():
                    return bpy_binary_path
        except ImportError:
            pass
        env_blender_path_str = environ.get("BLENDER_VRM_TEST_BLENDER_PATH")
        if env_blender_path_str:
            env_blender_path = Path(env_blender_path_str)
            if env_blender_path.exists():
                return env_blender_path
        if sys.platform == "win32":
            completed_process = subprocess.run(
                "where blender", shell=True, capture_output=True, check=False
            )
            if completed_process.returncode == 0:
                where_str = self.process_output_to_str(
                    completed_process.stdout
                ).splitlines()[0]
                if where_str:
                    where_path = Path(where_str)
                    if where_path.exists():
                        return where_path
        if os.name == "posix":
            completed_process = subprocess.run(
                "which blender", shell=True, capture_output=True, check=False
            )
            if completed_process.returncode == 0:
                which_str = self.process_output_to_str(
                    completed_process.stdout
                ).splitlines()[0]
                if which_str:
                    which_path = Path(which_str)
                    if which_path.exists():
                        return which_path
        if sys.platform == "darwin":
            default_path = Path("/Applications/Blender.app/Contents/MacOS/Blender")
            if default_path.exists():
                return default_path
        raise RuntimeError(
            "Failed to discover blender executable. "
            + "Please set blender executable location to "
            + 'environment variable "BLENDER_VRM_TEST_BLENDER_PATH"'
        )

    def run_script(self, script: str, *args: str) -> None:
        env = environ.copy()
        env["BLENDER_USER_SCRIPTS"] = str(self.user_scripts_dir)
        env["BLENDER_VRM_AUTOMATIC_LICENSE_CONFIRMATION"] = "true"
        env["BLENDER_VRM_BLENDER_MAJOR_MINOR_VERSION"] = self.major_minor
        pythonpath = env.get("PYTHONPATH", "")
        if pythonpath:
            pythonpath += os.pathsep
        pythonpath += str(self.addons_pythonpath)
        env["PYTHONPATH"] = pythonpath

        error_exit_code = 1
        command = [
            str(self.find_blender_command()),
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
            str(
                self.repository_root_dir / "tests" / urlsafe_b64decode(script).decode()
            ),
            "--",
            *[urlsafe_b64decode(arg).decode() for arg in args],
        ]

        if self.major_minor == "2.83" and sys.platform == "darwin":
            retry = 3
        else:
            retry = 1

        for _ in range(retry):
            completed_process = subprocess.run(
                command,
                check=False,
                capture_output=True,
                cwd=self.repository_root_dir,
                env=env,
            )
            if completed_process.returncode not in [0, error_exit_code]:
                continue

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
                "Failed to execute command:\n" + output,
            )
