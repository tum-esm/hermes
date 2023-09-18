import json
import queue
import signal
import time
from typing import Any, Callable, Optional
import pydantic
import paho.mqtt.client
import multiprocessing
import multiprocessing.synchronize
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
        """start the the communication loop in a separate process"""

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
        # TOOO: finish sentence
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
        logger = utils.Logger(origin="message-communication")
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
        def _enqueue_heartbeat_message() -> None:
            message_queue.enqueue_message(
                config,
                custom_types.MQTTHeartbeatMessageBody(
                    revision=config.revision, timestamp=time.time(), success=True
                ),
            )

        # tear down connection on program termination
        def _graceful_teardown(*args: Any) -> None:
            utils.set_alarm(10, "graceful teardown")

            logger.info("starting graceful shutdown")
            mqtt_connection.teardown()
            logger.info("finished graceful shutdown")
            exit(0)

        signal.signal(signal.SIGINT, _graceful_teardown)
        signal.signal(signal.SIGTERM, _graceful_teardown)
        logger.info("established graceful teardown hook")

        try:
            # TODO: finish changing topics to new structure and check other files
            config_topic = (
                f"{mqtt_config.mqtt_base_topic}configurations"
                + f"/{mqtt_config.station_identifier}"
            )
            mqtt_client.on_message = MQTTAgent.__on_config_message(config_request_queue)
            mqtt_client.subscribe(config_topic, qos=1)
        except Exception as e:
            logger.exception(
                e,
                label="could not subscribe to config topic",
                config=config,
            )
            raise e

        logger.info(f"subscribed to topic {config_topic}")

        # this queue is necessary because paho-mqtt does not support
        # a function that answers the question "has this message id
        # been delivered successfully?"
        current_records: dict[int, paho.mqtt.client.MQTTMessageInfo] = {}

        # -----------------------------------------------------------------

        def _publish_record(record: custom_types.SQLMQTTRecord) -> None:
            record.content.header.mqtt_topic = mqtt_config.mqtt_base_topic

            # TODO: finish changing topics to new structure and check other files
            record.content.header.mqtt_topic += {
                "logs": "logs/",
                "measurements": "measurements/",
                "acknowledgments": "acknowledgments/",
            }[record.content.variant]

            record.content.header.mqtt_topic += mqtt_config.station_identifier
            assert mqtt_client.is_connected(), "mqtt client is not connected anymore"

            payload: dict[str, list[Any]]
            if record.content.variant == "logs":
                message_body = record.content.body.dict()
                if len(message_body["details"]) == 0:
                    del message_body["details"]
                payload = {"logs": [message_body]}
            elif record.content.variant == "measurements":
                payload = {"measurements": [record.content.body.dict()]}
            else:
                payload = {"acknowledgments": [record.content.body.dict()]}

            message_info = mqtt_client.publish(
                topic=record.content.header.mqtt_topic,
                payload=json.dumps(payload),
                qos=1,
            )
            current_records[record.internal_id] = message_info
            record.status = "in-progress"

        # -----------------------------------------------------------------

        last_hearbeat_timestamp: float = 0

        while True:
            # send heartbeat message every 5 minutes
            now = time.time()
            if (now - last_hearbeat_timestamp) > 300:
                _enqueue_heartbeat_message()
                last_hearbeat_timestamp = now

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

                MAX_SEND_COUNT = 100
                OPEN_SENDING_SLOTS = max(
                    MAX_SEND_COUNT - (len(sent_records) - delivered_record_count), 0
                )
                if OPEN_SENDING_SLOTS == 0:
                    logger.warning(
                        f"sending queue is full ({MAX_SEND_COUNT} "
                        + "items not processed by broker yet)"
                    )

                records_to_be_sent = message_queue.get_rows_by_status(
                    "pending", limit=OPEN_SENDING_SLOTS
                )
                if len(records_to_be_sent) > 0:
                    records_to_be_sent = message_queue.get_rows_by_status(
                        "pending", limit=OPEN_SENDING_SLOTS
                    )
                    for record in records_to_be_sent:
                        _publish_record(record)
                        sent_record_count += 1
                    message_queue.update_records(records_to_be_sent)

                # -----------------------------------------------------------------

                if any([sent_record_count, resent_record_count, delivered_record_count]):
                    if config.verbose_logging:
                        logger.info(
                            f"{sent_record_count}/{resent_record_count}/{delivered_record_count} "
                            + "messages have been sent/resent/delivered"
                        )
                        logger.debug(
                            f"sending queue has {OPEN_SENDING_SLOTS -  len(records_to_be_sent)} more slot(s)"
                        )

                time.sleep(3)

            # TODO: Add exception for the MQTT connected assertion and trigger
            # a script that (re)nitialized the LTE head driver. Maybe add a 
            # check for disconnected since > x hours
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
                raise MQTTAgent.CommunicationOutage("communication loop process is not running")

    @staticmethod
    def __on_config_message(
        config_request_queue: queue.Queue[custom_types.MQTTConfigurationRequest],
    ) -> Callable[[paho.mqtt.client.Client, Any, paho.mqtt.client.MQTTMessage], None]:
        logger = utils.Logger(origin="message-communication")

        def _f(
            client: paho.mqtt.client.Client,
            userdata: Any,
            msg: paho.mqtt.client.MQTTMessage,
        ) -> None:
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

        return _f
