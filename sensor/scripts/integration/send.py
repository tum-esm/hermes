import json
import os
from os.path import dirname, abspath, join
import sys
import time
import dotenv

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
MQTT_ENV_VARS_PATH = join(PROJECT_DIR, "config", ".env.testing")
sys.path.append(PROJECT_DIR)

from src import utils

dotenv.load_dotenv(MQTT_ENV_VARS_PATH)

test_station_identifier = f"test-station-identifier-{round(time.time())}"
test_base_topic = f"/development/{round(time.time())*2}"
os.environ["INSERT_NAME_HERE_STATION_IDENTIFIER"] = test_station_identifier
os.environ["INSERT_NAME_HERE_MQTT_BASE_TOPIC"] = test_base_topic

mqtt_client, mqtt_config = utils.mqtt.get_mqtt_client()


i = 0
while True:
    mqtt_client.publish(
        mqtt_config.mqtt_base_topic + "/incrementor-test",
        json.dumps({"type": "text", "body": f"iteration {i}"}),
        qos=1,
    )
    print(f"published message {i}")
    time.sleep(2)
    i += 1
