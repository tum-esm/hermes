import json
import os
import sys
import pytest

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(PROJECT_DIR, "config", "config.json")
sys.path.append(PROJECT_DIR)
from src.custom_types import Config


@pytest.mark.integration
def test_config() -> None:
    """checks whether the used config.json makes sense:

    * are all required litres per minute within the pumps capable range?
    * is no valve occupied by two things (air inlets, calibration gases)?
    """

    with open(CONFIG_PATH, "r") as f:
        config = Config(**json.load(f))

    # check allowed pump speed
    max_litres_per_minute = 70 * config.hardware.pumped_litres_per_round * 60
    assert (
        config.measurement.pump_speed.litres_per_minute_on_measurements
        <= max_litres_per_minute
    )
    assert (
        config.measurement.pump_speed.litres_per_minute_on_valve_switching
        <= max_litres_per_minute
    )
    assert config.calibration.litres_per_minute <= max_litres_per_minute

    # check valve numbers
    valve_numbers = [ai.valve_number for ai in config.measurement.air_inlets] + [
        ai.valve_number for ai in config.calibration.gases
    ]
    unique_valve_numbers = list(set(valve_numbers))
    assert len(valve_numbers) == len(
        unique_valve_numbers
    ), "multiple things use the same valve number"
