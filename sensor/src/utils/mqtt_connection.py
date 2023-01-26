import os
import time
from typing import Optional
import paho.mqtt.client
import ssl
from src import custom_types
from .functions import get_hostname


class MQTTConnection:
    """provides an mqtt client"""

    __config: Optional[custom_types.MQTTConfig] = None
    __client: Optional[paho.mqtt.client.Client] = None

    @staticmethod
    def __init() -> None:
        """v and
        initializes the mqtt client. timeout_seconds is the amount
        of time the mqtt connection process is allowed to take."""
        MQTTConnection.__init_config()
        MQTTConnection.__init_client()

    @staticmethod
    def get_config() -> custom_types.MQTTConfig:
        """returns the mqtt config, runs init() on first call"""
        if MQTTConnection.__config is None or MQTTConnection.__client is None:
            MQTTConnection.__init()
        assert MQTTConnection.__config is not None
        return MQTTConnection.__config

    @staticmethod
    def get_client() -> paho.mqtt.client.Client:
        """returns the mqtt client, runs init() on first call"""
        if MQTTConnection.__config is None or MQTTConnection.__client is None:
            MQTTConnection.__init()
        assert MQTTConnection.__client is not None
        return MQTTConnection.__client

    @staticmethod
    def deinit() -> None:
        """disconnected the mqtt client and removes the internal class state"""
        if MQTTConnection.__client is not None:
            MQTTConnection.__client.disconnect()
            MQTTConnection.__client = None
        MQTTConnection.__config = None

    @staticmethod
    def __init_config() -> None:
        """loads the mqtt config from environment variables"""
        MQTTConnection.__config = custom_types.MQTTConfig(
            station_identifier=get_hostname(),
            mqtt_url=os.environ.get("INSERT_NAME_HERE_MQTT_URL"),
            mqtt_port=os.environ.get("INSERT_NAME_HERE_MQTT_PORT"),
            mqtt_username=os.environ.get("INSERT_NAME_HERE_MQTT_USERNAME"),
            mqtt_password=os.environ.get("INSERT_NAME_HERE_MQTT_PASSWORD"),
            mqtt_base_topic=os.environ.get("INSERT_NAME_HERE_MQTT_BASE_TOPIC"),
        )

    @staticmethod
    def __init_client() -> None:
        """initializes the mqtt client. timeout_seconds is the amount
        of time the mqtt connection process is allowed to take."""
        assert MQTTConnection.__config is not None

        mqtt_client = paho.mqtt.client.Client(
            client_id=MQTTConnection.__config.station_identifier
        )
        mqtt_client.username_pw_set(
            MQTTConnection.__config.mqtt_username, MQTTConnection.__config.mqtt_password
        )
        mqtt_client.tls_set(
            certfile=None,
            keyfile=None,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLS_CLIENT,
        )
        mqtt_client.connect(
            MQTTConnection.__config.mqtt_url,
            port=int(MQTTConnection.__config.mqtt_port),
            keepalive=60,
        )
        mqtt_client.loop_start()

        start_time = time.time()
        while True:
            if mqtt_client.is_connected():
                break
            if (time.time() - start_time) > 5:
                raise TimeoutError(
                    f"mqtt client is not connected (using params {MQTTConnection.__config})"
                )
            time.sleep(0.1)

        MQTTConnection.__client = mqtt_client
