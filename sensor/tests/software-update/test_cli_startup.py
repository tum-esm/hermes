import os
import pytest
import os
from os.path import dirname
import pytest
from src import utils


PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
INTERPRETER_PATH = os.path.join(PROJECT_DIR, ".venv", "bin", "python")
CLI_PATH = os.path.join(PROJECT_DIR, "cli", "main.py")


@pytest.mark.parameter_update
@pytest.mark.version_update
def test_cli_startup() -> None:
    """run the hermes-cli info command"""
    stdout = utils.run_shell_command(
        " ".join([INTERPRETER_PATH, CLI_PATH, "info"]),
        working_directory=PROJECT_DIR,
    )
    stdout_lines = stdout.split("\n")
    assert len(stdout_lines) == 2

    assert stdout_lines[0] == f"Using Python interpreter at: {INTERPRETER_PATH}"
    assert stdout_lines[1] == f"Using sensor code at: {PROJECT_DIR}"
