import os
import pytest
import subprocess
from os.path import dirname, abspath, join, isfile

PARENT_DIR = dirname(abspath(__file__))
MOSQUITTO_CONFIG_PATH = join(PARENT_DIR, "mosquitto-config.conf")
MOSQUITTO_PASSWORD_FILE_PATH = join(PARENT_DIR, "mosquitto-passwords.txt")


@pytest.fixture(scope="session")
def provide_mqtt_broker():
    # generate mosquitto config file
    with open(MOSQUITTO_CONFIG_PATH, "w") as f:
        f.write(
            f"allow_anonymous false\npassword_file {MOSQUITTO_PASSWORD_FILE_PATH}",
        )

    # remove old password file
    if isfile(MOSQUITTO_PASSWORD_FILE_PATH):
        os.remove(MOSQUITTO_PASSWORD_FILE_PATH)

    # generate new password file
    password_process = subprocess.run(
        [
            "mosquitto_passwd",
            MOSQUITTO_PASSWORD_FILE_PATH,
            "test_user",
            "test_password",
        ],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    if password_process.returncode != 0:
        raise Exception(
            "could not generate password file: "
            + f'stdout = "{start_process.stdout}", '
            + f'stderr = "{start_process.stderr}"'
        )

    # start mosquitto background process
    start_process = subprocess.run(
        [
            "mosquitto",
            "-p",
            "1883",
            "--daemon",
            "-c",
            MOSQUITTO_CONFIG_PATH,
        ],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    if start_process.returncode != 0:
        raise Exception(
            "could not start mosquitto broker: "
            + f'stdout = "{start_process.stdout}", '
            + f'stderr = "{start_process.stderr}"'
        )

    # TODO: load test env file

    yield

    stop_process = subprocess.run(
        [
            "pkill",
            "mosquitto",
        ],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    if stop_process.returncode != 0:
        raise Exception(
            "could not stop mosquitto broker: "
            + f'stdout = "{start_process.stdout}", '
            + f'stderr = "{start_process.stderr}"'
        )
