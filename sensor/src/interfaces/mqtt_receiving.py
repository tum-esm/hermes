import json
import queue
from typing import Any
import paho.mqtt.client
from src import utils

# TODO: statically type config messages
mqtt_message_queue: queue.Queue[dict[Any]] = queue.Queue(maxsize=1024)  # type:ignore


def on_message(
    client: paho.mqtt.client.Client,
    userdata: Any,
    msg: paho.mqtt.client.MQTTMessage,
) -> None:
    global mqtt_message_queue
    logger = utils.Logger(origin="mqtt-receiving-loop")
    logger.debug(f"received message: {msg}")
    try:
        payload = json.loads(msg.payload.decode())
        mqtt_message_queue.put({"topic": msg.topic, "payload": payload})
    except json.JSONDecodeError:
        logger.warning(f"could not decode message payload on message: {msg}")


class ReceivingMQTTClient:
    def __init__(self) -> None:
        logger = utils.Logger(origin="mqtt-receiving-client")
        mqtt_client = utils.mqtt.MQTTClient.get_client()
        mqtt_config = utils.mqtt.MQTTClient.get_config()
        mqtt_client.on_message = on_message
        config_topic = f"{mqtt_config.mqtt_base_topic}/configuration/{mqtt_config.station_identifier}"

        logger.info(f"subscribing to topic {config_topic}")
        mqtt_client.subscribe(
            f"{mqtt_config.mqtt_base_topic}/configuration/"
            + f"{mqtt_config.station_identifier}"
        )

    def get_messages(self) -> list[Any]:
        global mqtt_message_queue

        new_messages = []
        while True:
            try:
                new_messages.append(mqtt_message_queue.get(block=False))
            except queue.Empty:
                break

        return new_messages
