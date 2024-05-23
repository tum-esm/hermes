import pytest
from src import utils, hardware


@pytest.mark.hardware_interface
def test_wind_sensor() -> None:
    """This tests if the current configuration with or without a
    wind sensor present will cause any problems."""
    config = utils.ConfigInterface.read()
    wind_sensor = hardware.WindSensorInterface(config)

    wind_sensor.get_current_sensor_measurement()
    wind_sensor.check_errors()
    wind_sensor.teardown()
