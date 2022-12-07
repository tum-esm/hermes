import json
import time
import paho.mqtt.client
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
                identifier=None,
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
        # TODO: when active queue could not be loaded, move file to
        #       "corrupt" directory and start a new active queue file
        return active_queue

    @staticmethod
    def _dump_active_queue(active_queue: custom_types.ActiveMQTTMessageQueue) -> None:
        with open(ACTIVE_QUEUE_FILE, "w") as f:
            json.dump(active_queue.dict(), f, indent=4)

    # TODO: function "archive_successful_messages" that moves a list of
    #       messages to the archive directory

    @staticmethod
    def sending_loop(lock: multiprocessing.synchronize.Lock) -> None:
        """takes messages from the queue file and processes them"""
        logger = utils.Logger(origin="mqtt-sending-loop")
        logger.info("starting loop")

        mqtt_client, mqtt_config = utils.mqtt.get_mqtt_client()

        # this queue is necessary because paho-mqtt does not support
        # a function that answers the question "has this message id
        # been delivered successfully?"
        current_messages: dict[int, paho.mqtt.client.MQTTMessageInfo] = {}

        while True:
            with lock:
                active_queue = SendingMQTTClient._load_active_queue()
            sent_messages = []
            resent_messages = []
            successful_messages = []
            for message in active_queue.messages:
                if message.header.status in ["pending", "failed"]:
                    message_info = mqtt_client.publish(
                        topic=f"{mqtt_config.base_topic}/measurements/{mqtt_config.identifier}",
                        payload=[message.body.dict()],
                        qos=1,
                    )
                    message.header.identifier = message_info.mid
                    message.header.status = "sent"
                    current_messages[message.header.identifier] = message_info
                    sent_messages.append(message)

                elif message.header.status == "sent":
                    assert message.header.identifier is not None
                    message_info = current_messages.get(message.header.identifier, None)

                    if message_info is not None:
                        if message_info.is_published():
                            message.header.status = "successful"
                            message.header.success_timestamp = time.time()
                            successful_messages.append(message)
                            del current_messages[message.header.identifier]

                    # current_messages are lost when restarting the program
                    else:
                        message_info = mqtt_client.publish(
                            topic=f"{mqtt_config.base_topic}/measurements/{mqtt_config.identifier}",
                            payload=[message.body.dict()],
                            qos=1,
                        )
                        message.header.identifier = message_info.mid
                        current_messages[message.header.identifier] = message_info
                        resent_messages.append(message)

            active_queue.messages = list(
                filter(lambda m: m.header.status != "successful", active_queue.messages)
            )
            # TODO: move successful messages

            SendingMQTTClient._dump_active_queue(active_queue)

            logger.info(f"{len(sent_messages)} message(s) have been sent")
            logger.info(f"{len(resent_messages)} message(s) have been resent")
            logger.info(f"{len(successful_messages)} message(s) have been delivered")

            # TODO: adjust wait time based on length of "current_messages"
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

        # TODO: log when the last successful message has been sent
        # TODO: log how many messages were sent today
        pass

    # TODO: function "add_for_message_sending" that blocks until the
    #       active queue is empty
