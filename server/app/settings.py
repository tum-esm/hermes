import os

import app.utils as utils


# Environment: test, development, production
ENVIRONMENT = os.environ["HERMES_ENVIRONMENT"]
# Git commit hash
COMMIT_SHA = os.environ["HERMES_COMMIT_SHA"]
# Git branch name
BRANCH_NAME = os.environ["HERMES_BRANCH_NAME"]
# Timestamp of server startup
START_TIMESTAMP = utils.timestamp()

# PostgreSQL connection details
POSTGRESQL_URL = os.environ["HERMES_POSTGRESQL_URL"]
POSTGRESQL_PORT = int(os.environ["HERMES_POSTGRESQL_PORT"])
POSTGRESQL_IDENTIFIER = os.environ["HERMES_POSTGRESQL_IDENTIFIER"]
POSTGRESQL_PASSWORD = os.environ["HERMES_POSTGRESQL_PASSWORD"]
POSTGRESQL_DATABASE = os.environ["HERMES_POSTGRESQL_DATABASE"]

# MQTT connection details
MQTT_URL = os.environ["HERMES_MQTT_URL"]
MQTT_PORT = int(os.environ["HERMES_MQTT_PORT"])
MQTT_IDENTIFIER = os.environ["HERMES_MQTT_IDENTIFIER"]
MQTT_USERNAME = os.environ["HERMES_MQTT_USERNAME"]
MQTT_PASSWORD = os.environ["HERMES_MQTT_PASSWORD"]
