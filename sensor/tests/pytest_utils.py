from datetime import datetime
import os
from os.path import dirname, abspath, join
import time
from typing import Callable

PROJECT_DIR = dirname(dirname(abspath(__file__)))
LOG_FILE = join(
    PROJECT_DIR, "logs", "archive", datetime.now().strftime("%Y-%m-%d.log")
)


def expect_log_file_contents(
    required_content_blocks: list[str] = [],
    forbidden_content_blocks: list[str] = [],
) -> None:
    assert os.path.isfile(LOG_FILE), f"log file not found at {LOG_FILE}"
    with open(LOG_FILE, "r") as f:
        file_content = f.read()

    for b in required_content_blocks:
        assert b in file_content, f'required log content block not found "{b}"'

    for b in forbidden_content_blocks:
        assert b not in file_content, f'forbidden log content block found "{b}"'


def wait_for_condition(
    is_successful: Callable[[], bool],
    timeout_message: str,
    timeout_seconds: float = 5,
) -> None:
    start_time = time.time()
    while True:
        if is_successful():
            break
        if (time.time() - start_time) > timeout_seconds:
            raise TimeoutError(timeout_message)
        time.sleep(0.25)
