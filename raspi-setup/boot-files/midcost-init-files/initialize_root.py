import shutil
from utils import run_shell_command

# =============================================================================
# CHECK FOR ROOT ACCESS (REQUIRED BY APT)

assert run_shell_command("whoami") == "root", "please run this script as ROOT user"

# =============================================================================
# INSTALL SYSTEM PACKAGES

print("INSTALLING GENERAL PACKAGES WITH APT")
run_shell_command("apt update")
run_shell_command(
    "apt install -y "
    + "software-properties-common "
    + "make "
    + "gcc "
    + "vim "
    + "git "
    + "build-essential "
    + "zlib1g-dev "
    + "libncurses5-dev "
    + "libgdbm-dev "
    + "libnss3-dev "
    + "libssl-dev "
    + "libreadline-dev "
    + "libffi-dev "
    + "libsqlite3-dev "
    + "wget "
    + "pigpio "
    + "arduino "
    + "exa "
    + "uhubctl "
    + "screen "
)

print("INSTALLING PYTHON3.9 WITH APT")
run_shell_command(
    "apt install -y "
    + "python3.9-full "
    + "python3-venv "
    + "python3-wheel "
    + "python3-setuptools "
)

print("INSTALLING VSCODE WITH APT")
run_shell_command("apt install code -y")

# =============================================================================
# CONFIGURE THE SSH DAEMON

print("ALLOWING SSH ACCESS WITH PASWORD")

with open("/etc/ssh/sshd_config", "r") as f:
    sshd_config_content = f.read()
sshd_config_content = sshd_config_content.replace(
    "#PasswordAuthentication no", "PasswordAuthentication no"
).replace("PasswordAuthentication no", "PasswordAuthentication yes")
with open("/etc/ssh/sshd_config", "w") as f:
    f.write(sshd_config_content)
run_shell_command("service ssh restart")

# =============================================================================
# ADD WIFI SETTINGS

print("ADDING WIFI SETTINGS")

# this could be done by putting the .conf file directly onto
# /boot but did not work for me
shutil.copyfile(
    "/boot/midcost-init-files/system/wpa_supplicant.conf",
    "/etc/wpa_supplicant/wpa_supplicant.conf",
)

# =============================================================================

print("✨ DONE ✨")
