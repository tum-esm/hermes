import os
import paho.mqtt.client
import ssl
from src import custom_types


def get_mqtt_client() -> tuple[paho.mqtt.client.Client, custom_types.MQTTConfig]:
    mqtt_config = custom_types.MQTTConfig(
        station_identifier=os.environ.get("INSERT_NAME_HERE_STATION_IDENTIFIER"),
        mqtt_url=os.environ.get("INSERT_NAME_HERE_MQTT_URL"),
        mqtt_port=os.environ.get("INSERT_NAME_HERE_MQTT_PORT"),
        mqtt_username=os.environ.get("INSERT_NAME_HERE_MQTT_USERNAME"),
        mqtt_password=os.environ.get("INSERT_NAME_HERE_MQTT_PASSWORD"),
        mqtt_base_topic=os.environ.get("INSERT_NAME_HERE_MQTT_BASE_TOPIC"),
    )

    mqtt_client = paho.mqtt.client.Client(client_id=mqtt_config.station_identifier)
    mqtt_client.username_pw_set(mqtt_config.mqtt_username, mqtt_config.mqtt_password)
    mqtt_client.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED)
    mqtt_client.connect(
        mqtt_config.mqtt_url, port=int(mqtt_config.mqtt_port), keepalive=60
    )

    return mqtt_client, mqtt_config
