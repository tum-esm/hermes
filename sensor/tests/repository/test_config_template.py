import json
import os
import sys
import pytest

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
DEFAULT_CONFIG_PATH = os.path.join(PROJECT_DIR, "config", "config.template.json")
sys.path.append(PROJECT_DIR)
from src.custom_types import Config


@pytest.mark.ci
def test_default_config() -> None:
    with open(DEFAULT_CONFIG_PATH, "r") as f:
        default_config = json.load(f)
    Config(**default_config)
