from os.path import dirname, abspath
import sys
import pytest

PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(PROJECT_DIR)
from src import utils, hardware


@pytest.mark.integration
def test_sht45_sensor(log_files: None) -> None:
    config = utils.ConfigInterface.read()
    sensor = hardware.SHT45SensorInterface(config)
    data = sensor.get_data()
    assert data.temperature is not None
    assert data.humidity is not None
