from typing import Any
from src import types
from paho.mqtt.client import Client
import ssl
import queue

mqtt_message_queue = queue.Queue(maxsize=1024)


def on_message(*args: Any, **kwargs: dict[str, Any]) -> None:
    mqtt_message_queue.put(f"on_message: {args}, {kwargs}")


class MQTTInterface:
    def __init__(self, config: types.Config) -> None:
        self.config = config
        self.client = Client(client_id=self.config.general.node_id)

        self.client.username_pw_set(config.mqtt.identifier, config.mqtt.password)
        self.client.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED)
        self.client.on_message = on_message

        # TODO: Move port into config
        self.client.connect(config.mqtt.url, port=8883, keepalive=60)
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
