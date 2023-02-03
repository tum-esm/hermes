from os.path import dirname, abspath
import sys
import pytest

PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(PROJECT_DIR)
from src import utils, hardware


@pytest.mark.integration
def test_air_inlet_sensor(log_files: None) -> None:
    config = utils.ConfigInterface.read()
    sensor = hardware.AirInletSensorInterface(config)
    temperature, humidity = sensor.get_current_values()
    assert temperature is not None
    assert humidity is not None
    sensor.teardown()
