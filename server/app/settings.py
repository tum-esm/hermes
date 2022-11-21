import os

import app.utils as utils


# Environment: test, development, production
ENVIRONMENT = os.environ["ENVIRONMENT"]
# Git commit hash
COMMIT_SHA = os.environ["COMMIT_SHA"]
# Git branch name
BRANCH_NAME = os.environ["BRANCH_NAME"]
# Timestamp of server startup
START_TIME = utils.timestamp()

# PostgreSQL connection details
POSTGRESQL_URL = os.environ["POSTGRESQL_URL"]
POSTGRESQL_IDENTIFIER = os.environ["POSTGRESQL_IDENTIFIER"]
POSTGRESQL_PASSWORD = os.environ["POSTGRESQL_PASSWORD"]

# MQTT connection details
MQTT_URL = os.environ["MQTT_URL"]
MQTT_IDENTIFIER = os.environ["MQTT_IDENTIFIER"]
MQTT_PASSWORD = os.environ["MQTT_PASSWORD"]
