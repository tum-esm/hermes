import os
import sys
import pytest
from ..pytest_fixtures import log_files

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import interfaces


@pytest.mark.integration
def test_mainboard_sensor(log_files) -> None:
    sensor = interfaces.MainboardSensorInterface()
    sensor.get_system_data()
