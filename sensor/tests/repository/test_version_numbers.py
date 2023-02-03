import json
import os
import re
import pytest

dir = os.path.dirname
ROOT_DIR = dir(dir(dir(dir(os.path.abspath(__file__)))))
SERVER_PYPROJECT_TOML = os.path.join(ROOT_DIR, "server", "pyproject.toml")
SENSOR_PYPROJECT_TOML = os.path.join(ROOT_DIR, "sensor", "pyproject.toml")
SETUP_PYPROJECT_TOML = os.path.join(ROOT_DIR, "raspi-setup", "pyproject.toml")
SENSOR_DEFAULT_CONFIG = os.path.join(
    ROOT_DIR, "sensor", "config", "config.template.json"
)


@pytest.mark.ci
def test_version_numbers() -> None:
    assert os.path.isfile(SERVER_PYPROJECT_TOML)
    assert os.path.isfile(SENSOR_PYPROJECT_TOML)
    assert os.path.isfile(SENSOR_DEFAULT_CONFIG)

    with open(SERVER_PYPROJECT_TOML, "r") as f:
        version_server_line = f.read().split("\n")[2]
    with open(SENSOR_PYPROJECT_TOML, "r") as f:
        version_sensor_line = f.read().split("\n")[2]
    with open(SETUP_PYPROJECT_TOML, "r") as f:
        version_setup_line = f.read().split("\n")[2]

    with open(SENSOR_DEFAULT_CONFIG, "r") as f:
        version_config = json.load(f)["version"]

    toml_pattern = re.compile(r'^version = "\d+\.\d+\.\d+(\-(alpha|beta)\.\d+)?"$')
    assert toml_pattern.match(version_server_line) is not None
    assert toml_pattern.match(version_sensor_line) is not None
    assert toml_pattern.match(version_setup_line) is not None

    version_server = version_server_line.split('"')[1]
    version_sensor = version_sensor_line.split('"')[1]
    version_setup = version_setup_line.split('"')[1]

    # assert version_1 == version_2 == version_3
    assert version_sensor == version_config == version_setup
