from os.path import dirname, abspath
import sys
import pytest
from ..pytest_fixtures import log_files

PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(PROJECT_DIR)
from src import hardware_interfaces


@pytest.mark.integration
def test_mainboard_sensor(log_files: None) -> None:
    sensor = hardware_interfaces.MainboardSensorInterface()
    sensor.get_system_data()
