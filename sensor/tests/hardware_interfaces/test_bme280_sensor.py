from os.path import dirname, abspath
import sys
import pytest

PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(PROJECT_DIR)
from src import hardware, utils


@pytest.mark.hardware_interface
def test_bme280_sensor() -> None:
    """Two BME280 sensors are present in the system.
    BME280 sensor measure temperature, humidity and pressure.

    The test verifies that both BME280 sensors can be read."""

    config = utils.ConfigInterface.read()
    s1 = hardware.BME280SensorInterface(config, variant="ioboard")
    data1 = s1.get_data()
    assert data1.temperature is not None
    assert data1.humidity is not None
    assert data1.pressure is not None
    s1.teardown()

    s2 = hardware.BME280SensorInterface(config, variant="air-inlet")
    data2 = s2.get_data()
    assert data2.temperature is not None
    assert data2.humidity is not None
    assert data2.pressure is not None
    s2.teardown()
