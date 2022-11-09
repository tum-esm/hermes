import os
import sys
import time
import pytest


dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import interfaces


@pytest.mark.integration
def test_input_air_sensor() -> None:
    config = interfaces.ConfigInterface.read()
    sensor = interfaces.InputAirSensorInterface(config)
    valves = interfaces.ValveInterface(config)
    pump = interfaces.PumpInterface(config)

    valves.set_active_input(1, logger=False)
    pump.set_desired_pump_rps(20)
    time.sleep(5)
    sensor.run(logger=False)
    pump.teardown()
