import pytest
import subprocess


@pytest.fixture(scope="session")
def provide_mqtt_broker():
    start_process = subprocess.run(
        ["mosquitto", "-p", "1883"], stderr=subprocess.PIPE, stdout=subprocess.PIPE
    )
    if start_process.returncode != 0:
        raise Exception(
            "could not start mosquitto broker: "
            + f'stdout = "{start_process.stdout}", '
            + f'stderr = "{start_process.stderr}"'
        )

    yield

    stop_process = subprocess.run(
        ["pkill", "mosquitto"], stderr=subprocess.PIPE, stdout=subprocess.PIPE
    )
    if stop_process.returncode != 0:
        raise Exception(
            "could not stop mosquitto broker: "
            + f'stdout = "{start_process.stdout}", '
            + f'stderr = "{start_process.stderr}"'
        )
