import atexit
import os
import signal
import threading
import time


def terminate_self_thread() -> None:
    time.sleep(10)
    os.kill(os.getpid(), signal.SIGINT)


def call_terminate_self() -> None:
    threading.Thread(target=terminate_self_thread)


atexit.register(call_terminate_self)
