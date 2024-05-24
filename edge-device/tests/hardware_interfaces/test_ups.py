from os.path import dirname, abspath
import sys
import pytest

PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(PROJECT_DIR)
from src import utils, hardware


@pytest.mark.hardware_interface
def test_ups() -> None:
    config = utils.ConfigInterface.read()
    ups = hardware.UPSInterface(config)
    ups.update_ups_status()

    assert ups.powered_by_grid is not None
    assert ups.battery_is_fully_charged is not None
    assert ups.battery_error_detected is not None
    assert ups.battery_above_voltage_threshold is not None

    ups.teardown()
