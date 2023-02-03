from os.path import dirname, abspath
import sys
import pytest

PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(PROJECT_DIR)
from src import hardware, utils


@pytest.mark.integration
def test_mainboard_sensor(log_files: None) -> None:
    config = utils.ConfigInterface.read()
    sensor = hardware.MainboardSensorInterface(config)
    sensor.get_system_data()
    sensor.teardown()
