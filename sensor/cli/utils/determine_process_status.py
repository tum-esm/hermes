from typing import Optional
import os
import psutil

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
INTERPRETER_PATH = os.path.join(PROJECT_DIR, ".venv", "bin", "python")
SCRIPT_PATH = os.path.join(PROJECT_DIR, "run.py")


def process_is_running() -> Optional[int]:
    for p in psutil.process_iter():
        try:
            arguments = p.cmdline()
            if (len(arguments) >= 2) and (arguments[1] == SCRIPT_PATH):
                return p.pid
        except (psutil.AccessDenied, psutil.ZombieProcess, psutil.NoSuchProcess):
            pass
    return None


def terminate_processes() -> list[int]:
    termination_pids: list[int] = []
    for p in psutil.process_iter():
        try:
            arguments = p.cmdline()
            if len(arguments) > 0:
                if SCRIPT_PATH in arguments:
                    termination_pids.append(p.pid)
                    p.terminate()
        except (psutil.AccessDenied, psutil.ZombieProcess, psutil.NoSuchProcess):
            pass
    return termination_pids
