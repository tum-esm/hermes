import json
import os
import sys
import pytest

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
CONFIG_TEMPLATE_PATH = os.path.join(PROJECT_DIR, "config", "config.template.json")
sys.path.append(PROJECT_DIR)
from src.custom_types import Config


@pytest.mark.github_action
def test_config_template() -> None:
    with open(CONFIG_TEMPLATE_PATH, "r") as f:
        default_config = json.load(f)
    Config(**default_config)
