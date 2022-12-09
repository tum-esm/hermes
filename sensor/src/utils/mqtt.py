import os
import time
import paho.mqtt.client
import ssl
from src import custom_types


def get_mqtt_config() -> custom_types.MQTTConfig:
    return custom_types.MQTTConfig(
        station_identifier=os.environ.get("INSERT_NAME_HERE_STATION_IDENTIFIER"),
        mqtt_url=os.environ.get("INSERT_NAME_HERE_MQTT_URL"),
        mqtt_port=os.environ.get("INSERT_NAME_HERE_MQTT_PORT"),
        mqtt_username=os.environ.get("INSERT_NAME_HERE_MQTT_USERNAME"),
        mqtt_password=os.environ.get("INSERT_NAME_HERE_MQTT_PASSWORD"),
        mqtt_base_topic=os.environ.get("INSERT_NAME_HERE_MQTT_BASE_TOPIC"),
    )


def get_mqtt_client(
    timeout_seconds: float = 5,
) -> tuple[paho.mqtt.client.Client, custom_types.MQTTConfig]:
    mqtt_config = get_mqtt_config()

    mqtt_client = paho.mqtt.client.Client(client_id=mqtt_config.station_identifier)
    mqtt_client.username_pw_set(mqtt_config.mqtt_username, mqtt_config.mqtt_password)
    mqtt_client.tls_set(
        certfile=None,
        keyfile=None,
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLS_CLIENT,
    )
    mqtt_client.connect(
        mqtt_config.mqtt_url, port=int(mqtt_config.mqtt_port), keepalive=60
    )
    mqtt_client.loop_start()

    start_time = time.time()
    while True:
        if mqtt_client.is_connected():
            break
        if (time.time() - start_time) > timeout_seconds:
            raise TimeoutError(
                f"mqtt client is not connected (using params {mqtt_config})"
            )
        time.sleep(0.1)

    return mqtt_client, mqtt_config
