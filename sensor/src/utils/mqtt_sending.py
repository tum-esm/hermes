import datetime
import json
import time
from typing import Callable, Literal, Optional
import paho.mqtt.client
import os
from os.path import dirname
import pytz
import multiprocessing
import multiprocessing.synchronize
import filelock
from src import custom_types
from .mqtt_connection import MQTTConnection
from .active_mqtt_queue import ActiveMQTTQueue

PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
ACTIVE_QUEUE_FILE = os.path.join(PROJECT_DIR, "data", "incomplete-mqtt-messages.json")
ACTIVE_QUEUE_LOCK = os.path.join(PROJECT_DIR, "data", "incomplete-mqtt-messages.lock")

QUEUE_ARCHIVE_DIR = os.path.join(PROJECT_DIR, "data", "archive")

active_queue_lock = filelock.FileLock(ACTIVE_QUEUE_LOCK, timeout=10)


class SendingMQTTClient:
    sending_loop_process: Optional[multiprocessing.Process] = None
    archiving_loop_process: Optional[multiprocessing.Process] = None

    def __init__(self, config: custom_types.Config) -> None:
        self.config = config
        self.active_mqtt_queue = ActiveMQTTQueue()

    @staticmethod
    def init_sending_loop_process() -> None:
        """start the sending of messages in the active queue in a subprocess"""
        if SendingMQTTClient.sending_loop_process is None:
            new_process = multiprocessing.Process(
                target=SendingMQTTClient.sending_loop,
                daemon=True,
            )
            new_process.start()
            SendingMQTTClient.sending_loop_process = new_process

    @staticmethod
    def init_archiving_loop_process() -> None:
        """start the archiving of messages in the active queue in a subprocess"""
        if SendingMQTTClient.archiving_loop_process is None:
            new_process = multiprocessing.Process(
                target=SendingMQTTClient.archiving_loop,
                daemon=True,
            )
            new_process.start()
            SendingMQTTClient.archiving_loop_process = new_process

    @staticmethod
    def deinit_sending_loop_process() -> None:
        """stop the sending of messages in the active queue in a subprocess"""
        if SendingMQTTClient.sending_loop_process is not None:
            SendingMQTTClient.sending_loop_process.terminate()
            SendingMQTTClient.sending_loop_process = None

    @staticmethod
    def deinit_archiving_loop_process() -> None:
        """stop the archiving of messages in the active queue in a subprocess"""
        if SendingMQTTClient.archiving_loop_process is not None:
            SendingMQTTClient.archiving_loop_process.terminate()
            SendingMQTTClient.archiving_loop_process = None

    def enqueue_message(self, message_body: custom_types.MQTTMessageBody) -> None:
        if self.config.active_components.mqtt_data_sending:
            assert (
                SendingMQTTClient.sending_loop_process is not None
            ), "sending loop process has not been initialized"
        assert (
            SendingMQTTClient.archiving_loop_process is not None
        ), "archiving loop process has not been initialized"

        new_header = custom_types.MQTTMessageHeader(
            mqtt_topic=None,
            sending_skipped=(not self.config.active_components.mqtt_data_sending),
        )
        new_message: custom_types.MQTTMessage

        if isinstance(message_body, custom_types.MQTTStatusMessageBody):
            new_message = custom_types.MQTTStatusMessage(
                variant="status", header=new_header, body=message_body
            )
        else:
            new_message = custom_types.MQTTDataMessage(
                variant="data", header=new_header, body=message_body
            )

        self.active_mqtt_queue.add_row(new_message)

    @staticmethod
    def _load_active_queue() -> custom_types.ActiveMQTTMessageQueue:
        with active_queue_lock:
            # generate an empty queue file if the file does not exist
            if os.path.isfile(ACTIVE_QUEUE_FILE):
                with open(ACTIVE_QUEUE_FILE, "r") as f:
                    active_queue = custom_types.ActiveMQTTMessageQueue(**json.load(f))
            else:
                active_queue = custom_types.ActiveMQTTMessageQueue(
                    max_identifier=0,
                    messages=[],
                )
                with open(ACTIVE_QUEUE_FILE, "w") as f:
                    json.dump(active_queue.dict(), f, indent=4)

        return active_queue

    @staticmethod
    def _dump_active_queue(
        updated_active_queue: custom_types.ActiveMQTTMessageQueue,
        known_message_ids: Optional[list[int]] = None,
    ) -> None:
        """save an active queue to the active queue json file;

        use the `known_message_ids` parameter to mark which messages
        have been present at the time of active queue loading -> by
        this messages can be added from one thread while another one
        is processing an active queue loaded before the additions
        """

        with active_queue_lock:
            if known_message_ids is None:
                with open(ACTIVE_QUEUE_FILE, "w") as f:
                    json.dump(updated_active_queue.dict(), f, indent=4)
            else:
                # add messages that have been added since calling
                # "_load_active_queue" at the beginning of the loop
                racing_messages = [
                    m
                    for m in SendingMQTTClient._load_active_queue().messages
                    if (m.header.identifier not in known_message_ids)
                ]
                updated_active_queue.messages += racing_messages
                with open(ACTIVE_QUEUE_FILE, "w") as f:
                    json.dump(updated_active_queue.dict(), f, indent=4)

    @staticmethod
    def archiving_loop() -> None:
        """archive all message in the active queue that have the
        status `delivered` or `sending-skipped`; this function is
        blocking and should be called in a thread or subprocess"""

        filename_for_datestring: Callable[
            [str], str
        ] = lambda date_string: os.path.join(
            QUEUE_ARCHIVE_DIR, f"delivered-mqtt-messages-{date_string}.json"
        )

        known_message_ids: list[int] = []
        messages_to_be_archived: dict[str, list[custom_types.MQTTMessage]] = {}
        archived_message_ids: list[int] = []

        while True:

            # -----------------------------------------------------------------
            # LOAD CURRENT ACTIVE QUEUE

            active_queue = SendingMQTTClient._load_active_queue()
            known_message_ids = [m.header.identifier for m in active_queue.messages]
            messages_to_be_archived = {}
            archived_message_ids = []

            # -----------------------------------------------------------------
            # DETERMINE MESSAGES TO BE ARCHIVED

            for m in active_queue.messages:
                if m.header.status in ["delivered", "sending-skipped"]:
                    archived_message_ids.append(m.header.identifier)
                    date_string = datetime.datetime.fromtimestamp(
                        m.body.timestamp, tz=pytz.timezone("UTC")
                    ).strftime("%Y-%m-%d")
                    if date_string not in messages_to_be_archived.keys():
                        messages_to_be_archived[date_string] = []
                    messages_to_be_archived[date_string].append(m)

            # -----------------------------------------------------------------
            # DUMP ARCHIVE MESSAGES

            for date_string, messages in messages_to_be_archived.items():
                with open(
                    os.path.join(
                        QUEUE_ARCHIVE_DIR,
                        f"delivered-mqtt-messages-{date_string}.json",
                    ),
                    "a",
                ) as f:
                    for m in messages:
                        f.write(json.dump(m.dict()) + ",\n")

            # -----------------------------------------------------------------
            # DUMP REMAINING ACTIVE MESSAGES

            active_queue.messages = list(
                filter(
                    lambda m: m.header.identifier not in archived_message_ids,
                    active_queue.messages,
                )
            )
            SendingMQTTClient._dump_active_queue(
                active_queue, known_message_ids=known_message_ids
            )

            # -----------------------------------------------------------------

            time.sleep(5)

    @staticmethod
    def sending_loop() -> None:
        """takes messages from the queue file and processes them;
        this function is blocking and should be called in a thread
        os subprocess"""
        from src import utils

        logger = utils.Logger(origin="mqtt-sending-loop")
        logger.info("starting loop")

        mqtt_client = MQTTConnection.get_client()
        mqtt_config = MQTTConnection.get_config()

        # this queue is necessary because paho-mqtt does not support
        # a function that answers the question "has this message id
        # been delivered successfully?"
        current_messages: dict[int, paho.mqtt.client.MQTTMessageInfo] = {}

        # -----------------------------------------------------------------

        def _publish_mqtt_message(message: custom_types.MQTTMessage) -> None:
            if message.variant == "status":
                topic = f"{mqtt_config.mqtt_base_topic}statuses/{mqtt_config.station_identifier}"
            else:
                topic = f"{mqtt_config.mqtt_base_topic}measurements/{mqtt_config.station_identifier}"
            message.header.mqtt_topic = topic
            message_info = mqtt_client.publish(
                topic=message.header.mqtt_topic,
                payload=json.dumps([message.body.dict()]),
                qos=1,
            )
            message.header.status = "sent"
            current_messages[message.header.identifier] = message_info

        # -----------------------------------------------------------------

        while True:
            active_queue = SendingMQTTClient._load_active_queue()
            known_message_ids = [m.header.identifier for m in active_queue.messages]

            processed_message_ids: dict[
                Literal["sent", "resent", "delivered"],
                list[int],
            ] = {
                "sent": [],
                "resent": [],
                "delivered": [],
            }

            # -----------------------------------------------------------------
            # CHECK DELIVERY STATUS OF SENT MESSAGES

            for message in active_queue.messages:
                if message.header.status == "sent":
                    # normal behavior
                    if message.header.identifier in current_messages:
                        if current_messages[message.header.identifier].is_published():
                            message.header.status = "delivered"
                            message.header.delivery_timestamp = time.time()
                            processed_message_ids["delivered"].append(
                                message.header.identifier
                            )
                            del current_messages[message.header.identifier]

                    # resending is required, when current_messages are
                    # lost due to restarting the program
                    else:
                        _publish_mqtt_message(message)
                        processed_message_ids["resent"].append(
                            message.header.identifier
                        )

            # -----------------------------------------------------------------
            # SEND PENDING MESSAGES

            MAX_SEND_COUNT = 100
            current_send_count = len(
                [
                    m
                    for m in active_queue.messages
                    if m.header.status in ["sent", "resent"]
                ]
            )

            for message in active_queue.messages:
                if current_send_count >= MAX_SEND_COUNT:
                    logger.info(
                        "max. send count of 100 reached, waiting for "
                        + "message deliveries until sending new ones."
                    )
                    continue
                if message.header.status == "pending":
                    _publish_mqtt_message(message)
                    processed_message_ids["sent"].append(message.header.identifier)
                    current_send_count += 1

            # -----------------------------------------------------------------
            # SAVE NEW ACTIVE QUEUE FILE AND TRIGGER MESSAGE ARCHIVING

            SendingMQTTClient._dump_active_queue(
                active_queue, known_message_ids=known_message_ids
            )

            # -----------------------------------------------------------------

            logger.info(
                f"{len(processed_message_ids['sent'])}/"
                + f"{len(processed_message_ids['resent'])}/"
                + f"{len(processed_message_ids['delivered'])} "
                + "messages have been sent/resent/delivered"
            )

            time.sleep(5)

    @staticmethod
    def check_errors() -> None:
        """checks whether the sending loop process is still running"""

        if SendingMQTTClient.sending_loop_process is not None:
            assert (
                SendingMQTTClient.sending_loop_process.is_alive()
            ), "sending loop process is not running"

        if SendingMQTTClient.archiving_loop_process is not None:
            assert (
                SendingMQTTClient.archiving_loop_process.is_alive()
            ), "archiving loop process is not running"
