import shutil
from utils import run_shell_command

# =============================================================================
# CHECK FOR ROOT ACCESS (REQUIRED BY APT)

assert run_shell_command("whoami") == "root", "please run this script as ROOT user"

# =============================================================================
# INSTALL SYSTEM PACKAGES

print("UPATING RASPBERRYPI")
run_shell_command("sudo apt-get update")
print("UPDATING HEADERS")
run_shell_command("sudo apt install raspberrypi-kernel-headers")

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
    + "p7zip-full "
    + "minicom "
    + "udhcpc "
)

# =============================================================================

print("INSTALLING VSCODE WITH APT")
run_shell_command("apt install code -y")

# =============================================================================

print("✨ DONE ✨")
