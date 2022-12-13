import os
import sys
import time
import pytest

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import interfaces


# TODO: use log_file fixture


@pytest.mark.integration
def test_pump_cycle() -> None:
    config = interfaces.ConfigInterface.read()
    pump = interfaces.PumpInterface(config)

    for rps in range(10, 71, 10):
        print(f"setting rps to {rps}")
        pump.set_desired_pump_rps(rps)
        time.sleep(8)

    pump.set_desired_pump_rps(0)
    pump.check_errors()
    pump.teardown()


"""
setting rps to 10
desired rps = 10, average rps = 9.85
setting rps to 20
desired rps = 20, average rps = 20.194444444444446
setting rps to 30
desired rps = 30, average rps = 30.388888888888893
setting rps to 40
desired rps = 40, average rps = 40.87777777777778
setting rps to 50
desired rps = 50, average rps = 51.21666666666666
setting rps to 60
desired rps = 60, average rps = 61.677777777777784
setting rps to 70
desired rps = 70, average rps = 69.84444444444445
"""
