from os.path import dirname, abspath
import sys
import time
import pytest
from ..pytest_fixtures import log_files

PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(PROJECT_DIR)
from src import utils, hardware_interfaces


@pytest.mark.integration
def test_input_air_sensor(log_files: None) -> None:
    config = utils.ConfigInterface.read()
    sensor = hardware_interfaces.AirInletSensorInterface()
    valves = hardware_interfaces.ValveInterface(config)
    pump = hardware_interfaces.PumpInterface(config)

    valves.set_active_input(1)
    pump.set_desired_pump_rps(20)
    time.sleep(5)
    sensor.get_current_values()
    pump.teardown()
