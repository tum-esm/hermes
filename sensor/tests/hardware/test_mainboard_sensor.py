import os
import sys
import pytest

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import interfaces


@pytest.mark.integration
def test_mainboard_sensor() -> None:
    config = interfaces.ConfigInterface.read()
    sensor = interfaces.MainboardSensorInterface(config)

    sensor.log_system_data(logger=False)
