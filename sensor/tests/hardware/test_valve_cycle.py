import os
import sys
import time
import pytest

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import interfaces


@pytest.mark.integration
def test_valve_cycle() -> None:
    config = interfaces.ConfigInterface.read()
    valves = interfaces.ValveInterface(config)
    pump = interfaces.PumpInterface(config)
    pump.set_desired_pump_rps(30)

    for i in range(5):
        for valve_no in range(1, 5):
            valves.set_active_input(valve_no, logger=False)
            time.sleep(3)

    pump.set_desired_pump_rps(0)
    pump.teardown()
