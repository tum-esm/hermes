import shutil
import os
from utils import run_shell_command, IP_LOGGER_DIR, AUTOMATION_DIR, AUTOMATION_TAG


# =============================================================================
# EXTEND BASHRC FILE

with open("/boot/midcost-init-files/system/.bashrc", "r") as f:
    new_bashrc_lines = [l for l in f.read().split("\n") if (not l.startswith("#"))]
with open("~/.bashrc", "r") as f:
    current_bashrc_content = f.read()
for l in new_bashrc_lines:
    if l not in current_bashrc_content:
        with open("~/.bashrc", "a") as f:
            f.write(f"\n\n{l}\n")

# =============================================================================
# INSTALL SYSTEM PACKAGES

print("Installing General Apt Packages")
run_shell_command("apt update")
run_shell_command(
    "apt install software-properties-common make gcc vim git build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget pigpio arduino exa -y"
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

# =============================================================================
# SET UP SSH

# Add SSH files
for src, dst in [
    (
        "/boot/midcost-init-files/ssh/authorized_keys",
        "/hom/pi/.ssh/authorized_keys",
    ),
    (
        "/boot/midcost-init-files/ssh/id_ed25519_esm_technical_user",
        "/hom/pi/.ssh/id_ed25519_esm_technical_user",
    ),
    (
        "/boot/midcost-init-files/ssh/id_ed25519_esm_technical_user.pub",
        "/hom/pi/.ssh/id_ed25519_esm_technical_user.pub",
    ),
    (
        "/boot/midcost-init-files/ssh/config.txt",
        "/hom/pi/.ssh/config.txt",
    ),
]:
    if not os.path.isfile(dst):
        shutil.copyfile(src, dst)

# configure the SSH daemon
print("Allow password access via SSH")
with open("/etc/ssh/sshd_config", "r") as f:
    sshd_config_content = f.read()
sshd_config_content = sshd_config_content.replace(
    "#PasswordAuthentication no", "PasswordAuthentication no"
).replace("PasswordAuthentication no", "PasswordAuthentication yes")
with open("/etc/ssh/sshd_config", "w") as f:
    f.write(sshd_config_content)
run_shell_command("service ssh restart")

# test SSH keys with GitHub
gihub_ssh_response = run_shell_command(
    'ssh -o "StrictHostKeyChecking accept-new" -T git@github.com',
    check_exit_code=False,
)
assert (
    "You've successfully authenticated" in gihub_ssh_response
), "GitHub Authentication failed"

# =============================================================================
# INSTALL BASEROW-IP-LOGGER

# remove old baserow-ip-logger
if os.path.isdir(IP_LOGGER_DIR):
    shutil.rmtree(IP_LOGGER_DIR)

# install baserow-ip-logger
run_shell_command(
    "git clone git@github.com:dostuffthatmatters/baserow-ip-logger.git " + IP_LOGGER_DIR
)
run_shell_command(f"python3.9 -m venv {IP_LOGGER_DIR}/.venv")
run_shell_command(
    "source .venv/bin/activate && poetry install",
    working_directory=IP_LOGGER_DIR,
)
shutil.copyfile(
    "/boot/midcost-init-files/baserow-ip-logger/config.json",
    f"{IP_LOGGER_DIR}/config.json",
)

# =============================================================================
# INSTALL INSERT-NAME-HERE

assert not os.path.isdir(AUTOMATION_DIR)
TMP_AUTOMATION_DIR = "/tmp/automation-dir"

# download a specific tag via SSH
run_shell_command(
    "git clone git@github.com:tum-esm/insert-name-here.git " + f"{TMP_AUTOMATION_DIR}"
)
run_shell_command(
    f"git checkout {AUTOMATION_TAG}",
    working_directory=f"{TMP_AUTOMATION_DIR}",
)
shutil.copytree(f"{TMP_AUTOMATION_DIR}/sensor", f"{AUTOMATION_DIR}/{AUTOMATION_TAG}")
shutil.rmtree(TMP_AUTOMATION_DIR)

# install dependencies
run_shell_command(f"python3.9 -m venv {AUTOMATION_DIR}/{AUTOMATION_TAG}/.venv")
run_shell_command(
    "source .venv/bin/activate && poetry install",
    working_directory=f"{AUTOMATION_DIR}/{AUTOMATION_TAG}",
)

# copy config files
shutil.copyfile(
    "/boot/midcost-init-files/insert-name-here/config.json",
    f"{AUTOMATION_DIR}/{AUTOMATION_TAG}/config/config.json",
)
shutil.copyfile(
    "/boot/midcost-init-files/insert-name-here/.env",
    f"{AUTOMATION_DIR}/{AUTOMATION_TAG}/config/.env",
)

# make CLI point to release version
with open(
    "/boot/midcost-init-files/insert-name-here/insert-name-here-cli.template.sh"
) as f:
    cli_file_content = f.read()
cli_file_content = cli_file_content.replace("%VERSION%", AUTOMATION_TAG)
with open("/home/pi/insert-name-here/insert-name-here-cli.sh", "w") as f:
    f.write(cli_file_content)

# =============================================================================
# ADD CRONTAB

run_shell_command("crontab /boot/midcost-init-files/system/crontab")
