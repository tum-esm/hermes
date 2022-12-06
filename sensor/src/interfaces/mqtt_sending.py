import json
from os.path import dirname, abspath, join, isfile
import ssl
import time
from paho.mqtt.client import Client
from src import custom_types, utils

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
ACTIVE_QUEUE_FILE = join(PROJECT_DIR, "data", "active-mqtt-queue.json")
QUEUE_ARCHIVE_DIR = join(PROJECT_DIR, "data", "archive")


class SendingMQTTClient:
    def __init__(self, config: custom_types.Config) -> None:
        self.config = config
        self.logger = utils.Logger(config, origin="sending-mqtt-client")

        # TODO: lock
        # generate an empty queue file if the file does not exist
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
        # TODO: lock the whole function
        active_queue = self._load_active_queue()
        new_header = custom_types.MQTTMessageHeader(
            identifier=active_queue.max_identifier + 1,
            status="pending",
            revision=0,  # TODO: use from self.config.revision,
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
        self._dump_active_queue(active_queue)

    def _load_active_queue(self) -> custom_types.ActiveMQTTMessageQueue:
        with open(ACTIVE_QUEUE_FILE, "r") as f:
            active_queue = custom_types.ActiveMQTTMessageQueue(**json.load(f))
        return active_queue

    def _dump_active_queue(
        self, active_queue: custom_types.ActiveMQTTMessageQueue
    ) -> None:
        with open(ACTIVE_QUEUE_FILE, "w") as f:
            json.dump(f, active_queue.dict(), indent=4)

    # TODO: function to pick messages from the queue file and process them
