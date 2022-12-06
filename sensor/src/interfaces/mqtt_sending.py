from os.path import dirname, abspath, join
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
        self.logger = utils.Logger(origin="sending-mqtt-client")

    # TODO: function to pick messages from the queue file and process them

    def enqueue_status_message(
        self, message_body: custom_types.MQTTStatusMessageBody
    ) -> None:
        self._add_message_to_queue_file(
            custom_types.MQTTStatusMessage(
                header=self._generate_header(),
                body=message_body,
            )
        )

    def enqueue_measurement_message(
        self, message_body: custom_types.MQTMeasurementMessageBody
    ) -> None:
        self._add_message_to_queue_file(
            custom_types.MQTMeasurementMessage(
                header=self._generate_header(),
                body=message_body,
            )
        )

    def _generate_header(self) -> custom_types.MQTTMessageHeader:
        # TODO: determine new identifier from queue
        new_identifier = 0

        # TODO: increment new_identifier in queue file

        return custom_types.MQTTMessageHeader(
            identifier=new_identifier,
            status="pending",
            revision=self.config.revision,
            issue_timestamp=time.time(),
            success_timestamp=None,
        )

    def _add_message_to_queue_file(
        self,
        message: custom_types.MQTTStatusMessage | custom_types.MQTTMeasurementMessage,
    ) -> None:
        pass
        # TODO: add message to queue file
        # TODO: increment new_identifier in queue file
