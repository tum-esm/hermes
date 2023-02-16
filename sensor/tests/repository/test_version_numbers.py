import json
import os
import re
import pytest

dir = os.path.dirname
ROOT_DIR = dir(dir(dir(dir(os.path.abspath(__file__)))))
SENSOR_PYPROJECT_TOML = os.path.join(ROOT_DIR, "sensor", "pyproject.toml")
SENSOR_DEFAULT_CONFIG = os.path.join(
    ROOT_DIR, "sensor", "config", "config.template.json"
)


@pytest.mark.ci
def test_version_numbers() -> None:
    assert os.path.isfile(SENSOR_PYPROJECT_TOML)
    assert os.path.isfile(SENSOR_DEFAULT_CONFIG)

    # fetch version number from "pyproject.toml"
    with open(SENSOR_PYPROJECT_TOML, "r") as f:
        sensor_version_line = f.read().split("\n")[2]
    toml_pattern = re.compile(r'^version = "\d+\.\d+\.\d+(\-(alpha|beta)\.\d+)?"$')
    assert toml_pattern.match(sensor_version_line) is not None
    sensor_version = sensor_version_line.split('"')[1]

    # fetch version number from "config.template.json"
    with open(SENSOR_DEFAULT_CONFIG, "r") as f:
        sensor_config_template_version = json.load(f)["version"]
    
    assert sensor_version == sensor_config_template_version
