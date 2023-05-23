import time
import os
from typing import Callable
import psutil
import click

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(os.path.abspath(__file__)))
INTERPRETER_PATH = os.path.join(PROJECT_DIR, ".venv", "bin", "python")
SCRIPT_PATH = os.path.join(PROJECT_DIR, "run_automation.py")


def print_green(text: str) -> None:
    click.echo(click.style(text, fg="green"))


def print_red(text: str) -> None:
    click.echo(click.style(text, fg="red"))


def get_process_pids() -> list[int]:
    pids: list[int] = []
    for p in psutil.process_iter():
        try:
            if (SCRIPT_PATH == os.path.join(p.cwd(), p.cmdline()[-1])) or (
                SCRIPT_PATH == p.cmdline()[-1]
            ):
                pids.append(p.pid)
        except:
            pass
    return pids


def terminate_processes() -> list[int]:
    pids: list[int] = get_process_pids()
    pid_is_still_running: Callable[[int], bool] = lambda pid: psutil.pid_exists(pid)

    # gently ask processes to terminate by sending SIGTERM
    for pid in pids:
        os.system(f"kill {pid}")

    waiting_start_time = time.time()
    while True:
        if time.time() - waiting_start_time > 10:
            break
        if any(map(pid_is_still_running, pids)):
            time.sleep(1)
        else:
            break

    # force killing processes that are still running 10
    # seconds after sending SIGTERM
    for pid in pids:
        if pid_is_still_running(pid):
            os.system(f"kill -9 {pid}")

    return pids
