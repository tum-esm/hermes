import os
import time
import pytest
import dotenv
import psutil
from os.path import dirname, abspath, join, isfile

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
MQTT_ENV_VARS_PATH = join(
    PROJECT_DIR,
    "config",
    ".env.testing",
)
MOSQUITTO_CONFIG_PATH = join(
    PROJECT_DIR,
    "tests",
    "software",
    "mosquitto-config.conf",
)
MOSQUITTO_PASSWORD_FILE_PATH = join(
    PROJECT_DIR,
    "tests",
    "software",
    "mosquitto-passwords.txt",
)


def _run_process(command: str) -> None:
    print(f'running command "{command}"')
    exit_code = os.system(command)
    if exit_code != 0:
        raise Exception(f"command failed with exit code {exit_code}")


def _generate_mosquitto_config_file() -> None:
    print("generating mosquitto config file")
    with open(MOSQUITTO_CONFIG_PATH, "w") as f:
        f.write(
            f"allow_anonymous false\npassword_file {MOSQUITTO_PASSWORD_FILE_PATH}",
        )


def _generate_mosquitto_password_file() -> None:
    print("generating mosquitto password file")
    if isfile(MOSQUITTO_PASSWORD_FILE_PATH):
        os.remove(MOSQUITTO_PASSWORD_FILE_PATH)
    _run_process(
        f"mosquitto_passwd -b -c {MOSQUITTO_PASSWORD_FILE_PATH} "
        + "test_user test_password",
    )


def _start_mosquitto_background_process() -> None:
    print("starting mosquitto background process")
    _run_process(
        f"mosquitto -p 1883 --daemon -c {MOSQUITTO_CONFIG_PATH}",
    )


def _stop_mosquitto_background_process() -> None:
    print("stopping mosquitto background process")
    killed_process_count = 0
    for p in psutil.process_iter():
        try:
            if "mosquitto" in p.exe():
                p.kill()
                print(f"killed process with PID {p.pid}")
                killed_process_count += 1
        except:
            pass


@pytest.fixture(scope="session")
def provide_mqtt_broker():
    _generate_mosquitto_config_file()
    _generate_mosquitto_password_file()
    _start_mosquitto_background_process()

    # load testing environment variables
    # used by all clients in code
    dotenv.load_dotenv(MQTT_ENV_VARS_PATH)

    time.sleep(2)

    yield

    _stop_mosquitto_background_process()


if __name__ == "__main__":
    _generate_mosquitto_config_file()
    _generate_mosquitto_password_file()
    _start_mosquitto_background_process()
    _stop_mosquitto_background_process()
