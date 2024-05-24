from copy import deepcopy
import json
import sys
from typing import Any
import pydantic
import pytest
import os

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
CONFIG_TEMPLATE_PATH = os.path.join(PROJECT_DIR, "config", "config.template.json")
sys.path.append(PROJECT_DIR)
from src.custom_types import Config

with open(CONFIG_TEMPLATE_PATH, "r") as f:
    VALID_CONFIG = json.load(f)


# adapted from https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
def merge_dicts(original: Any, updates: Any) -> Any:
    for key, value in updates.items():
        if (
            (key in original)
            and isinstance(original[key], dict)
            and isinstance(value, dict)
        ):
            original[key] = merge_dicts(original[key], value)
        else:
            original[key] = value
    return original


class ValidationPassedException(Exception):
    """raise when validation does not catch some validation error"""


@pytest.mark.github_action
def test_config_validation() -> None:
    # some valid configs
    Config(**VALID_CONFIG)

    for modification in [
        {"general": 30},  # parameter does not exist
        {
            "measurement": {
                "air_inlets": [
                    {"number": 1, "direction": 300},  # missing key "pipe_length"
                ]
            }
        },
        {
            "measurement": {
                "air_inlets": [
                    {
                        "number": "1",
                        "direction": 300,
                        "tube_length": 50,
                    },  # invalid type of "number"
                ]
            }
        },
    ]:
        try:
            invalid_config = merge_dicts(deepcopy(VALID_CONFIG), modification)
            Config(**invalid_config)
            print(f"invalid_config:")
            print(json.dumps(invalid_config, indent=4))
            raise ValidationPassedException(
                f"config validation passed for invalid config"
            )
        except pydantic.ValidationError:
            pass
