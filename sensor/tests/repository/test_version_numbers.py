import json
import os
import re

dir = os.path.dirname
ROOT_DIR = dir(dir(dir(dir(os.path.abspath(__file__)))))
SERVER_PYPROJECT_TOML = os.path.join(ROOT_DIR, "server", "pyproject.toml")
SENSOR_PYPROJECT_TOML = os.path.join(ROOT_DIR, "sensor", "pyproject.toml")
SENSOR_DEFAULT_CONFIG = os.path.join(
    ROOT_DIR, "sensor", "config", "config.default.json"
)

# TODO: test version number of dashboard


def test_version_numbers():
    assert os.path.isfile(SERVER_PYPROJECT_TOML)
    assert os.path.isfile(SENSOR_PYPROJECT_TOML)
    assert os.path.isfile(SENSOR_DEFAULT_CONFIG)

    with open(SERVER_PYPROJECT_TOML, "r") as f:
        version_1_line = f.read().split("\n")[2]
    with open(SENSOR_PYPROJECT_TOML, "r") as f:
        version_2_line = f.read().split("\n")[2]

    toml_pattern = re.compile(r'^version = "\d+\.\d+\.\d+"$')
    assert toml_pattern.match(version_1_line) is not None
    assert toml_pattern.match(version_2_line) is not None

    version_1 = version_1_line.split('"')[1]
    version_2 = version_2_line.split('"')[1]

    with open(SENSOR_DEFAULT_CONFIG, "r") as f:
        version_3 = json.load(f)["version"]

    assert version_1 == version_2 == version_3
