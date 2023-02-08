import json
import os
import shutil
from utils import (
    run_shell_command,
    IP_LOGGER_DIR,
    AUTOMATION_DIR,
    AUTOMATION_TAG,
    get_hostname,
)

# =============================================================================
# CHECK FOR ROOT ACCESS (REQUIRED BY APT)

assert run_shell_command("whoami") == "pi", "please run this script as the PI users"

# =============================================================================
# EXTEND BASHRC FILE

with open("/boot/midcost-init-files/system/.bashrc", "r") as f:
    new_bashrc_lines = [l for l in f.read().split("\n") if (not l.startswith("#"))]
with open("/home/pi/.bashrc", "r") as f:
    current_bashrc_content = f.read()
for l in new_bashrc_lines:
    if l not in current_bashrc_content:
        with open("/home/pi/.bashrc", "a") as f:
            f.write(f"\n\n{l}\n")

# =============================================================================
# INSTALL POETRY AND ARDUINO CLI

print("Installing Poetry")
run_shell_command("curl -sSL https://install.python-poetry.org | python3 -")

print("Installing Arduino CLI")
run_shell_command(
    "curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh"
)

print("Installing Arduino CLI Chipsets")
run_shell_command("arduino-cli core install arduino:avr")

# =============================================================================
# ADD GLOBAL GIT SETTINGS

run_shell_command('git config --global core.editor "vim"')
run_shell_command('git config --global core.commentChar "$"')
run_shell_command('git config --global user.name "ESM Technical User"')
run_shell_command('git config --global user.email "esm-technical-user@protonmail.com"')
run_shell_command("git config --global pull.ff only")

# =============================================================================
# ADD VSCODE EXTENSIONS

print("Installing VS Code Extensions")
run_shell_command(
    "code "
    + "--install-extension whatwewant.open-terminal "
    + "--install-extension ms-python.python "
    + "--install-extension VisualStudioExptTeam.vscodeintellicode "
    + "--install-extension donjayamanne.python-environment-manager "
    + "--install-extension bungcip.better-toml "
    + "--install-extension yzhang.markdown-all-in-one "
    + "--install-extension christian-kohler.path-intellisense "
    + "--install-extension ms-vscode.vscode-serial-monitor "
    + "--install-extension Gruntfuggly.todo-tree "
    + "--install-extension AnchovyStudios.zip-extract-all"
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
# INSTALL HERMES

assert not os.path.isdir(AUTOMATION_DIR)
TMP_AUTOMATION_DIR = "/tmp/automation-dir"

# download a specific tag via SSH
run_shell_command(
    "git clone git@github.com:tum-esm/hermes.git " + f"{TMP_AUTOMATION_DIR}"
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
    "source .venv/bin/activate && poetry install --with=dev",
    working_directory=f"{AUTOMATION_DIR}/{AUTOMATION_TAG}",
)

# copy config.json
shutil.copyfile(
    "/boot/midcost-init-files/hermes/config.json",
    f"{AUTOMATION_DIR}/{AUTOMATION_TAG}/config/config.json",
)

# copy .env
with open("/boot/midcost-init-files/hermes/hostname_to_mqtt_id.json") as f:
    hostname_to_mqtt_identifier = json.load(f)
hostname = get_hostname()
mqtt_identifier: str = hostname_to_mqtt_identifier[hostname]
with open("/boot/midcost-init-files/hermes/.env") as f:
    env_file_content = f.read()
with open(f"{AUTOMATION_DIR}/{AUTOMATION_TAG}/config/.env", "w") as f:
    f.write(env_file_content.replace("%HERMES_MQTT_IDENTIFIER%", mqtt_identifier))

# make CLI point to release version
with open("/boot/midcost-init-files/hermes/hermes-cli.template.sh") as f:
    cli_file_content = f.read()
cli_file_content = cli_file_content.replace("%VERSION%", AUTOMATION_TAG)
with open("/home/pi/hermes/hermes-cli.sh", "w") as f:
    f.write(cli_file_content)

# =============================================================================
# ADD CRONTAB

run_shell_command("crontab /boot/midcost-init-files/system/crontab")
