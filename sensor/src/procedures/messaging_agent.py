import json
import queue
import signal
import time
from typing import Any, Callable, Optional
import paho.mqtt.client
import multiprocessing
import multiprocessing.synchronize
from src import custom_types, utils


class MessagingAgent:
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
        if MessagingAgent.communication_loop_process is None:
            if config.active_components.mqtt_communication:
                new_process = multiprocessing.Process(
                    target=MessagingAgent.communication_loop,
                    args=(
                        config,
                        MessagingAgent.config_request_queue,
                    ),
                    daemon=True,
                )
                new_process.start()
                MessagingAgent.communication_loop_process = new_process

        # wait until messaging agent has
        time.sleep(2)

    @staticmethod
    def deinit() -> None:
        """stop the communication loop process"""

        if MessagingAgent.communication_loop_process is not None:
            MessagingAgent.communication_loop_process.terminate()
            MessagingAgent.communication_loop_process.join()
            MessagingAgent.communication_loop_process = None

    @staticmethod
    def communication_loop(
        config: custom_types.Config,
        config_request_queue: queue.Queue[custom_types.MQTTConfigurationRequest],
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
            active_mqtt_queue = utils.ActiveMQTTQueue()
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

        # tear down connection on program termination
        def graceful_teardown(*args: Any) -> None:
            def _raise_teardown_timeout(*args: Any) -> None:
                logger.info("graceful teardown took too long")
                raise TimeoutError("teardown took too long")

            signal.signal(signal.SIGALRM, _raise_teardown_timeout)
            signal.alarm(10)

            logger.info("starting graceful shutdown")
            mqtt_connection.teardown()
            logger.info("finished graceful shutdown")
            exit(0)

        signal.signal(signal.SIGINT, graceful_teardown)
        signal.signal(signal.SIGTERM, graceful_teardown)
        logger.info("established graceful teardown hook")

        try:
            config_topic = (
                f"{mqtt_config.mqtt_base_topic}configurations"
                + f"/{mqtt_config.station_identifier}"
            )
            mqtt_client.on_message = MessagingAgent.__on_config_message(
                config_request_queue
            )
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
            record.content.header.mqtt_topic += (
                "log-messages/" if record.content.variant == "logs" else "measurements/"
            )
            record.content.header.mqtt_topic += mqtt_config.station_identifier
            assert mqtt_client.is_connected(), "mqtt client is not connected anymore"

            payload: dict[str, list[Any]]
            if record.content.variant == "logs":
                message_body = record.content.body.dict()
                if len(message_body["details"]) == 0:
                    del message_body["details"]
                payload = {"log_messages": [message_body]}
            else:
                payload = {"measurements": [record.content.body.dict()]}

            message_info = mqtt_client.publish(
                topic=record.content.header.mqtt_topic,
                payload=json.dumps(payload),
                qos=1,
            )
            current_records[record.internal_id] = message_info
            record.status = "in-progress"

        # -----------------------------------------------------------------

        while True:
            sent_record_count = 0
            resent_record_count = 0
            delivered_record_count = 0
            records_ids_to_be_removed: list[int] = []

            try:
                assert mqtt_client.is_connected(), "mqtt client is not connected"

                # -----------------------------------------------------------------
                # CHECK DELIVERY STATUS OF SENT MESSAGES

                sent_records = active_mqtt_queue.get_rows_by_status("in-progress")

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
                active_mqtt_queue.remove_records_by_id(records_ids_to_be_removed)

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

                records_to_be_sent = active_mqtt_queue.get_rows_by_status(
                    "pending", limit=OPEN_SENDING_SLOTS
                )
                if len(records_to_be_sent) > 0:
                    records_to_be_sent = active_mqtt_queue.get_rows_by_status(
                        "pending", limit=OPEN_SENDING_SLOTS
                    )
                    for record in records_to_be_sent:
                        _publish_record(record)
                        sent_record_count += 1
                    active_mqtt_queue.update_records(records_to_be_sent)

                # -----------------------------------------------------------------

                if any(
                    [sent_record_count, resent_record_count, delivered_record_count]
                ):
                    if config.verbose_logging:
                        logger.info(
                            f"{sent_record_count}/{resent_record_count}/{delivered_record_count} "
                            + "messages have been sent/resent/delivered"
                        )
                        logger.debug(
                            f"sending queue has {OPEN_SENDING_SLOTS -  len(records_to_be_sent)} more slot(s)"
                        )

                time.sleep(3)

            except Exception as e:
                logger.exception(e, label="sending loop has stopped", config=config)
                mqtt_connection.teardown()
                raise e

    @staticmethod
    def get_config_message() -> Optional[custom_types.MQTTConfigurationRequest]:
        new_config_messages: list[custom_types.MQTTConfigurationRequest] = []
        while True:
            try:
                new_config_messages.append(
                    MessagingAgent.config_request_queue.get_nowait()
                )
            except queue.Empty:
                break

        if len(new_config_messages) == 0:
            return None

        return max(new_config_messages, key=lambda cm: cm.revision)

    @staticmethod
    def check_errors() -> None:
        """Checks whether the loop processes is still running. Possibly
        raises an `MessagingAgent.CommunicationOutage` exception."""

        if MessagingAgent.communication_loop_process is not None:
            if not MessagingAgent.communication_loop_process.is_alive():
                raise MessagingAgent.CommunicationOutage(
                    "communication loop process is not running"
                )

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
            except json.JSONDecodeError:
                logger.warning(f"could not decode message payload on message: {msg}")

        return _f
