from os.path import dirname, abspath
import sys
import time
import pytest
from ..pytest_fixtures import log_files

PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(PROJECT_DIR)
from src import utils, hardware


@pytest.mark.integration
def test_pump_cycle(log_files: None) -> None:
    config = utils.ConfigInterface.read()
    pump = hardware.PumpInterface(config)

    for rps in range(10, 71, 10):
        print(f"setting rps to {rps}")
        pump.set_desired_pump_speed(unit="rps", value=rps)
        time.sleep(8)

    pump.set_desired_pump_speed(unit="rps", value=0)
    pump.check_errors()
    pump.teardown()
