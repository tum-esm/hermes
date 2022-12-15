import pytest
from ..pytest_fixtures import log_files
from os.path import dirname, abspath, join
import sys

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
LOG_FILE = join(PROJECT_DIR, "logs", "current-logs.log")
sys.path.append(PROJECT_DIR)

from src import utils


# TODO: test whether logger enqueues and sends mqtt messages


@pytest.mark.dev
@pytest.mark.ci
def test_logger(log_files: None) -> None:
    expected_lines = [
        "pytests - DEBUG - some message a",
        "pytests - INFO - some message b",
        "pytests - WARNING - some message c",
        "pytests - ERROR - some message d",
    ]

    with open(LOG_FILE, "r") as f:
        file_content = f.read()
        for l in expected_lines:
            assert l not in file_content

    logger = utils.Logger(origin="pytests")
    logger.debug("some message a")
    logger.info("some message b")
    logger.warning("some message c")
    logger.error("some message d")

    with open(LOG_FILE, "r") as f:
        file_content = f.read()
        for l in expected_lines:
            assert l in file_content
