from os.path import dirname, abspath, join
import time
from typing import Callable

PROJECT_DIR = dirname(dirname(abspath(__file__)))
LOG_FILE = join(PROJECT_DIR, "logs", "current-logs.log")


def expect_log_lines(
    required_lines: list[str] = [], forbidden_lines: list[str] = []
) -> None:
    with open(LOG_FILE, "r") as f:
        file_content = f.read()

    for l in required_lines:
        assert l in file_content, f'required log line not found "{l}"'

    for l in forbidden_lines:
        assert l not in file_content, f'forbidden log line found "{l}"'


def wait_for_condition(
    is_successful: Callable[[], bool], timeout_message: str, timeout_seconds: float = 5
) -> None:
    start_time = time.time()
    while True:
        if is_successful():
            break
        if (time.time() - start_time) > timeout_seconds:
            raise TimeoutError(timeout_message)
        time.sleep(0.1)
