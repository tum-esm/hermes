import subprocess
import os
from typing import Optional

ENV = os.environ.copy()
ENV["PATH"] = "/home/pi/bin:/home/pi/.local/bin:" + ENV["PATH"]
AUTOMATION_TAG = "0.1.0-beta.1"
AUTOMATION_DIR = "/home/pi/Documents/hermes"
IP_LOGGER_DIR = "/home/pi/Documents/baserow-ip-logger"


def run_shell_command(
    command: str,
    working_directory: Optional[str] = None,
    check_exit_code: bool = True,
) -> str:
    p = subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=working_directory,
        env=ENV,
        working_directory="/home/pi",
    )
    stdout = p.stdout.decode("utf-8", errors="replace")
    stderr = p.stderr.decode("utf-8", errors="replace")
    if check_exit_code:
        assert p.returncode == 0, (
            f"command '{command}' failed with exit code "
            + f"{p.returncode}: stderr = '{stderr}'"
        )
    return stdout.strip()
