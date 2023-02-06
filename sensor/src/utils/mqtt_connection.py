import os
import time
import paho.mqtt.client
import ssl
from src import custom_types


class MQTTConnection:
    """provides the mqtt config and client"""

    def __init__(self) -> None:
        self.config = custom_types.MQTTConfig(
            station_identifier=os.environ.get("HERMES_MQTT_IDENTIFIER"),
            mqtt_url=os.environ.get("HERMES_MQTT_URL"),
            mqtt_port=os.environ.get("HERMES_MQTT_PORT"),
            mqtt_username=os.environ.get("HERMES_MQTT_USERNAME"),
            mqtt_password=os.environ.get("HERMES_MQTT_PASSWORD"),
            mqtt_base_topic=os.environ.get("HERMES_MQTT_BASE_TOPIC"),
        )

        self.client = paho.mqtt.client.Client(client_id=self.config.station_identifier)
        self.client.username_pw_set(
            self.config.mqtt_username, self.config.mqtt_password
        )
        self.client.tls_set(
            certfile=None,
            keyfile=None,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLS_CLIENT,
        )
        self.client.connect(
            self.config.mqtt_url,
            port=int(self.config.mqtt_port),
            keepalive=60,
        )
        self.client.loop_start()

        start_time = time.time()
        while True:
            if self.client.is_connected():
                break
            if (time.time() - start_time) > 5:
                raise TimeoutError(
                    f"mqtt client is not connected (using params {self.config})"
                )
            time.sleep(0.1)

    def teardown(self) -> None:
        """disconnected the mqtt client"""
        self.client.loop_stop(force=True)
        self.client.disconnect()

    @staticmethod
    def validate_config() -> None:
        """checks whether the current environment contains all
        variables required for running an MQTT client"""

        custom_types.MQTTConfig(
            station_identifier=os.environ.get("HERMES_MQTT_IDENTIFIER"),
            mqtt_url=os.environ.get("HERMES_MQTT_URL"),
            mqtt_port=os.environ.get("HERMES_MQTT_PORT"),
            mqtt_username=os.environ.get("HERMES_MQTT_USERNAME"),
            mqtt_password=os.environ.get("HERMES_MQTT_PASSWORD"),
            mqtt_base_topic=os.environ.get("HERMES_MQTT_BASE_TOPIC"),
        )
