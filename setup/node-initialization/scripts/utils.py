import subprocess
import os
from typing import Optional

ENV = os.environ.copy()
ENV["PATH"] = "/home/pi/bin:/home/pi/.local/bin:" + ENV["PATH"]
ENV["PYTHON_KEYRING_BACKEND"] = "keyring.backends.null.Keyring"
AUTOMATION_VERSION = "0.2.0-beta.9"
AUTOMATION_DIR = "/home/pi/Documents/hermes"
IP_LOGGER_DIR = "/home/pi/Documents/baserow-ip-logger"


def run_shell_command(
    command: str,
    working_directory: Optional[str] = "/home/pi",
    check_exit_code: bool = True,
) -> str:
    p = subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=working_directory,
        env=ENV,
        executable="/bin/bash",
    )
    stdout = p.stdout.decode("utf-8", errors="replace").strip()
    stderr = p.stderr.decode("utf-8", errors="replace").strip()
    if check_exit_code:
        assert p.returncode == 0, (
            f"command '{command}' failed with exit code "
            + f"{p.returncode}: stderr = '{stderr}'"
        )
        return stdout
    else:
        # only used for SSH access test
        return stdout + stderr


def get_hostname() -> str:
    raw_hostname = run_shell_command("hostname")
    if "." in raw_hostname:
        return raw_hostname.split(".")[0]
    else:
        return raw_hostname
