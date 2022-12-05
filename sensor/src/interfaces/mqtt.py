import json
import queue
import ssl
from typing import Any
from paho.mqtt.client import Client, MQTTMessage
from src import custom_types

# TODO: statically type messages
mqtt_message_queue = queue.Queue(maxsize=1024)  # type:ignore


# print message, useful for checking if it was successful
def on_message(client: Client, userdata: Any, msg: MQTTMessage) -> None:
    try:
        payload = json.loads(msg.payload.decode())
        mqtt_message_queue.put({"topic": msg.topic, "qos": msg.qos, "payload": payload})
    except json.JSONDecodeError:
        # TODO: log
        pass


class MQTTInterface:
    def __init__(self, config: custom_types.Config) -> None:
        self.config = config
        self.client = Client(client_id=self.config.general.station_name)

        self.client.username_pw_set(config.mqtt.identifier, config.mqtt.password)
        self.client.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED)
        self.client.on_message = on_message

        self.client.connect(config.mqtt.url, port=config.mqtt.port, keepalive=60)
        self.client.subscribe(
            config.mqtt.base_topic + "/initial-setup-test",
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
