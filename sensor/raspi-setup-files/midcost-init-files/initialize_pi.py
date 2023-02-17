import json
import os
import shutil
from utils import (
    run_shell_command,
    IP_LOGGER_DIR,
    AUTOMATION_DIR,
    AUTOMATION_VERSION,
    get_hostname,
)

# =============================================================================
# CHECK FOR ROOT ACCESS (REQUIRED BY APT)

assert run_shell_command("whoami") == "pi", "please run this script as the PI users"

# =============================================================================
# EXTEND BASHRC FILE

print("EXTENDING BASHRC FILE")

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

print("INSTALLING POETRY")
run_shell_command("curl -sSL https://install.python-poetry.org | python3 -")

print("INSTALLING ARDUINO CLI")
run_shell_command(
    "curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh"
)

print("INSTALLING ARDUINO CLI CHIPSETS")
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

print("INSTALLING VSCODE EXTENSIONS")

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

print("SETTING UP SSH")

print(f"\tcopying files")
if not os.path.isdir("/home/pi/.ssh"):
    os.mkdir("/home/pi/.ssh")
for src, dst in [
    (
        "/boot/midcost-init-files/ssh/authorized_keys",
        "/home/pi/.ssh/authorized_keys",
    ),
    (
        "/boot/midcost-init-files/ssh/id_ed25519_esm_technical_user",
        "/home/pi/.ssh/id_ed25519_esm_technical_user",
    ),
    (
        "/boot/midcost-init-files/ssh/id_ed25519_esm_technical_user.pub",
        "/home/pi/.ssh/id_ed25519_esm_technical_user.pub",
    ),
    (
        "/boot/midcost-init-files/ssh/config",
        "/home/pi/.ssh/config",
    ),
]:
    if not os.path.isfile(dst):
        shutil.copyfile(src, dst)

print(f"\tadding ssh key to agent")
run_shell_command("chmod 600 /home/pi/.ssh/id_ed25519_esm_technical_user")
run_shell_command("chmod 600 /home/pi/.ssh/id_ed25519_esm_technical_user.pub")
run_shell_command("eval `ssh-agent -s`")
run_shell_command("ssh-add /home/pi/.ssh/id_ed25519_esm_technical_user")

print(f"\ttesting access to github")
github_ssh_response = run_shell_command(
    'ssh -o "StrictHostKeyChecking accept-new" -T git@github.com',
    check_exit_code=False,
)
assert (
    "You've successfully authenticated" in github_ssh_response
), "GitHub Authentication failed"

# =============================================================================
# INSTALL BASEROW-IP-LOGGER

print("SETTING UP BASEROW-IP-LOGGER")

# remove old baserow-ip-logger
if os.path.isdir(IP_LOGGER_DIR):
    shutil.rmtree(IP_LOGGER_DIR)

print(f"\tcloning repository")
run_shell_command(
    "git clone git@github.com:dostuffthatmatters/baserow-ip-logger.git " + IP_LOGGER_DIR
)

print(f"\tsetting up .venv")
run_shell_command(f"python3.9 -m venv {IP_LOGGER_DIR}/.venv")

print(f"\tinstalling dependencies")
run_shell_command(
    "source .venv/bin/activate && poetry install",
    working_directory=IP_LOGGER_DIR,
)

print(f"\tcopying config.json")
shutil.copyfile(
    "/boot/midcost-init-files/baserow-ip-logger/config.json",
    f"{IP_LOGGER_DIR}/config.json",
)

# =============================================================================
# INSTALL HERMES

print("SETTING UP HERMES")
assert not os.path.isdir(AUTOMATION_DIR), f"{AUTOMATION_DIR} already exist"
TMP_AUTOMATION_DIR = "/tmp/automation-dir"

print(f"\tcloning into tmp dir {TMP_AUTOMATION_DIR}")
run_shell_command(
    "git clone git@github.com:tum-esm/hermes.git " + f"{TMP_AUTOMATION_DIR}"
)

print(f"\tchecking out tag v{AUTOMATION_VERSION}")
run_shell_command(
    f"git checkout v{AUTOMATION_VERSION}",
    working_directory=f"{TMP_AUTOMATION_DIR}",
)

print(f"\tcopying sensor subdirectory")
shutil.copytree(
    f"{TMP_AUTOMATION_DIR}/sensor", f"{AUTOMATION_DIR}/{AUTOMATION_VERSION}"
)
shutil.rmtree(TMP_AUTOMATION_DIR)

print(f"\tsetting up .venv")
run_shell_command(f"python3.9 -m venv {AUTOMATION_DIR}/{AUTOMATION_VERSION}/.venv")

print(f"\tinstalling dependencies")
run_shell_command(
    "source .venv/bin/activate && poetry install --with=dev",
    working_directory=f"{AUTOMATION_DIR}/{AUTOMATION_VERSION}",
)

print(f"\tcopying config.json")
shutil.copyfile(
    "/boot/midcost-init-files/hermes/config.json",
    f"{AUTOMATION_DIR}/{AUTOMATION_VERSION}/config/config.json",
)

print(f"\tcopying .env")
with open("/boot/midcost-init-files/hermes/hostname_to_mqtt_id.json") as f:
    hostname_to_mqtt_identifier = json.load(f)
hostname = get_hostname()
mqtt_identifier: str = hostname_to_mqtt_identifier[hostname]
with open("/boot/midcost-init-files/hermes/.env") as f:
    env_file_content = f.read()
with open(f"{AUTOMATION_DIR}/{AUTOMATION_VERSION}/config/.env", "w") as f:
    f.write(env_file_content.replace("%HERMES_MQTT_IDENTIFIER%", mqtt_identifier))

print(f"\tmaking CLI point to release version")
with open("/boot/midcost-init-files/hermes/hermes-cli.template.sh") as f:
    cli_file_content = f.read()
cli_file_content = cli_file_content.replace("%VERSION%", AUTOMATION_VERSION)
with open("/home/pi/Documents/hermes/hermes-cli.sh", "w") as f:
    f.write(cli_file_content)

# =============================================================================
# ADD CRONTAB

print(f"ADDING CRONTAB")
run_shell_command("crontab /boot/midcost-init-files/system/crontab")

# =============================================================================

print("✨ DONE ✨")
