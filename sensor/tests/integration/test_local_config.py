import json
import os
import sys
import pytest

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(PROJECT_DIR, "config", "config.json")
sys.path.append(PROJECT_DIR)
from src.custom_types import Config


MAX_PUMP_RPS = 70


@pytest.mark.integration
def test_local_config() -> None:
    """checks whether the local config/config.json makes sense:

    * are all required litres per minute within the pumps capable range?
    * is no valve occupied by two things (air inlets, calibration gases)?
    """

    with open(CONFIG_PATH, "r") as f:
        config = Config(**json.load(f))

    # check allowed pump speed
    max_litres_per_minute = MAX_PUMP_RPS * config.hardware.pumped_litres_per_round * 60
    assert config.measurement.pumped_litres_per_minute <= max_litres_per_minute, (
        "config.measurement.pumped_litres_per_minute is above the maximum "
        + f"of {max_litres_per_minute} litres per minute"
    )
    assert (
        config.calibration.flushing.pumped_litres_per_minute <= max_litres_per_minute
    ), (
        "config.calibration.flushing.pumped_litres_per_minut is above the maximum "
        + f"of {max_litres_per_minute} litres per minute"
    )
    assert (
        config.calibration.sampling.pumped_litres_per_minute <= max_litres_per_minute
    ), (
        "config.calibration.sampling.pumped_litres_per_minut is above the maximum "
        + f"of {max_litres_per_minute} litres per minute"
    )
    assert (
        config.calibration.cleaning.pumped_litres_per_minute <= max_litres_per_minute
    ), (
        "config.calibration.cleaning.pumped_litres_per_minut is above the maximum "
        + f"of {max_litres_per_minute} litres per minute"
    )

    # check valve numbers
    valve_numbers = [ai.valve_number for ai in config.measurement.air_inlets] + [
        ai.valve_number for ai in config.calibration.gases
    ]
    unique_valve_numbers = list(set(valve_numbers))
    assert len(valve_numbers) == len(
        unique_valve_numbers
    ), "multiple things use the same valve number"

    # check whether valve 1 is connected to an air inlet
    assert 1 in [
        ai.valve_number for ai in config.measurement.air_inlets
    ], "valve 1 has to be connected to an air inlet"

    # check air inlet directions
    air_inlet_directions = [ai.direction for ai in config.measurement.air_inlets]
    unique_air_inlet_directions = list(set(air_inlet_directions))
    assert len(air_inlet_directions) == len(
        unique_air_inlet_directions
    ), "multiple air inlets use the same direction"

    # check calibration gas concentrations
    calibration_gas_concentrations = [
        cg.concentration for cg in config.calibration.gases
    ]
    unique_calibration_gas_concentrations = list(set(calibration_gas_concentrations))
    assert len(calibration_gas_concentrations) == len(
        unique_calibration_gas_concentrations
    ), "multiple calibration gases use the same concentration"
