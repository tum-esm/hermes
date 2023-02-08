import os
from utils import run_shell_command, IP_LOGGER_DIR, AUTOMATION_DIR, AUTOMATION_VERSION

# =============================================================================
# TEST BASEROW-IP-LOGGER

os.system(
    f"cd {IP_LOGGER_DIR} && .venv/bn/python run.py",
)

# =============================================================================
# TEST HERMES

os.system(
    f"cd {AUTOMATION_DIR}/{AUTOMATION_VERSION} && "
    + '.venv/bn/python -m pytest -m "version_update"',
)
