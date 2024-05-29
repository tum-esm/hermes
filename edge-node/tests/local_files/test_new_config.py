import json
import os
import pytest
from os.path import dirname
from src import custom_types

PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(PROJECT_DIR, "config", "config.json")


@pytest.mark.remote_update
@pytest.mark.version_update
def test_new_config() -> None:
    """checks whether the local config/config.json makes sense:"""

    # verify that config matches template types
    with open(CONFIG_PATH, "r") as f:
        config = custom_types.Config(**json.load(f))

    # check if valves assignments are unique
    valve_numbers = [config.measurement.valve_number] + [
        ai.valve_number for ai in config.calibration.gas_cylinders
    ]
    unique_valve_numbers = list(set(valve_numbers))
    assert len(valve_numbers) == len(
        unique_valve_numbers
    ), "multiple things use the same valve number"

    # check that different calibration cylinders are present
    calibration_gas_bottle_ids = [
        cg.bottle_id for cg in config.calibration.gas_cylinders
    ]
    unique_calibration_gas_concentrations = list(set(calibration_gas_bottle_ids))
    assert len(calibration_gas_bottle_ids) == len(
        unique_calibration_gas_concentrations
    ), "multiple calibration cylinders use the same bottle id"
