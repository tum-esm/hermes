import os


# check that required environment variables are set
_VARS = [
    "MQTT_URL",
    "MQTT_IDENTIFIER",
    "MQTT_PASSWORD",
]
for var in _VARS:
    assert os.getenv(var), f"environment variable {var} not set"

# MQTT broker URL
MQTT_URL = os.getenv("MQTT_URL")
# MQTT identifier of this server
MQTT_IDENTIFIER = os.getenv("MQTT_IDENTIFIER")
# MQTT password of this server
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
