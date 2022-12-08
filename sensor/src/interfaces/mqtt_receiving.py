import json
import queue
from typing import Any
import paho.mqtt.client
from src import utils

# TODO: statically type config messages
mqtt_message_queue = queue.Queue(maxsize=1024)  # type:ignore


def on_message(
    client: paho.mqtt.client.Client,
    userdata: Any,
    msg: paho.mqtt.client.MQTTMessage,
) -> None:
    try:
        payload = json.loads(msg.payload.decode())
        mqtt_message_queue.put({"topic": msg.topic, "qos": msg.qos, "payload": payload})
    except json.JSONDecodeError:
        utils.Logger(origin="mqtt-receiver").warning(
            f"could not decode message payload on message: {msg}"
        )


class ReceivingMQTTClient:
    def __init__(self) -> None:
        self.mqtt_client, self.mqtt_config = utils.mqtt.get_mqtt_client()
        self.mqtt_client.on_message = on_message
        self.mqtt_client.subscribe(
            f"{self.mqtt_config.mqtt_base_topic}/configuration/"
            + f"{self.mqtt_config.station_identifier}"
        )
        self.mqtt_client.loop_start()

    def get_messages(self) -> list[Any]:
        new_messages = []
        while True:
            try:
                new_messages.append(mqtt_message_queue.get(block=False))
            except queue.Empty:
                break

        return new_messages
