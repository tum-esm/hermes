import os
import sys
import time
from typing import Literal
import pytest

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)

from src import interfaces

# TODO: use log_file fixture


@pytest.mark.integration
def test_valve_cycle() -> None:
    config = interfaces.ConfigInterface.read()
    valves = interfaces.ValveInterface(config)

    valve_nos: list[Literal[1, 2, 3, 4]] = [1, 2, 3, 4]

    for valve_no in valve_nos:
        valves.set_active_input(valve_no)
        time.sleep(3)

    valves.teardown()
