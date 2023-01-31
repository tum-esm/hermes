from os.path import dirname, abspath
import sys
import pytest
from ..pytest_fixtures import log_files

PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(PROJECT_DIR)
from src import utils, hardware


@pytest.mark.integration
def test_co2_sensor(log_files: None) -> None:
    config = utils.ConfigInterface.read()
    sensor = hardware.CO2SensorInterface(config)

    sensor.get_correction_info()
    sensor.get_current_concentration()
    sensor.get_device_info()

    sensor.check_errors()
    sensor.teardown()
