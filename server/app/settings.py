import os


# check that required environment variables are set
_VARS = [
    "COMMIT_SHA",
    "BRANCH_NAME",
    "MQTT_URL",
    "MQTT_IDENTIFIER",
    "MQTT_PASSWORD",
]
for var in _VARS:
    assert os.getenv(var), f"environment variable {var} not set"

# git commit hash
COMMIT_SHA = os.getenv("COMMIT_SHA")
# git branch name
BRANCH_NAME = os.getenv("BRANCH_NAME")
# timestamp of when the server was started
# START_TIME = utils.timestamp()
# MQTT broker URL
MQTT_URL = os.getenv("MQTT_URL")
# MQTT identifier of this server
MQTT_IDENTIFIER = os.getenv("MQTT_IDENTIFIER")
# MQTT password of this server
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
