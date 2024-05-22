from os.path import dirname, abspath
import sys
import time
import pytest

PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(PROJECT_DIR)
from src import utils, hardware


@pytest.mark.integration
def test_pump_cycle() -> None:
    config = utils.ConfigInterface.read()
    pump = hardware.PumpInterface(config)

    for duty_cycle in [0, 0.05, 0.1, 0.15, 0.2, 0]:
        print(f"setting duty cycle to {duty_cycle}")
        pump.set_desired_pump_speed(pwm_duty_cycle=duty_cycle)
        time.sleep(3)

    pump.teardown()
