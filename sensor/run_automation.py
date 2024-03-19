import dotenv
import os
from os.path import dirname
import filelock
from src import main

ROOT_DIR = dirname(dirname(os.path.abspath(__file__)))
PROJECT_DIR = dirname(os.path.abspath(__file__))


# Modifies the dotenv file to add the prefix "HERMES_" to all keys that don't have it,
# while also preserving the original keys
def update_dotenv(dotenv_path: str) -> None:
    # skip if dotenv doesn't exist
    if not os.path.exists(dotenv_path):
        return

    with open(dotenv_path, "r") as file:
        # read all lines
        data = file.readlines()

        hermes_vars = [line for line in data if line.strip().startswith("HERMES_")]

        new_file = []
        # add the prefix "HERMES_" to all keys that don't have it
        for i, line in enumerate(data):
            if line.strip() and not line.endswith("\n"):
                line += "\n"

            new_file.append(line)
            if line.startswith("HERMES_"):
                continue
            # skip lines with whitespace or comments
            if not line.strip() or line.strip().startswith("#"):
                continue

            if not ("HERMES_" + line) in hermes_vars:
                new_file.append("HERMES_" + line)

    with open(dotenv_path, "w") as file:
        file.writelines(new_file)


if __name__ == "__main__":
    update_dotenv(os.path.join(PROJECT_DIR, "config", ".env"))
    dotenv.load_dotenv(os.path.join(PROJECT_DIR, "config", ".env"))
    lock = filelock.FileLock(os.path.join(ROOT_DIR, "run_automation.lock"), timeout=2)

    try:
        with lock:
            main.run()
    except filelock.Timeout:
        raise TimeoutError("automation is already running")



