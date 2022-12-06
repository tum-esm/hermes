import json
import os
import queue
import ssl
from typing import Any
from paho.mqtt.client import Client, MQTTMessage
from src import custom_types, utils

# TODO: statically type config messages
mqtt_message_queue = queue.Queue(maxsize=1024)  # type:ignore


def on_message(client: Client, userdata: Any, msg: MQTTMessage) -> None:
    try:
        payload = json.loads(msg.payload.decode())
        mqtt_message_queue.put({"topic": msg.topic, "qos": msg.qos, "payload": payload})
    except json.JSONDecodeError:
        utils.Logger(origin="mqtt-receiver").warning(
            f"could not decode message payload on message: {msg}"
        )


class ReceivingMQTTClient:
    def __init__(self) -> None:
        mqtt_config = custom_types.MQTTConfig(
            url=os.environ.get("INSERT_NAME_HERE_MQTT_URL"),
            port=os.environ.get("INSERT_NAME_HERE_MQTT_PORT"),
            identifier=os.environ.get("INSERT_NAME_HERE_STATION_IDENTIFIER"),
            password=os.environ.get("INSERT_NAME_HERE_MQTT_PASSWORD"),
            base_topic=os.environ.get("INSERT_NAME_HERE_MQTT_BASE_TOPIC"),
        )

        self.client = Client(client_id=mqtt_config.identifier)

        self.client.username_pw_set(mqtt_config.identifier, mqtt_config.password)
        self.client.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED)
        self.client.on_message = on_message

        self.client.connect(mqtt_config.url, port=mqtt_config.port, keepalive=60)
        self.client.subscribe(
            mqtt_config.base_topic + "/initial-setup-test",
        )
        self.client.loop_start()

    def get_messages(self) -> list[Any]:
        new_messages = []
        while True:
            try:
                new_messages.append(mqtt_message_queue.get(block=False))
            except queue.Empty:
                break

        return new_messages
