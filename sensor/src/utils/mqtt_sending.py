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
QUEUE_ARCHIVE_DIR = os.path.join(PROJECT_DIR, "data", "archive")


class SendingMQTTClient:
    sending_loop_process: Optional[multiprocessing.Process] = None
    archiving_loop_process: Optional[multiprocessing.Process] = None

    def __init__(self) -> None:
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

    def enqueue_message(
        self, config: custom_types.Config, message_body: custom_types.MQTTMessageBody
    ) -> None:
        if config.active_components.mqtt_data_sending:
            assert (
                SendingMQTTClient.sending_loop_process is not None
            ), "sending loop process has not been initialized"
        assert (
            SendingMQTTClient.archiving_loop_process is not None
        ), "archiving loop process has not been initialized"

        new_header = custom_types.MQTTMessageHeader(
            mqtt_topic=None,
            sending_skipped=(not config.active_components.mqtt_data_sending),
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

        self.active_mqtt_queue.add_row(
            new_message,
            status="pending" if config.active_components.mqtt_data_sending else "done",
        )

    @staticmethod
    def archiving_loop() -> None:
        """archive all message in the active queue that have the
        status `delivered` or `sending-skipped`; this function is
        blocking and should be called in a thread or subprocess"""

        messages_to_be_archived: dict[str, list[custom_types.MQTTMessage]] = {}
        active_mqtt_queue = ActiveMQTTQueue()

        while True:
            # DETERMINE MESSAGES TO BE ARCHIVED
            records_to_be_archived = active_mqtt_queue.get_rows_by_status("done")

            # SPLIT RECORDS BY DATE
            messages_to_be_archived = {}
            for record in records_to_be_archived:
                date_string = datetime.datetime.fromtimestamp(
                    record.content.body.timestamp, tz=pytz.timezone("UTC")
                ).strftime("%Y-%m-%d")
                if date_string not in messages_to_be_archived.keys():
                    messages_to_be_archived[date_string] = []
                messages_to_be_archived[date_string].append(record.content)

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
                        f.write(json.dumps(m.dict()) + "\n")

            # DUMP REMAINING ACTIVE MESSAGES
            active_mqtt_queue.remove_archive_messages()

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
        active_mqtt_queue = ActiveMQTTQueue()

        # this queue is necessary because paho-mqtt does not support
        # a function that answers the question "has this message id
        # been delivered successfully?"
        current_records: dict[int, paho.mqtt.client.MQTTMessageInfo] = {}

        # -----------------------------------------------------------------

        def _publish_record(record: custom_types.SQLMQTTRecord) -> None:
            record.content.header.mqtt_topic = mqtt_config.mqtt_base_topic
            record.content.header.mqtt_topic += (
                "statuses/" if record.content.variant == "status" else "measurements/"
            )
            record.content.header.mqtt_topic += mqtt_config.station_identifier
            message_info = mqtt_client.publish(
                topic=record.content.header.mqtt_topic,
                payload=json.dumps([record.content.body.dict()]),
                qos=1,
            )
            current_records[record.internal_id] = message_info

        # -----------------------------------------------------------------

        while True:
            sent_record_count = 0
            resent_record_count = 0
            delivered_record_count = 0
            record_ids_to_be_archived: list[int] = []

            # -----------------------------------------------------------------
            # CHECK DELIVERY STATUS OF SENT MESSAGES

            sent_records = active_mqtt_queue.get_rows_by_status("in-progress")

            for record in sent_records:
                # normal behavior
                if record.internal_id in current_records.keys():
                    if current_records[record.internal_id].is_published():
                        delivered_record_count += 1
                        del current_records[record.internal_id]
                        record_ids_to_be_archived.append(record.internal_id)

                # resending is required, when current_messages are
                # lost due to restarting the program
                else:
                    _publish_record(record)
                    resent_record_count += 1

            # mark successful messages in active queue
            active_mqtt_queue.update_row_status_by_id(record_ids_to_be_archived, "done")

            # -----------------------------------------------------------------
            # SEND PENDING MESSAGES

            MAX_SEND_COUNT = 100
            OPEN_SENDING_SLOTS = MAX_SEND_COUNT - (
                len(sent_records) - delivered_record_count
            )
            if OPEN_SENDING_SLOTS <= 0:
                logger.debug(
                    f"sending queue is full ({MAX_SEND_COUNT} "
                    + "items not processed by broker yet)"
                )
            else:
                logger.debug(f"sending queue has {OPEN_SENDING_SLOTS} more slot(s)")

                records_to_be_sent = active_mqtt_queue.get_rows_by_status(
                    "pending", limit=OPEN_SENDING_SLOTS
                )
                for record in records_to_be_sent:
                    _publish_record(record)
                    sent_record_count += 1
                active_mqtt_queue.update_row_status_by_id(
                    internal_ids=[r.internal_id for r in records_to_be_sent],
                    new_status="in-progress",
                )

            # -----------------------------------------------------------------

            logger.info(
                f"{sent_record_count}/{resent_record_count}/{delivered_record_count} "
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
