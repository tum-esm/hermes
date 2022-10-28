import click
import os
import psutil

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))
INTERPRETER_PATH = os.path.join(PROJECT_DIR, ".venv", "bin", "python")
SCRIPT_PATH = os.path.join(PROJECT_DIR, "run.py")


def print_green(text: str) -> None:
    click.echo(click.style(text, fg="green"))


def print_red(text: str) -> None:
    click.echo(click.style(text, fg="red"))


def process_is_running() -> int | None:
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
