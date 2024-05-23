from os.path import dirname, abspath
import sys
import time
from typing import Literal
import pytest

PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(PROJECT_DIR)
from src import utils, hardware


@pytest.mark.hardware_interface
def test_valves() -> None:
    config = utils.ConfigInterface.read()
    valves = hardware.ValveInterface(config)

    valve_nos: list[Literal[1, 2, 3, 4]] = [1, 2, 3, 4]

    for valve_no in valve_nos:
        valves.set_active_input(valve_no)
        time.sleep(2)

    valves.teardown()
