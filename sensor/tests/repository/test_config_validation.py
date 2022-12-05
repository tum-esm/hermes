from copy import deepcopy
import json
import sys
from typing import Any
import pydantic
import pytest
import os

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
sys.path.append(PROJECT_DIR)
from src.custom_types import Config


VALID_CONFIG = {
    "version": "0.1.0",
    "general": {
        "station_name": "a-unique-node-id",
    },
    "mqtt": {
        "url": "...",
        "port": 8883,
        "identifier": "...",
        "password": "........",
        "base_topic": "/abc/def",
    },
    "valves": {
        "air_inlets": [
            {"number": 1, "direction": 300},
            {"number": 2, "direction": 50},
        ]
    },
}


# adapted from https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
def merge_dicts(original: Any, updates: Any):
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


@pytest.mark.ci
def test_config_validation():
    # some valid configs
    Config(**VALID_CONFIG)

    # testing the merge_dicts function
    Config(
        **merge_dicts(deepcopy(VALID_CONFIG), {"general": {"station_name": "fghj-a"}})
    )

    for modification in [
        {"version": "0.2.0"},
        {"general": {"station_name", 30}},
        {"mqtt": {"url": 30}},
        {"mqtt": {"port": "30"}},
        {"mqtt": {"identifier": 30}},
        {"mqtt": {"password": 30}},
        {"mqtt": {"base_topic": 30}},
        {"mqtt": {"base_topic": "/fghj/fghj/"}},
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
