import os
import pytest
import subprocess
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


def run_process(command: list[str]) -> None:
    p = subprocess.run(
        command,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    if p.returncode != 0:
        raise Exception(
            "could not generate password file: "
            + f'stdout = "{p.stdout}", '
            + f'stderr = "{p.stderr}"'
        )


def generate_mosquitto_config_file() -> None:
    with open(MOSQUITTO_CONFIG_PATH, "w") as f:
        f.write(
            f"allow_anonymous false\npassword_file {MOSQUITTO_PASSWORD_FILE_PATH}",
        )


def generate_mosquitto_password_file() -> None:
    # remove old password file
    if isfile(MOSQUITTO_PASSWORD_FILE_PATH):
        os.remove(MOSQUITTO_PASSWORD_FILE_PATH)
    run_process(
        [
            "mosquitto_passwd",
            "-b",
            "-c",
            MOSQUITTO_PASSWORD_FILE_PATH,
            "test_user",
            "test_password",
        ]
    )


def start_mosquitto_background_process() -> None:
    run_process(
        [
            "mosquitto",
            "-p",
            "1883",
            "--daemon",
            "-c",
            MOSQUITTO_CONFIG_PATH,
        ]
    )


def stop_mosquitto_background_process() -> None:
    killed_process_count = 0
    for p in psutil.process_iter():
        try:
            if "mosquitto" in p.exe():
                p.kill()
                print(f"killed process with PID {p.pid}")
                killed_process_count += 1
        except:
            pass
    assert killed_process_count == 1, "killed no or more than two mosquitto processes"


@pytest.fixture(scope="session")
def provide_mqtt_broker():
    generate_mosquitto_config_file()
    generate_mosquitto_password_file()
    start_mosquitto_background_process()

    # load testing environment variables
    # used by all clients in code
    dotenv.load_dotenv(MQTT_ENV_VARS_PATH)

    yield

    stop_mosquitto_background_process()
