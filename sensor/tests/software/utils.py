from os.path import dirname, abspath, join

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
LOG_FILE = join(PROJECT_DIR, "logs", "current-logs.log")


def expect_log_lines(required_lines: list[str] = [], forbidden_lines: list[str] = []):
    with open(LOG_FILE, "r") as f:
        file_content = f.read()

    for l in required_lines:
        assert l in file_content, f'required log line not found "{l}"'

    for l in forbidden_lines:
        assert l not in file_content, f'forbidden log line found "{l}"'
