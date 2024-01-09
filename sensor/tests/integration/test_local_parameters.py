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

    # check valve numbers
    valve_numbers = [ai.valve_number for ai in config.measurement.air_inlets] + [
        ai.valve_number for ai in config.calibration.gases
    ]
    unique_valve_numbers = list(set(valve_numbers))
    assert len(valve_numbers) == len(
        unique_valve_numbers
    ), "multiple things use the same valve number"

    # check air inlet directions
    air_inlet_directions = [ai.direction for ai in config.measurement.air_inlets]
    unique_air_inlet_directions = list(set(air_inlet_directions))
    assert len(air_inlet_directions) == len(
        unique_air_inlet_directions
    ), "multiple air inlets use the same direction"

    # check calibration gas concentrations
    calibration_gas_bottle_ids = [cg.bottle_id for cg in config.calibration.gases]
    unique_calibration_gas_concentrations = list(set(calibration_gas_bottle_ids))
    assert len(calibration_gas_bottle_ids) == len(
        unique_calibration_gas_concentrations
    ), "multiple calibration gases use the same bottle ids"


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


@pytest.mark.version_update
@pytest.mark.integration
def test_local_libraries() -> None:
    """checks whether the raspberry pi specific libraries can be loaded"""

    import board
    import RPi.GPIO
