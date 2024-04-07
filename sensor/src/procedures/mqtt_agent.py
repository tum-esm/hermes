import json
import multiprocessing
import multiprocessing.synchronize
import os
import queue
import signal
import sys
import time
from typing import Any, Callable, Optional

import paho.mqtt.client
import pydantic

from run_automation import DOTENV_PATH
from src import custom_types, utils


class MQTTAgent:
    communication_loop_process: Optional[multiprocessing.Process] = None
    config_request_queue: queue.Queue[
        custom_types.MQTTConfigurationRequest
    ] = multiprocessing.Queue()

    class CommunicationOutage(Exception):
        """raised when the communication loop has stopped unexpectedly"""

    @staticmethod
    def init(config: custom_types.Config) -> None:
        """start the communication loop in a separate process"""

        # the communication loop starts a connection to the
        # mqtt broker, receives config messages and send out
        # messages from the active queue db
        if MQTTAgent.communication_loop_process is None:
            if config.active_components.send_messages_over_mqtt:
                new_process = multiprocessing.Process(
                    target=MQTTAgent.communication_loop,
                    args=(
                        config,
                        MQTTAgent.config_request_queue,
                    ),
                    daemon=True,
                )
                new_process.start()
                MQTTAgent.communication_loop_process = new_process

        # wait until messaging agent has
        # TODO: finish sentence
        time.sleep(2)

    @staticmethod
    def deinit() -> None:
        """stop the communication loop process"""

        if MQTTAgent.communication_loop_process is not None:
            MQTTAgent.communication_loop_process.terminate()
            MQTTAgent.communication_loop_process.join()
            MQTTAgent.communication_loop_process = None

    @staticmethod
    def communication_loop(
        config: custom_types.Config,
        config_request_queue: queue.Queue[custom_types.MQTTConfigurationRequest],
        end_after_one_loop: bool = False,
    ) -> None:
        """takes messages from the queue file and processes them;
        this function is blocking and should be called in a thread
        os subprocess"""
        logger = utils.Logger(origin="message-communication", print_to_console=os.environ.get("HERMES_MODE") == "simulate")
        logger.info("starting loop")

        try:
            mqtt_connection = utils.MQTTConnection()
            mqtt_config = mqtt_connection.config
            mqtt_client = mqtt_connection.client
            message_queue = utils.MessageQueue()
        except Exception as e:
            logger.exception(
                e,
                label="could not start connection to mqtt broker",
                config=config,
            )
            raise e

        logger.info(
            "established connection to mqtt broker and active mqtt queue",
        )

        # periodically send a heartbeat message
        state = utils.StateInterface.read()

        def _enqueue_heartbeat_message() -> None:
            message_queue.enqueue_message(
                config,
                custom_types.MQTTAcknowledgmentMessageBody(
                    revision=state.current_config_revision,
                    success=True,
                ),
                "v1/devices/me/telemetry"
            )

        # tear down connection on program termination
        def _graceful_teardown(*_args: Any) -> None:
            logger.info("starting graceful shutdown")
            mqtt_connection.teardown()
            MQTTAgent.communication_loop_process = None
            logger.info("finished graceful shutdown")

        signal.signal(signal.SIGINT, _graceful_teardown)
        signal.signal(signal.SIGTERM, _graceful_teardown)
        logger.info("established graceful teardown hook")

        quit_signal = False

        def quit_now():
            nonlocal quit_signal
            quit_signal = True
            _graceful_teardown()

        try:
            config_topic = (
                f"{mqtt_config.mqtt_base_topic}configurations"
                + f"/{mqtt_config.station_identifier}"
            )
            mqtt_client.on_message = MQTTAgent.__on_mqtt_message(config_request_queue, quit_now)
            mqtt_client.subscribe(config_topic, qos=1)
            mqtt_client.subscribe("/provision/response", qos=1)

        except Exception as e:
            logger.exception(
                e,
                label="could not subscribe to config topic",
                config=config,
            )
            raise e

        logger.info(f"subscribed to topic {config_topic}")
        logger.info(f"subscribed to topic /provision/response")

        # this queue is necessary because paho-mqtt does not support
        # a function that answers the question "has this message id
        # been delivered successfully?"
        current_records: dict[int, paho.mqtt.client.MQTTMessageInfo] = {}

        # -----------------------------------------------------------------

        def _publish_record(_record: custom_types.SQLMQTTRecord) -> None:
            if _record.content.header.mqtt_topic is None:
                raise ValueError("mqtt topic is not set in the record")

            assert mqtt_client.is_connected(), "mqtt client is not connected anymore"

            payload: list[Any] = [
                {
                    "ts": _record.content.header.ts,
                    "values": _record.content.body.dict()
                }
            ]

            message_info = mqtt_client.publish(
                topic=_record.content.header.mqtt_topic,
                payload=json.dumps(payload),
                qos=1,
            )
            current_records[_record.internal_id] = message_info
            _record.status = "in-progress"

        # -----------------------------------------------------------------
        # Provisioning the device in thingsboard if necessary
        if os.environ.get("HERMES_THINGSBOARD_ACCESS_TOKEN") is None:
            logger.info("Sending thingsboard provisioning request...", config=config)
            mqtt_client.publish(
                topic="/provision/request",
                payload=json.dumps({
                    "deviceName": os.environ.get("HERMES_DEVICE_NAME"),
                    "provisionDeviceKey": os.environ.get(
                        "HERMES_THINGSBOARD_PROVISION_DEVICE_KEY"
                    ),
                    "provisionDeviceSecret": os.environ.get(
                        "HERMES_THINGSBOARD_PROVISION_DEVICE_SECRET"
                    ),
                }),
                qos=1,
            )
            logger.info("Sent thingsboard provisioning request", config=config)
            while not quit_signal:
                time.sleep(1)
            return

        # -----------------------------------------------------------------

        last_heartbeat_timestamp: float = 0

        while not quit_signal:
            # send heartbeat message every 5 minutes
            now = time.time()
            if (now - last_heartbeat_timestamp) > 300:
                _enqueue_heartbeat_message()
                last_heartbeat_timestamp = now

            sent_record_count = 0
            resent_record_count = 0
            delivered_record_count = 0
            records_ids_to_be_removed: list[int] = []

            try:
                assert mqtt_client.is_connected(), "mqtt client is not connected"

                # -----------------------------------------------------------------
                # CHECK DELIVERY STATUS OF SENT MESSAGES

                sent_records = message_queue.get_rows_by_status("in-progress")

                for record in sent_records:
                    # normal behavior
                    if record.internal_id in current_records.keys():
                        if current_records[record.internal_id].is_published():
                            delivered_record_count += 1
                            del current_records[record.internal_id]
                            records_ids_to_be_removed.append(record.internal_id)

                    # resending is required, when current_messages are
                    # lost due to restarting the program
                    else:
                        _publish_record(record)
                        resent_record_count += 1

                # remove successfully delivered messages from the active queue
                message_queue.remove_records_by_id(records_ids_to_be_removed)

                # -----------------------------------------------------------------
                # SEND PENDING MESSAGES

                max_send_count = 100
                open_sending_slots = max(
                    max_send_count - (len(sent_records) - delivered_record_count), 0
                )
                if open_sending_slots == 0:
                    logger.warning(
                        f"sending queue is full ({max_send_count} "
                        + "items not processed by broker yet)"
                    )

                records_to_be_sent = message_queue.get_rows_by_status(
                    "pending", limit=open_sending_slots
                )
                if len(records_to_be_sent) > 0:
                    records_to_be_sent = message_queue.get_rows_by_status(
                        "pending", limit=open_sending_slots
                    )
                    for record in records_to_be_sent:
                        _publish_record(record)
                        sent_record_count += 1
                    message_queue.update_records(records_to_be_sent)

                time.sleep(3)

            except Exception as e:
                logger.exception(e, label="sending loop has stopped", config=config)
                mqtt_connection.teardown()
                raise e

            if end_after_one_loop:
                break

    @staticmethod
    def get_config_message() -> Optional[custom_types.MQTTConfigurationRequest]:
        new_config_messages: list[custom_types.MQTTConfigurationRequest] = []
        while True:
            try:
                new_config_messages.append(MQTTAgent.config_request_queue.get_nowait())
            except queue.Empty:
                break

        if len(new_config_messages) == 0:
            return None

        return max(new_config_messages, key=lambda cm: cm.revision)

    @staticmethod
    def check_errors() -> None:
        """Checks whether the loop processes is still running. Possibly
        raises an `MQTTAgent.CommunicationOutage` exception."""
        if MQTTAgent.communication_loop_process is not None:
            if not MQTTAgent.communication_loop_process.is_alive():
                MQTTAgent.communication_loop_process = None
                raise MQTTAgent.CommunicationOutage(
                    "communication loop process is not running"
                )

    @staticmethod
    def __on_mqtt_message(
        config_request_queue: queue.Queue[custom_types.MQTTConfigurationRequest],
        quit_now: Callable[[], None],
    ) -> Callable[[paho.mqtt.client.Client, Any, paho.mqtt.client.MQTTMessage], None]:
        logger = utils.Logger(origin="message-communication", print_to_console=os.environ.get("HERMES_MODE") == "simulate")

        def _f(
            _client: paho.mqtt.client.Client,
            _userdata: Any,
            msg: paho.mqtt.client.MQTTMessage,
        ) -> None:
            # skip messages that are not coming from a config topic
            if "configurations" in msg.topic:
                logger.info(f"received message on config topic: {msg.payload.decode()}")
                try:
                    config_request_queue.put(
                        custom_types.MQTTConfigurationRequest(
                            **json.loads(msg.payload.decode())
                        )
                    )
                    logger.debug(f"put config message into the message queue")
                except (json.JSONDecodeError, pydantic.ValidationError):
                    logger.warning(f"could not decode message payload on message: {msg}")
            elif "/provision/response" in msg.topic:
                thingsboard_response = json.loads(msg.payload.decode())
                if not thingsboard_response["status"].lower() == "success":
                    logger.error(f"failed to provision device in thingsboard: {thingsboard_response}")
                    return quit_now()

                access_token = thingsboard_response["credentialsValue"]
                logger.info(f"received access token from thingsboard.")
                os.environ["HERMES_THINGSBOARD_ACCESS_TOKEN"] = access_token
                dotenv_data = []
                with open(DOTENV_PATH) as env_file:
                    dotenv_data += env_file.readlines()
                    dotenv_data.append(f"\nHERMES_THINGSBOARD_ACCESS_TOKEN={access_token}\n")
                with open(DOTENV_PATH, "w") as env_file:
                    env_file.writelines(''.join(dotenv_data))
                logger.info(f"added access token to .env file.")
                return quit_now()

            else:
                logger.warning(f"received message on unknown topic: {msg.topic} with payload: {msg.payload.decode()}")

        return _f
