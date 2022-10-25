import os

import app.utils as utils

# Check that required environment variables are set
_VARS = [
    "COMMIT_SHA",
    "BRANCH_NAME",
    "POSTGRESQL_URL",
    "POSTGRESQL_IDENTIFIER",
    "POSTGRESQL_PASSWORD",
    "MQTT_URL",
    "MQTT_IDENTIFIER",
    "MQTT_PASSWORD",
]
for var in _VARS:
    assert os.getenv(var), f"environment variable {var} not set"

# Git commit hash
COMMIT_SHA = os.getenv("COMMIT_SHA")
# Git branch name
BRANCH_NAME = os.getenv("BRANCH_NAME")
# Timestamp of server startup
START_TIME = utils.timestamp()

# PostgreSQL connection details
POSTGRESQL_URL = os.getenv("POSTGRESQL_URL")
POSTGRESQL_IDENTIFIER = os.getenv("POSTGRESQL_IDENTIFIER")
POSTGRESQL_PASSWORD = os.getenv("POSTGRESQL_PASSWORD")

# MQTT connection details
MQTT_URL = os.getenv("MQTT_URL")
MQTT_IDENTIFIER = os.getenv("MQTT_IDENTIFIER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
