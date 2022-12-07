import json
import time
from os.path import dirname, abspath, join, isfile
from src import custom_types, utils
import multiprocessing
import multiprocessing.synchronize

PROJECT_DIR = dirname(dirname(dirname(abspath(__file__))))
ACTIVE_QUEUE_FILE = join(PROJECT_DIR, "data", "active-mqtt-queue.json")
QUEUE_ARCHIVE_DIR = join(PROJECT_DIR, "data", "archive")

lock = multiprocessing.Lock()


class SendingMQTTClient:
    sending_loop_process: multiprocessing.Process | None = None

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

        if SendingMQTTClient.sending_loop_process is None:
            new_process = multiprocessing.Process(
                target=SendingMQTTClient.sending_loop, args=(lock,)
            )
            new_process.start()
            SendingMQTTClient.sending_loop_process = new_process

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
    def sending_loop(lock: multiprocessing.synchronize.Lock) -> None:
        """takes messages from the queue file and processes them"""
        logger = utils.Logger(origin="mqtt-sending-loop")
        logger.info("starting loop")

        mqtt_client, mqtt_config = utils.mqtt.get_mqtt_client()

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

    @staticmethod
    def check_errors() -> None:
        """checks whether the sending loop process is still running"""

        if SendingMQTTClient.sending_loop_process is not None:
            assert (
                SendingMQTTClient.sending_loop_process.is_alive()
            ), "sending loop process is not running"

    @staticmethod
    def log_statistics() -> None:
        """logs a few statistics about the current MQTT sending activity"""

        # TODO: log how many messages are pending/sent/...
        # TODO: log when the last successful message has been sent
        # TODO: log how many messages were sent today
        pass
