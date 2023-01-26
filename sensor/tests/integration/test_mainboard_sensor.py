from os.path import dirname, abspath
import sys
import pytest
from ..pytest_fixtures import (
    mqtt_client_environment,
    mqtt_archiving_loop,
    mqtt_data_files,
    log_files,
)

PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(PROJECT_DIR)
from src import hardware, utils


@pytest.mark.integration
def test_mainboard_sensor(
    mqtt_archiving_loop: None, mqtt_data_files: None, log_files: None
) -> None:
    config = utils.ConfigInterface.read()
    sensor = hardware.MainboardSensorInterface(config)
    sensor.get_system_data()
    sensor.teardown()
