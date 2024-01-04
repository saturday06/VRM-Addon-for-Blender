import os
import subprocess
import sys
from base64 import urlsafe_b64decode
from pathlib import Path
from unittest import TestCase

from .base_blender_test_case import BaseBlenderTestCase


class BaseBlenderGuiTestCase(TestCase):
    has_docker = True
    exclude_gui_test = bool(os.environ.get("BLENDER_VRM_EXCLUDE_GUI_TEST"))

    @staticmethod
    def format_process_output(
        completed_process: "subprocess.CompletedProcess[bytes]",
    ) -> str:
        stdout_str = BaseBlenderTestCase.process_output_to_str(completed_process.stdout)
        stderr_str = BaseBlenderTestCase.process_output_to_str(completed_process.stderr)
        return (
            f"Return Code: {completed_process.returncode}\n"
            + "===== stdout =====\n"
            + stdout_str
            + "===== stderr =====\n"
            + stderr_str
            + "=================="
        )

    def __init__(self, *args: str, **kwargs: str) -> None:
        # https://stackoverflow.com/a/19102520
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls) -> None:
        if cls.exclude_gui_test:
            return

        try:
            subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                check=True,
            )
        except FileNotFoundError:
            cls.has_docker = False
            return

        if sys.platform == "win32":
            server_start_bat_path = "tools\\gui_test_server_start.bat"
        else:
            server_start_bat_path = "tools/gui_test_server_start.sh"
        completed_process = subprocess.run(
            server_start_bat_path,
            check=False,
            cwd=Path(__file__).parent.parent,
            capture_output=True,
        )

        if completed_process.returncode:
            raise AssertionError(
                f"{server_start_bat_path}\n"
                + BaseBlenderGuiTestCase.format_process_output(completed_process)
            )

    def do_not_skip(self) -> bool:
        return bool(os.environ.get("CI"))

    def run_gui_test(self, sikuli_test_path: str) -> None:
        if self.exclude_gui_test:
            return
        if not self.has_docker:
            message = "There's no docker executable"
            if self.do_not_skip():
                self.fail(message)
            else:
                self.skipTest(message)
            return
        container_hash = (
            Path("var/repository_root_path_hash.txt")
            .read_text(encoding="ascii")
            .strip()
        )

        commands = [
            "docker",
            "exec",
            "vrm_addon_for_blender_gui_test_container_" + container_hash,
            "java",
            "-jar",
            "sikulixide.jar",
            "-c",
            "-r",
            "tests/test.sikuli/" + urlsafe_b64decode(sikuli_test_path).decode(),
        ]
        completed_process = subprocess.run(
            commands,
            capture_output=True,
            check=False,
        )

        output = f"Test: {sikuli_test_path}\n" + self.format_process_output(
            completed_process
        )
        if completed_process.returncode == 0:
            return

        # Collect artifact
        collect_artifact_commands = [
            "docker",
            "cp",
            "vrm_addon_for_blender_gui_test_container_"
            + container_hash
            + ":"
            + "/root/latest_capture.ogv",
            ".",
        ]
        collect_artifact_completed_process = subprocess.run(
            collect_artifact_commands,
            capture_output=True,
            check=False,
        )

        collect_artifact_output = "Collect artifact\n" + self.format_process_output(
            collect_artifact_completed_process
        )

        if collect_artifact_completed_process.returncode != 0:
            collect_artifact_message = (
                "\nFailed to execute command:\n"
                + (" ".join(collect_artifact_commands))
                + "\n"
                + collect_artifact_output
                + "\n"
            )
        else:
            collect_artifact_message = "See latest capture file: latest_capture.ogv\n"

        message = (
            "\nFailed to execute command:\n"
            + (" ".join(commands))
            + "\n"
            + output
            + "\n"
            + collect_artifact_message
            + "See local test web server:\n"
            + "http://127.0.0.1:6080/vnc.html?autoconnect=true"
        )

        self.assertEqual(completed_process.returncode, 0, message)
