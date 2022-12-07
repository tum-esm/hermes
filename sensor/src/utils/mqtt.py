import os
import paho.mqtt.client
import ssl
from src import custom_types


def get_mqtt_client() -> tuple[paho.mqtt.client.Client, custom_types.MQTTConfig]:
    mqtt_config = custom_types.MQTTConfig(
        url=os.environ.get("INSERT_NAME_HERE_MQTT_URL"),
        port=os.environ.get("INSERT_NAME_HERE_MQTT_PORT"),
        identifier=os.environ.get("INSERT_NAME_HERE_STATION_IDENTIFIER"),
        password=os.environ.get("INSERT_NAME_HERE_MQTT_PASSWORD"),
        base_topic=os.environ.get("INSERT_NAME_HERE_MQTT_BASE_TOPIC"),
    )

    mqtt_client = paho.mqtt.client.Client(client_id=mqtt_config.identifier)
    mqtt_client.username_pw_set(mqtt_config.identifier, mqtt_config.password)
    mqtt_client.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED)
    mqtt_client.connect(mqtt_config.url, port=mqtt_config.port, keepalive=60)

    return mqtt_client, mqtt_config
