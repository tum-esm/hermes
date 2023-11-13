import json
import os
import shutil
from utils import (
    run_shell_command,
    AUTOMATION_DIR,
    AUTOMATION_VERSION,
    get_hostname,
)

# =============================================================================
# CHECK That SCRIPT IS NOT RUN IN ROOT ACCESS (REQUIRED BY APT)

assert run_shell_command("whoami") == "pi", "please run this script as the PI users"

# =============================================================================
# EXTEND BASHRC FILE

print("EXTENDING BASHRC FILE")

with open("/boot/firmware/midcost-init-files/system/.bashrc", "r") as f:
    new_bashrc_lines = [l for l in f.read().split("\n") if (not l.startswith("#"))]
with open("/home/pi/.bashrc", "r") as f:
    current_bashrc_content = f.read()

with open("/home/pi/.bashrc", "a") as f:
    f.write("\n")

for line in new_bashrc_lines:
    if line not in current_bashrc_content.split("\n"):
        with open("/home/pi/.bashrc", "a") as f:
            f.write(line + "\n")

# =============================================================================
# INSTALL POETRY

print("INSTALLING POETRY")
run_shell_command("curl -sSL https://install.python-poetry.org | python3 -")

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
# INSTALL HERMES

print("SETTING UP HERMES")
# assert os.path.isdir(AUTOMATION_DIR), f"{AUTOMATION_DIR} already exist"

# download release using the github cli
print("downloading code from GitHub")
run_shell_command(
    f"wget https://github.com/tum-esm/hermes/archive/refs/tags/v{AUTOMATION_VERSION}.tar.gz"
)

# extract code archive
print("extracting tarball")
run_shell_command(f"tar -xf v{AUTOMATION_VERSION}.tar.gz")

# move sensor subdirectory
run_shell_command(f"mkdir {AUTOMATION_DIR}")
run_shell_command(f"mkdir {AUTOMATION_DIR}/{AUTOMATION_VERSION}")
run_shell_command(
    f"cp -r hermes-{AUTOMATION_VERSION}/sensor/* {AUTOMATION_DIR}/{AUTOMATION_VERSION}"
)
run_shell_command(f"rm v{AUTOMATION_VERSION}.tar.gz")
run_shell_command(f"rm -r hermes-{AUTOMATION_VERSION}")

# set up .venv
print(f"\tsetting up .venv")
run_shell_command(f"python3.9 -m venv {AUTOMATION_DIR}/{AUTOMATION_VERSION}/.venv")

print(f"\tinstalling dependencies")
run_shell_command(
    "source .venv/bin/activate && poetry install --with=dev",
    working_directory=f"{AUTOMATION_DIR}/{AUTOMATION_VERSION}",
)

print(f"\tcopying config.json")
shutil.copyfile(
    "/boot/firmware/midcost-init-files/hermes/config.json",
    f"{AUTOMATION_DIR}/{AUTOMATION_VERSION}/config/config.json",
)

print(f"\tcopying .env")
with open("/boot/firmware/midcost-init-files/hermes/hostname_to_mqtt_id.json") as f:
    hostname_to_mqtt_identifier = json.load(f)
hostname = get_hostname()
mqtt_identifier: str = hostname_to_mqtt_identifier[hostname]
with open("/boot/firmware/midcost-init-files/hermes/.env") as f:
    env_file_content = f.read()
with open(f"{AUTOMATION_DIR}/{AUTOMATION_VERSION}/config/.env", "w") as f:
    f.write(env_file_content.replace("%HERMES_MQTT_IDENTIFIER%", mqtt_identifier))

print(f"\tmaking CLI point to release version")
with open("/boot/firmware/midcost-init-files/hermes/hermes-cli.template.sh") as f:
    cli_file_content = f.read()
cli_file_content = cli_file_content.replace("%VERSION%", AUTOMATION_VERSION)
with open("/home/pi/Documents/hermes/hermes-cli.sh", "w") as f:
    f.write(cli_file_content)

# =============================================================================
# ADD CRONTAB

print(f"ADDING CRONTAB")
run_shell_command("crontab /boot/firmware/midcost-init-files/system/crontab")

# =============================================================================

print("✨ DONE ✨")
