import os
import sys
import pytest

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import interfaces

# TODO: use log_file fixture


@pytest.mark.integration
def test_mainboard_sensor() -> None:
    sensor = interfaces.MainboardSensorInterface()
    sensor.get_system_data()
