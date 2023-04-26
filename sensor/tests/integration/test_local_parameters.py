import json
import os
import pytest
import os
from os.path import dirname
import pytest
import dotenv
from src import custom_types

PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(PROJECT_DIR, "config", "config.json")


MAX_PUMP_RPS = 70


@pytest.mark.parameter_update
@pytest.mark.version_update
@pytest.mark.integration
def test_local_config() -> None:
    """checks whether the local config/config.json makes sense:

    * are all required litres per minute within the pumps capable range?
    * is no valve occupied by two things (air inlets, calibration gases)?
    """

    with open(CONFIG_PATH, "r") as f:
        config = custom_types.Config(**json.load(f))

    # check allowed pump speed
    max_litres_per_minute = MAX_PUMP_RPS * config.hardware.pumped_litres_per_round * 60
    assert config.measurement.pumped_litres_per_minute <= max_litres_per_minute, (
        "config.measurement.pumped_litres_per_minute is above the maximum "
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


@pytest.mark.version_update
@pytest.mark.integration
def test_local_env_vars() -> None:
    """checks whether the local config/.env can be loaded"""

    env_file_path = os.path.join(PROJECT_DIR, "config", ".env")
    assert os.path.isfile(env_file_path), f"{env_file_path} is not a file"

    dotenv.load_dotenv(env_file_path)
    custom_types.MQTTConfig(
        station_identifier=os.environ.get("HERMES_MQTT_IDENTIFIER"),
        mqtt_url=os.environ.get("HERMES_MQTT_URL"),
        mqtt_port=os.environ.get("HERMES_MQTT_PORT"),
        mqtt_username=os.environ.get("HERMES_MQTT_USERNAME"),
        mqtt_password=os.environ.get("HERMES_MQTT_PASSWORD"),
        mqtt_base_topic=os.environ.get("HERMES_MQTT_BASE_TOPIC"),
    )
