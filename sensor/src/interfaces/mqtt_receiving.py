import json
import queue
from typing import Any
import paho.mqtt.client
from src import utils

# TODO: statically type config messages
mqtt_message_queue = queue.Queue(maxsize=1024)  # type:ignore


def get_message_callback(queue: queue.Queue) -> Any:
    def on_message(
        client: paho.mqtt.client.Client,
        userdata: Any,
        msg: paho.mqtt.client.MQTTMessage,
    ) -> None:
        logger = utils.Logger(origin="mqtt-receiving-loop")
        logger.debug(f"received message: {msg}")
        try:
            # payload = json.loads(msg.payload.decode())
            queue.put(msg)
        except json.JSONDecodeError:
            logger.warning(f"could not decode message payload on message: {msg}")

    return on_message


class ReceivingMQTTClient:
    def __init__(self) -> None:
        logger = utils.Logger(origin="mqtt-receiving-client")
        self.mqtt_client, self.mqtt_config = utils.mqtt.get_mqtt_client()
        self.mqtt_client.on_message = get_message_callback(queue)
        config_topic = f"{self.mqtt_config.mqtt_base_topic}/configuration/{self.mqtt_config.station_identifier}"

        logger.info(f"subscribing to topic {config_topic}")
        self.mqtt_client.subscribe(
            f"{self.mqtt_config.mqtt_base_topic}/configuration/"
            + f"{self.mqtt_config.station_identifier}"
        )

        logger.info(f"starting receiving loop")
        self.mqtt_client.loop_start()

    def get_messages(self) -> list[Any]:
        new_messages = []
        while True:
            try:
                new_messages.append(mqtt_message_queue.get(block=False))
            except queue.Empty:
                break

        return new_messages
