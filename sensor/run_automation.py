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

            # keep existing lines in the config file, we're only adding new ones if necessary
            new_file.append(line)

            # add HERMES_MQTT_ variables if they don't exist (and leave the original HERMES_MOSQUITTO_ variables)
            if line.startswith("HERMES_MOSQUITTO_"):
                fixed_mqtt_line = line.replace("HERMES_MOSQUITTO_", "HERMES_MQTT_")
                if fixed_mqtt_line not in hermes_vars:
                    new_file.append(fixed_mqtt_line)

            # skip lines that already have the prefix
            if line.startswith("HERMES_"):
                continue
            # skip lines consisting only of whitespace or comments
            if not line.strip() or line.strip().startswith("#"):
                continue

            # the remaining lines are missing the prefix
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
