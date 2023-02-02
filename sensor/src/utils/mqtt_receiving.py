import json
import queue
import ssl
from typing import Any, Optional
import paho.mqtt.client
import paho.mqtt.subscribe
from .logger import Logger
from .mqtt_connection import MQTTConnection
from src import custom_types

mqtt_config_message_queue: queue.Queue[
    custom_types.MQTTConfigurationRequest
] = queue.Queue()


def on_message(
    client: paho.mqtt.client.Client,
    userdata: Any,
    msg: paho.mqtt.client.MQTTMessage,
) -> None:
    global mqtt_config_message_queue
    logger = Logger(origin="mqtt-receiving-loop")
    logger.debug(f"received message: {msg}")
    try:
        mqtt_config_message_queue.put(
            custom_types.MQTTConfigurationRequest(**json.loads(msg.payload.decode()))
        )
    except json.JSONDecodeError:
        logger.warning(f"could not decode message payload on message: {msg}")


class ReceivingMQTTClient:
    def __init__(self) -> None:
        self.logger = Logger(origin="mqtt-receiving-client")
        self.mqtt_config = MQTTConnection.get_config()
        self.config_topic = (
            f"{self.mqtt_config.mqtt_base_topic}configuration"
            + f"/{self.mqtt_config.station_identifier}"
        )

        # subscribing to new messages on config topic
        mqtt_client = MQTTConnection.get_client()
        mqtt_client.on_message = on_message
        self.logger.info(f"subscribing to topic {self.config_topic}")
        mqtt_client.subscribe(self.config_topic)

    def get_retained_config_message(
        self,
    ) -> Optional[custom_types.MQTTConfigurationRequest]:
        """Only used on startup, otherwise too bandwidth intensive"""
        retained_messages: list[
            paho.mqtt.client.MQTTMessage
        ] = paho.mqtt.subscribe.simple(
            topic=self.config_topic,
            client_id=self.mqtt_config.station_identifier,
            tls=ssl.create_default_context(),
            msg_count=10,
            retained=True,
            auth={
                "username": MQTTConnection.__config.mqtt_username,
                "password": MQTTConnection.__config.mqtt_password,
            },
            hostname=MQTTConnection.__config.mqtt_url,
            port=int(MQTTConnection.__config.mqtt_port),
        )

        config_messages: list[custom_types.MQTTConfigurationRequest] = []
        for msg in retained_messages:
            try:
                config_messages.append(
                    custom_types.MQTTConfigurationRequest(
                        **json.loads(msg.payload.decode())
                    )
                )
            except:
                pass

        if len(config_messages) == 0:
            self.logger.warning("did not find any retained valid config messages")
            return None

        return max(config_messages, key=lambda cm: cm.revision)

    def get_config_message(self) -> Optional[custom_types.MQTTConfigurationRequest]:
        global mqtt_config_message_queue

        new_config_messages: list[custom_types.MQTTConfigurationRequest] = []
        while True:
            try:
                new_config_messages.append(mqtt_config_message_queue.get(block=False))
            except queue.Empty:
                break

        if len(new_config_messages) == 0:
            self.logger.warning("did not find any retained valid config messages")
            return None

        return max(new_config_messages, key=lambda cm: cm.revision)
