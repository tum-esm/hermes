import json
from os.path import dirname, abspath, join, isfile
import ssl
import time
from paho.mqtt.client import Client
from src import custom_types, utils
import multiprocessing

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
ACTIVE_QUEUE_FILE = join(PROJECT_DIR, "data", "active-mqtt-queue.json")
QUEUE_ARCHIVE_DIR = join(PROJECT_DIR, "data", "archive")

lock = multiprocessing.Lock()


class SendingMQTTClient:
    def __init__(self, config: custom_types.Config) -> None:
        self.config = config
        self.logger = utils.Logger(origin="mqtt-sender")

        # generate an empty queue file if the file does not exist
        with lock:
            if not isfile(ACTIVE_QUEUE_FILE):
                self._dump_active_queue(
                    custom_types.ActiveMQTTMessageQueue(
                        max_identifier=0,
                        messages=[],
                    )
                )

    def enqueue_message(
        self,
        message_body: custom_types.MQTTStatusMessageBody
        | custom_types.MQTTMeasurementMessageBody,
    ) -> None:
        with lock:
            active_queue = SendingMQTTClient._load_active_queue()
            new_header = custom_types.MQTTMessageHeader(
                identifier=active_queue.max_identifier + 1,
                status="pending",
                revision=self.config.revision,
                issue_timestamp=time.time(),
                success_timestamp=None,
            )
            new_message: custom_types.MQTTStatusMessage | custom_types.MQTTMeasurementMessage

            if isinstance(message_body, custom_types.MQTTStatusMessageBody):
                new_message = custom_types.MQTTStatusMessage(
                    header=new_header, body=message_body
                )
            else:
                new_message = custom_types.MQTTMeasurementMessage(
                    header=new_header, body=message_body
                )

            active_queue.messages.append(new_message)
            active_queue.max_identifier += 1
            SendingMQTTClient._dump_active_queue(active_queue)

    @staticmethod
    def _load_active_queue() -> custom_types.ActiveMQTTMessageQueue:
        with open(ACTIVE_QUEUE_FILE, "r") as f:
            active_queue = custom_types.ActiveMQTTMessageQueue(**json.load(f))
        return active_queue

    @staticmethod
    def _dump_active_queue(active_queue: custom_types.ActiveMQTTMessageQueue) -> None:
        with open(ACTIVE_QUEUE_FILE, "w") as f:
            json.dump(active_queue.dict(), f, indent=4)

    @staticmethod
    def sending_loop(lock: multiprocessing.Lock) -> None:
        """takes messages from the queue file and processes them"""
        logger = utils.Logger(origin="mqtt-sending-loop")
        logger.info("starting loop")

        # TODO: init mqtt client

        while True:
            # TODO: read active queue
            # TODO: for each pending or failed message, send it and set it to sent
            # TODO: for each sent message, check whether it has been successful
            #       -> for each successful message, move it
            #       -> for each failed message, move it
            # TODO: write out new active queue

            # TODO: when any message could not be sent, wait with
            #       exponentially increasing times
            time.sleep(5)
