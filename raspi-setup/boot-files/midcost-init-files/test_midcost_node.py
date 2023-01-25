from utils import run_shell_command, IP_LOGGER_DIR, AUTOMATION_DIR, AUTOMATION_TAG

# =============================================================================
# TEST BASEROW-IP-LOGGER

run_shell_command(
    '.venv/bn/python -m pytest -m "integration"',
    working_directory=f"{IP_LOGGER_DIR}",
)

# =============================================================================
# TEST INSERT-NAME-HERE

run_shell_command(
    '.venv/bn/python -m pytest -m "integration"',
    working_directory=f"{AUTOMATION_DIR}/{AUTOMATION_TAG}",
)
