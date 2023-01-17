import json
import queue
from typing import Any, Optional
import paho.mqtt.client
from .logger import Logger
from .mqtt_connection import MQTTConnection
from src import custom_types

mqtt_message_queue: queue.Queue[dict] = queue.Queue(maxsize=1024)  # type:ignore


def on_message(
    client: paho.mqtt.client.Client,
    userdata: Any,
    msg: paho.mqtt.client.MQTTMessage,
) -> None:
    global mqtt_message_queue
    logger = Logger(origin="mqtt-receiving-loop")
    logger.debug(f"received message: {msg}")
    try:
        payload = json.loads(msg.payload.decode())
        mqtt_message_queue.put(payload)
    except json.JSONDecodeError:
        logger.warning(f"could not decode message payload on message: {msg}")


class ReceivingMQTTClient:
    def __init__(self) -> None:
        logger = Logger(origin="mqtt-receiving-client")
        mqtt_client = MQTTConnection.get_client()
        mqtt_config = MQTTConnection.get_config()
        mqtt_client.on_message = on_message
        config_topic = f"{mqtt_config.mqtt_base_topic}/configuration/{mqtt_config.station_identifier}"

        logger.info(f"subscribing to topic {config_topic}")
        mqtt_client.subscribe(
            f"{mqtt_config.mqtt_base_topic}/configuration/"
            + f"{mqtt_config.station_identifier}"
        )

    def get_config_message(self) -> Optional[custom_types.MQTTConfigurationRequest]:
        global mqtt_message_queue

        new_config_messages: list[custom_types.MQTTConfigurationRequest] = []
        while True:
            try:
                new_message = mqtt_message_queue.get(block=False)
            except queue.Empty:
                break
            try:
                new_config_message = custom_types.MQTTConfigurationRequest(
                    **new_message
                )
                new_config_messages.append(new_config_message)
            except:
                pass

        if len(new_config_messages) > 0:
            return max(new_config_messages, key=lambda m: m.revision)
