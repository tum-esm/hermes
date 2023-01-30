import pytest
from ..pytest_fixtures import log_files
from ..pytest_utils import wait_for_condition
from src import utils, hardware


@pytest.mark.integration
def test_wind_sensor(log_files: None) -> None:
    config = utils.ConfigInterface.read()
    wind_sensor = hardware.WindSensorInterface(config)

    def data_arrived() -> bool:
        d1 = wind_sensor.get_current_wind_measurement()
        d2 = wind_sensor.get_current_device_status()
        print(f"measurement: {d1.dict()}")
        print(f"device_status: {d2.dict()}")
        return (d1 is not None) and (d2 is not None)

    wait_for_condition(
        data_arrived,
        timeout_message="wind sensor did not send data",
        timeout_seconds=30,
    )

    print("tearing down interface")
    wind_sensor.teardown()
