import json
import os
import sys
import time
import dotenv

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
dotenv.load_dotenv(os.path.join(PROJECT_DIR, "config", ".env"))

sys.path.append(PROJECT_DIR)
from src import custom_types, utils


if __name__ == "__main__":
    config = utils.ConfigInterface.read()
    mqtt_connection = utils.MQTTConnection()

    mqtt_config = mqtt_connection.config
    mqtt_client = mqtt_connection.client

    config_topic = (
        f"{mqtt_config.mqtt_base_topic}configurations/{mqtt_config.station_identifier}"
    )
    print(f"config_topic = {config_topic}")

    sent_config_message = custom_types.MQTTConfigurationRequest(
        revision=1, configuration={"version": "0.1.0", "other_params": 30}
    )
    message_info = mqtt_client.publish(
        topic=config_topic,
        payload=json.dumps(sent_config_message.dict()),
        qos=1,
        retain=True,
    )
    while True:
        if message_info.is_published():
            print("published")
            break
        time.sleep(1)
        print("pending")
