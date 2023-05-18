from os.path import dirname, abspath
import sys
import pytest

PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(PROJECT_DIR)
from src import hardware, utils


@pytest.mark.integration
def test_bme280_sensor(log_files: None) -> None:
    config = utils.ConfigInterface.read()
    s1 = hardware.BME280SensorInterface(config, variant="mainboard")
    data1 = s1.get_data()
    assert data1.temperature is not None
    s1.teardown()

    s2 = hardware.BME280SensorInterface(config, variant="air-inlet")
    data2 = s2.get_data()
    assert data2.temperature is not None
    s2.teardown()
