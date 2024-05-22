from os.path import dirname, abspath
import sys
import time
from typing import Literal
import pytest

PROJECT_DIR = dirname(dirname(abspath(__file__)))
sys.path.append(PROJECT_DIR)
from src import utils, hardware


@pytest.mark.integration
def test_valves() -> None:
    config = utils.ConfigInterface.read()
    valves = hardware.ValveInterface(config)

    for valve_no in [1, 2, 3, 4]:
        valves.set_active_input(valve_no)
        time.sleep(2)

    valves.teardown()
