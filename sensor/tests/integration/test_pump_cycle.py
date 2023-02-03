from os.path import dirname, abspath
import sys
import time
import pytest

PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(PROJECT_DIR)
from src import utils, hardware


@pytest.mark.integration
def test_pump_cycle(log_files: None) -> None:
    config = utils.ConfigInterface.read()
    pump = hardware.PumpInterface(config)

    for rps in [20, 40, 60, 0]:
        print(f"setting rps to {rps}")
        pump.set_desired_pump_speed(unit="rps", value=rps)
        time.sleep(3)

    pump.check_errors()
    pump.teardown()
