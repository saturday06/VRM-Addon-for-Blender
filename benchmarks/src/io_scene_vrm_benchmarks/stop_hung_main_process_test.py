import atexit
import os
import platform
import subprocess


def stop_hung_main_process() -> None:
    if platform.system() != "Linux" or os.environ.get("CI") != "true":
        return

    pid = os.getpid()
    subprocess.Popen(
        [
            "/bin/sh",
            "-c",
            f"sleep 120; kill {pid:d}",
        ],
        start_new_session=True,
    )


atexit.register(stop_hung_main_process)
