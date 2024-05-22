import pytest
from ..pytest_utils import wait_for_condition
from src import utils, hardware


@pytest.mark.integration
def test_wind_sensor(log_files: None) -> None:
    config = utils.ConfigInterface.read()
    wind_sensor = hardware.WindSensorInterface(config)

    def data_arrived() -> bool:
        d1, d2 = wind_sensor.get_current_sensor_measurement()

        print(f"measurement: {d1}")
        print(f"device_status: {d2}")
        return d1 is not None

    wait_for_condition(
        data_arrived,
        timeout_message="wind sensor did not send data",
        timeout_seconds=30,
    )

    print("tearing down interface")
    wind_sensor.teardown()
