import dotenv
import os
from os.path import dirname
import filelock
from src import main

ROOT_DIR = dirname(dirname(os.path.abspath(__file__)))
PROJECT_DIR = dirname(os.path.abspath(__file__))


def update_dotenv(dotenv_path: str) -> None:
    # skip if dotenv doesn't exist
    if not os.path.exists(dotenv_path):
        return

    with open(dotenv_path, "r") as file:
        # read all lines
        data = file.readlines()

        # add the prefix "HERMES_" to all keys that don't have it
        for i, line in enumerate(data):
            if line.startswith("HERMES_"):
                continue
            # skip lines with whitespace or comments
            if not line.strip() or line.strip().startswith("#"):
                continue

            data[i] = "HERMES_" + line

    with open(dotenv_path, "w") as file:
        file.writelines(data)


if __name__ == "__main__":
    update_dotenv(os.path.join(PROJECT_DIR, "config", ".env"))
    dotenv.load_dotenv(os.path.join(PROJECT_DIR, "config", ".env"))
    lock = filelock.FileLock(os.path.join(ROOT_DIR, "run_automation.lock"), timeout=2)

    try:
        with lock:
            main.run()
    except filelock.Timeout:
        raise TimeoutError("automation is already running")



