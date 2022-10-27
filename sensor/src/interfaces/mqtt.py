from datetime import datetime
import time
from typing import Any
from src import types
from paho.mqtt.client import Client
import ssl


def log(message: str) -> None:
    with open("send.log", "a") as f:
        f.write(f"{datetime.now()} {message}\n")


# TODO: Put message into global queue (shared between threads)
def on_message(*args: Any, **kwargs: dict[str, Any]) -> None:
    log(f"on_message: {args}, {kwargs}")


# TODO: Log as debug line
def on_connect(*args: Any, **kwargs: dict[str, Any]) -> None:
    log(f"on_connect: {args}, {kwargs}")


# TODO: Log as debug line
def on_publish(*args: Any, **kwargs: dict[str, Any]) -> None:
    log(f"on_publish: {args}, {kwargs}")


# TODO: Log as debug line
def on_subscribe(*args: Any, **kwargs: dict[str, Any]) -> None:
    log(f"on_subscribe: {args}, {kwargs}")


class MQTTInterface:
    def __init__(self, config: types.Config) -> None:
        # TODO: initialize shared queue

        client = Client(client_id=config.general.node_id)
        client.username_pw_set(config.mqtt.identifier, config.mqtt.password)
        client.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED)

        # TODO: pass shared queue to on_message function
        client.on_message = on_message
        client.on_connect = on_connect
        client.on_publish = on_publish
        client.on_subscribe = on_subscribe

        client.connect(config.mqtt.url, port=8883, keepalive=60)
        log("client connected")

        client.subscribe("/development/moritz/initial-setup-test")

        client.loop_start()
        log("loop started")

        while True:
            time.sleep(10)

    @staticmethod
    def get_messages(config: types.Config) -> list[Any]:
        # TODO: return messages from shared queue
        return []
