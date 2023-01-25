import shutil
import subprocess
import os
from typing import Optional

ENV = os.environ.copy()
ENV["PATH"] = "/home/pi/bin:/home/pi/.local/bin:" + ENV["PATH"]


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


# add `/home/pi/bin` to PATH variable

new_bashrc_line = 'export PATH="/home/pi/bin:/home/pi/.local/bin:$PATH"'
with open("~/.bashrc", "r") as f:
    file_content = f.read()
if new_bashrc_line not in file_content:
    with open("~/.bashrc", "a") as f:
        f.write(f"\n\n{new_bashrc_line}\n")

# install dependencies
print("Installing General Apt Packages")
run_shell_command("apt update")
run_shell_command(
    "apt install software-properties-common make gcc vim git build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget pigpio arduino -y"
)

print("Installing Python3.9 via Apt")
run_shell_command("apt python3.9-full python3-venv python3-wheel python3-setuptools -y")

print("Installing Poetry")
run_shell_command("curl -sSL https://install.python-poetry.org | python3 -")

print("Installing Arduino CLI")
run_shell_command(
    "curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh"
)

print("Installing Arduino CLI Chipsets")
run_shell_command("arduino-cli core install arduino:avr")

print("Installing VS Code via Apt")
run_shell_command("apt install code -y")

print("Installing VS Code Extensions")
run_shell_command(
    "code --install-extension whatwewant.open-terminal --install-extension ms-python.python --install-extension VisualStudioExptTeam.vscodeintellicode --install-extension donjayamanne.python-environment-manager --install-extension bungcip.better-toml --install-extension yzhang.markdown-all-in-one --install-extension  christian-kohler.path-intellisense --install-extension ms-vscode.vscode-serial-monitor --install-extension Gruntfuggly.todo-tree --install-extension AnchovyStudios.zip-extract-all"
)

# Add SSH config and test GitHub Access to ESM Technical User
for src, dst in [
    (
        "/boot/midcost-init-files/ssh_id_ed25519_esm_technical_user",
        "/hom/pi/.ssh/id_ed25519_esm_technical_user",
    ),
    (
        "/boot/midcost-init-files/ssh_id_ed25519_esm_technical_user.pub",
        "/hom/pi/.ssh/id_ed25519_esm_technical_user.pub",
    ),
    (
        "/boot/midcost-init-files/ssh_config.txt",
        "/hom/pi/.ssh/config.txt",
    ),
]:
    if not os.path.isfile(dst):
        shutil.copyfile(src, dst)

# test SSH keys with GitHub
gihub_ssh_response = run_shell_command(
    'ssh -o "StrictHostKeyChecking accept-new" -T git@github.com',
    check_exit_code=False,
)
assert (
    "You've successfully authenticated" in gihub_ssh_response
), "GitHub Authentication failed"

# installing new crontab
run_shell_command("crontab /boot/midcost-init-files/crontab")
