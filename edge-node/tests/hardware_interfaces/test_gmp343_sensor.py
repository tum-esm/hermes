from os.path import dirname, abspath
import sys
import pytest

PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(PROJECT_DIR)
from src import utils, hardware


@pytest.mark.hardware_interface
def test_gmp343_sensor() -> None:
    config = utils.ConfigInterface.read()
    sensor = hardware.CO2SensorInterface(config)

    # test high level functions
    sensor.set_compensation_values(pressure=950.0, humidity=20.0)
    sensor.set_filter_setting()
    sensor.get_current_concentration()
    sensor.get_param_info()
    sensor.get_device_info()
    sensor.get_correction_info()
    sensor.check_errors()
    sensor.teardown()
