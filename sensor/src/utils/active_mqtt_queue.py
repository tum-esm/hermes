import json
import sqlite3
import os
from os.path import dirname
from typing import Any, Literal, Optional
from src import custom_types, utils

PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
ACTIVE_QUEUE_FILE = os.path.join(PROJECT_DIR, "data", "active-mqtt-messages.db")


class ActiveMQTTQueue:
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

    def add_row(
        self,
        message: custom_types.MQTTMessage,
        status: Literal["pending", "done"],
    ) -> None:
        """add a new pending message to the active queue"""
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

    def get_rows_by_status(
        self,
        status: Literal["pending", "in-progress", "done"],
        limit: Optional[int] = None,
    ) -> list[custom_types.SQLMQTTRecord]:
        """Used for:
        * "Which rows have to be sent out?"
        * "Which rows have been sent but not delivered"
        * "Which rows can be archived?"
        """
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

    def update_records(self, records: list[custom_types.SQLMQTTRecord]) -> None:
        """Records distinguished by `interal_id`. Used for:
        * "Message has been `sent`"
        * "Message has been `delivered`"
        """
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

    def remove_archive_messages(self) -> None:
        """delete all rows with status 'done'"""
        self.__read_sql(f"DELETE FROM QUEUE WHERE status = 'done';")
