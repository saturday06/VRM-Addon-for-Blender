import os
import pathlib
import platform
import subprocess
import tempfile
from unittest import TestCase

if platform.system() == "Windows":
    import _winapi

    exeext = ".exe"
else:
    exeext = ""

repository_root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
user_scripts_dir = tempfile.mkdtemp()
os.mkdir(os.path.join(user_scripts_dir, "addons"))
addon_dir = os.path.join(user_scripts_dir, "addons", "io_scene_vrm_saturday06")
if platform.system() == "Windows":
    _winapi.CreateJunction(repository_root_dir, addon_dir)
else:
    os.symlink(repository_root_dir, addon_dir)

test_vrm_dir = os.environ.get(
    "BLENDER_VRM_TEST_VRM_DIR", os.path.join(repository_root_dir, "test", "vrm")
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


def find_blender_command():
    try:
        import bpy

        bpy_binary_path = bpy.app.binary_path
        if bpy_binary_path and os.path.exists(bpy_binary_path):
            return bpy_binary_path
    except ImportError:
        pass
    env = os.environ.get("BLENDER_VRM_TEST_BLENDER_PATH")
    if env:
        return env
    if platform.system() == "Windows":
        completed_process = subprocess.run(
            ["where", "blender"], shell=True, capture_output=True, check=False
        )
        if completed_process.returncode == 0:
            return completed_process.stdout.decode("oem").splitlines()[0]
    if os.name == "posix":
        completed_process = subprocess.run(
            ["which", "blender"], shell=True, capture_output=True, check=False
        )
        if completed_process.returncode == 0:
            return completed_process.stdout.decode().splitlines()[0]
    if platform.system() == "Darwin":
        default_path = "/Applications/Blender.app/Contents/MacOS/Blender"
        if os.path.exists(default_path):
            return default_path
    raise Exception(
        "Failed to discover blender executable. "
        + "Please set blender executable location to "
        + 'environment variable "BLENDER_VRM_TEST_BLENDER_PATH"'
    )


def run_script(script, *args):
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
        os.path.join(repository_root_dir, "test", script),  # run the test script
        "--",
        *args,
    ]
    print("run: " + "\n  ".join(command))
    return subprocess.run(command, check=False, cwd=repository_root_dir, env=env)


class TestBlender(TestCase):
    def run_script(self, script, *args):
        self.assertEqual(0, run_script(script, *args).returncode)

    def test_basic_armature(self):
        self.run_script(
            "blender_basic_armature.py",
            os.path.join(test_in_vrm_dir, "basic_armature.vrm"),
            test_temp_vrm_dir,
        )

    def test_io(self):
        update_vrm_dir = os.environ.get("BLENDER_VRM_TEST_UPDATE_VRM_DIR") == "yes"
        for vrm in [f for f in os.listdir(test_in_vrm_dir) if f.endswith(".vrm")]:
            with self.subTest(vrm):
                self.run_script(
                    "blender_io.py",
                    os.path.join(test_in_vrm_dir, vrm),
                    os.path.join(test_out_vrm_dir, vrm),
                    test_temp_vrm_dir,
                )
                if (
                    os.path.exists(os.path.join(test_out2_vrm_dir, vrm))
                    or update_vrm_dir
                ):
                    self.run_script(
                        "blender_io.py",
                        os.path.join(test_out_vrm_dir, vrm),
                        os.path.join(test_out2_vrm_dir, vrm),
                        test_temp_vrm_dir,
                    )

                    if (
                        pathlib.Path(os.path.join(test_out_vrm_dir, vrm)).read_bytes()
                        == pathlib.Path(
                            os.path.join(test_out2_vrm_dir, vrm)
                        ).read_bytes()
                    ):
                        os.remove(os.path.join(test_out2_vrm_dir, vrm))
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
                    )

                    if (
                        test_last_vrm_dir == test_out3_vrm_dir
                        and pathlib.Path(
                            os.path.join(test_out2_vrm_dir, vrm)
                        ).read_bytes()
                        == pathlib.Path(
                            os.path.join(test_out3_vrm_dir, vrm)
                        ).read_bytes()
                    ):
                        os.remove(os.path.join(test_last_vrm_dir, vrm))
                else:
                    self.run_script(
                        "blender_io.py",
                        os.path.join(test_out_vrm_dir, vrm),
                        os.path.join(test_out_vrm_dir, vrm),
                        test_temp_vrm_dir,
                    )
