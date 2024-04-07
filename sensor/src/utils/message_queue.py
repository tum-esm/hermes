import json
import os
import sqlite3
import time
from datetime import datetime
from os.path import dirname
from typing import Any, Literal, Optional

import filelock

from src import custom_types

PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
ACTIVE_QUEUE_FILE = os.path.join(PROJECT_DIR, "data", "active-mqtt-messages.db")
QUEUE_ARCHIVE_DIR = os.path.join(PROJECT_DIR, "data", "archive")
ARCHIVE_FILELOCK_PATH = os.path.join(PROJECT_DIR, "data", "archive.lock")


class MessageQueue:
    def __init__(self) -> None:
        self.connection = sqlite3.connect(ACTIVE_QUEUE_FILE, check_same_thread=True)
        self.__write_sql(
            """
                CREATE TABLE IF NOT EXISTS QUEUE (
                    internal_id INTEGER PRIMARY KEY,
                    status text,
                    content text
                );
            """
        )
        self.filelock = filelock.FileLock(ARCHIVE_FILELOCK_PATH, timeout=3)

    def __read_sql(self, sql_statement: str) -> list[Any]:
        with self.connection:
            results = list(self.connection.execute(sql_statement).fetchall())
        return results

    def __write_sql(
        self,
        sql_statement: str,
        parameters: Optional[list[tuple]] = None,  # type: ignore
    ) -> None:
        with self.connection:
            if parameters is not None:
                self.connection.executemany(sql_statement, parameters)
            else:
                self.connection.execute(sql_statement)

    def __add_row(
        self,
        message: custom_types.MQTTMessage,
        status: Literal["pending", "done"],
    ) -> None:
        """add a new message to the active queue db and message archive"""

        # add pending messages to active queue
        if status == "pending":
            self.__write_sql(
                f"""
                    INSERT INTO QUEUE (status, content)
                    VALUES (
                        ?,
                        ?
                    );
                """,
                parameters=[(status, json.dumps(message.dict()))],
            )

        # write all messages to archive immediately
        date_string = datetime.now().strftime("%Y-%m-%d")
        with self.filelock:
            with open(
                os.path.join(
                    QUEUE_ARCHIVE_DIR,
                    f"mqtt-messages-{date_string}.json",
                ),
                "a",
            ) as f:
                f.write(json.dumps(message.dict()) + "\n")

    def get_rows_by_status(
        self,
        status: Literal["pending", "in-progress"],
        limit: Optional[int] = None,
    ) -> list[custom_types.SQLMQTTRecord]:
        """Used for:
        * "Which rows have to be sent out?"
        * "Which rows have been sent but not delivered"
        * "Which rows can be archived?" """

        records = self.__read_sql(
            f"""
            SELECT internal_id, status, content FROM QUEUE
            WHERE status = '{status}'
            {'' if limit is None else ('LIMIT ' + str(limit))};
            """
        )
        return [
            custom_types.SQLMQTTRecord(
                **{
                    "internal_id": r[0],
                    "status": r[1],
                    "content": json.loads(r[2]),
                }
            )
            for r in records
        ]

    def get_row_count(self) -> int:
        return len(self.__read_sql("SELECT Count(internal_id) FROM QUEUE;"))

    def update_records(self, records: list[custom_types.SQLMQTTRecord]) -> None:
        """Records distinguished by `internal_id`. Used for:
        * "Message has been `sent`"
        * "Message has been `delivered`" """

        if len(records) == 0:
            return

        self.__write_sql(
            f"""
                UPDATE QUEUE SET
                    status = ?,
                    content = ?
                WHERE internal_id = ?;
            """,
            parameters=[
                (
                    r.status,
                    json.dumps(r.content.dict()),
                    r.internal_id,
                )
                for r in records
            ],
        )

    def remove_records_by_id(self, record_ids: list[int]) -> None:
        """Records distinguished by `internal_id`. Used for:
        * "Message has been `sent`"
        * "Message has been `delivered`" """

        if len(record_ids) == 0:
            return

        self.__write_sql(
            f"""
                DELETE FROM QUEUE
                WHERE internal_id = ?;
            """,
            parameters=[(rid,) for rid in record_ids],
        )

    def enqueue_message(
        self,
        config: custom_types.Config,
        message_body: custom_types.MQTTMessageBody,
        mqtt_topic: Optional[str],
    ) -> None:
        new_header = custom_types.MQTTMessageHeader(
            mqtt_topic=None,
            sending_skipped=(not config.active_components.send_messages_over_mqtt),
        )
        new_message: custom_types.MQTTMessage

        if mqtt_topic is not None:
            new_header.mqtt_topic = mqtt_topic

        if isinstance(message_body, custom_types.MQTTLogMessageBody):
            new_message = custom_types.MQTTLogMessage(
                header=new_header, body=message_body
            )
        elif isinstance(message_body, custom_types.MQTTMeasurementMessageBody):
            new_message = custom_types.MQTTMeasurementMessage(
                header=new_header, body=message_body
            )
        elif isinstance(message_body, custom_types.MQTTAcknowledgmentMessageBody):
            new_message = custom_types.MQTTAcknowledgmentMessage(
                header=new_header, body=message_body
            )
        else:
            raise ValueError(f"Unknown message type: {message_body}")

        if config.active_components.send_messages_over_mqtt:
            self.__add_row(new_message, status="pending")
        else:
            self.__add_row(new_message, status="done")

    def wait_until_queue_is_empty(self, timeout: int) -> None:
        start_time = time.time()
        while True:
            if self.get_row_count() == 0:
                break
            if (time.time() - start_time) > timeout:
                raise TimeoutError()
            time.sleep(1)
