import os
import sys
import time
import pytest
from ..pytest_fixtures import log_files

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import interfaces


@pytest.mark.integration
def test_pump_cycle(log_files) -> None:
    config = interfaces.ConfigInterface.read()
    pump = interfaces.PumpInterface(config)

    for rps in range(10, 71, 10):
        print(f"setting rps to {rps}")
        pump.set_desired_pump_rps(rps)
        time.sleep(8)

    pump.set_desired_pump_rps(0)
    pump.check_errors()
    pump.teardown()
