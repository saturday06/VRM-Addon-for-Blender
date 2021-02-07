import contextlib
import os
import platform
import subprocess
import tempfile
from unittest import TestCase

system = platform.system()
if system == "Windows":
    exeext = ".exe"
else:
    exeext = ""

repository_root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
user_scripts_dir = tempfile.mkdtemp()
os.mkdir(os.path.join(user_scripts_dir, "addons"))
addon_dir = os.path.join(user_scripts_dir, "addons", "io_scene_vrm_saturday06")
if system == "Windows":
    import _winapi

    _winapi.CreateJunction(repository_root_dir, addon_dir)
else:
    os.symlink(repository_root_dir, addon_dir)

test_vrm_dir = os.environ.get(
    "BLENDER_VRM_TEST_VRM_DIR", os.path.join(repository_root_dir, "tests", "vrm")
)
test_temp_vrm_dir = os.path.join(test_vrm_dir, "temp")
test_in_vrm_dir = os.path.join(test_vrm_dir, "in")
test_out_vrm_dir = os.path.join(test_vrm_dir, "out")
test_out2_vrm_dir = os.path.join(test_vrm_dir, "out2")
test_out3_vrm_dir = os.path.join(test_vrm_dir, "out3")

os.makedirs(test_temp_vrm_dir, exist_ok=True)
os.makedirs(test_out_vrm_dir, exist_ok=True)
os.makedirs(test_out2_vrm_dir, exist_ok=True)
os.makedirs(test_out3_vrm_dir, exist_ok=True)


def process_output_to_str(process_output: bytes) -> str:
    output = None
    if platform.system() != "Windows":
        output = process_output.decode()
    else:
        with contextlib.suppress(UnicodeDecodeError):
            output = process_output.decode("ansi")
        if output is None:
            output = process_output.decode()
    if output != "" and not output.endswith("\n"):
        output += "\n"
    return output


def find_blender_command() -> str:
    try:
        import bpy

        bpy_binary_path = str(bpy.app.binary_path)
        if bpy_binary_path and os.path.exists(bpy_binary_path):
            return bpy_binary_path
    except ImportError:
        pass
    env = os.environ.get("BLENDER_VRM_TEST_BLENDER_PATH")
    if env:
        return env
    if platform.system() == "Windows":
        completed_process = subprocess.run(
            "where blender", shell=True, capture_output=True, check=False
        )
        if completed_process.returncode == 0:
            return process_output_to_str(completed_process.stdout).splitlines()[0]
    if os.name == "posix":
        completed_process = subprocess.run(
            "which blender", shell=True, capture_output=True, check=False
        )
        if completed_process.returncode == 0:
            return process_output_to_str(completed_process.stdout).splitlines()[0]
    if platform.system() == "Darwin":
        default_path = "/Applications/Blender.app/Contents/MacOS/Blender"
        if os.path.exists(default_path):
            return default_path
    raise Exception(
        "Failed to discover blender executable. "
        + "Please set blender executable location to "
        + 'environment variable "BLENDER_VRM_TEST_BLENDER_PATH"'
    )


class TestBlender(TestCase):
    def run_script(self, script: str, *args: str) -> None:
        env = os.environ.copy()
        env["BLENDER_USER_SCRIPTS"] = user_scripts_dir
        env["BLENDER_VRM_AUTOMATIC_LICENSE_CONFIRMATION"] = "true"
        command = [
            find_blender_command(),
            "-noaudio",  # sound system to None (less output on stdout)
            "--factory-startup",  # factory settings
            "--addons",
            "io_scene_vrm_saturday06",  # enable the addon
            "--python-exit-code",
            "1",
            "--background",
            "--python",
            os.path.join(repository_root_dir, "tests", script),  # run the test script
            "--",
            *args,
        ]
        indented_command_str = "\n  ".join(command)
        print("run: " + indented_command_str)
        completed_process = subprocess.run(
            command, check=False, capture_output=True, cwd=repository_root_dir, env=env
        )
        stdout_str = process_output_to_str(completed_process.stdout)
        stderr_str = process_output_to_str(completed_process.stderr)
        output = (
            "===== stdout =====\n"
            + stdout_str
            + "===== stderr =====\n"
            + stderr_str
            + "=================="
        )
        print(output)
        self.assertEqual(
            completed_process.returncode,
            0,
            f"Failed to execute command:\n{indented_command_str}\n" + output,
        )

    def test_basic_armature(self) -> None:
        self.run_script(
            "blender_basic_armature.py",
            os.path.join(test_in_vrm_dir, "basic_armature.vrm"),
            test_temp_vrm_dir,
        )

    def test_io(self) -> None:
        update_vrm_dir = os.environ.get("BLENDER_VRM_TEST_UPDATE_VRM_DIR") == "true"
        for (vrm, extract_textures) in [
            (v, e)
            for e in ["false", "true"]
            for v in os.listdir(test_in_vrm_dir)
            if v.endswith(".vrm")
        ]:
            with self.subTest((vrm, extract_textures)):
                self.run_script(
                    "blender_io.py",
                    os.path.join(test_in_vrm_dir, vrm),
                    os.path.join(test_out_vrm_dir, vrm),
                    test_temp_vrm_dir,
                    extract_textures,
                )

                if (
                    not os.path.exists(os.path.join(test_out2_vrm_dir, vrm))
                    and not update_vrm_dir
                ):
                    self.run_script(
                        "blender_io.py",
                        os.path.join(test_out_vrm_dir, vrm),
                        os.path.join(test_out_vrm_dir, vrm),
                        test_temp_vrm_dir,
                        extract_textures,
                    )
                    continue

                self.run_script(
                    "blender_io.py",
                    os.path.join(test_out_vrm_dir, vrm),
                    os.path.join(test_out2_vrm_dir, vrm),
                    test_temp_vrm_dir,
                    extract_textures,
                )

                if update_vrm_dir and not os.path.exists(
                    os.path.join(test_out2_vrm_dir, vrm)
                ):
                    continue

                test_last_vrm_dir = test_out2_vrm_dir
                if (
                    os.path.exists(os.path.join(test_out3_vrm_dir, vrm))
                    or update_vrm_dir
                ):
                    test_last_vrm_dir = test_out3_vrm_dir

                self.run_script(
                    "blender_io.py",
                    os.path.join(test_out2_vrm_dir, vrm),
                    os.path.join(test_last_vrm_dir, vrm),
                    test_temp_vrm_dir,
                    extract_textures,
                )
