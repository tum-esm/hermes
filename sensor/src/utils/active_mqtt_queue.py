import json
import sqlite3
import os
from os.path import dirname
from typing import Any, Literal, Optional
from src import custom_types

PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
ACTIVE_QUEUE_FILE = os.path.join(PROJECT_DIR, "data", "active-mqtt-messages.db")


class ActiveMQTTQueue:
    def __init__(self) -> None:
        self.connection = sqlite3.connect(ACTIVE_QUEUE_FILE)
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
        cursor = self.connection.cursor()
        cursor.execute(sql_statement)
        results = cursor.fetchall()
        cursor.close()
        return results

    def __write_sql(self, sql_statement: str) -> None:
        cursor = self.connection.cursor()
        cursor.execute(sql_statement)
        self.connection.commit()
        cursor.close()

    def add_row(self, message: custom_types.MQTTMessage) -> None:
        """add a new pending message to the active queue"""
        self.__write_sql(
            f"""
            INSERT INTO QUEUE (status, content)
            VALUES (
                'pending',
                '{json.dumps(message.dict())}'
            );
            """
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
            SELECT content FROM QUEUE
            WHERE status = '{status}'
            {'' if limit is None else ('LIMIT ' + str(limit))};
            """
        )
        return [
            custom_types.SQLMQTTRecord(
                internal_id=r[0],
                status=r[1],
                message=json.loads(r[2]),
            )
            for r in records
        ]

    def update_row_status_by_id(
        self,
        internal_ids: list[int],
        new_status: Literal["pending", "in-progress", "done"],
    ) -> None:
        """Used for:
        * "Message has been `sent`"
        * "Message has been `delivered`"
        """
        row_conditions = " OR ".join([f"(internal_id = {n})" for n in internal_ids])
        self.__write_sql(
            f"""
            UPDATE QUEUE
            SET status = '{new_status}'
            WHERE ({row_conditions});
            """
        )

    def remove_archive_messages(self) -> None:
        """delete all rows with status 'done'"""
        self.__read_sql(f"DELETE FROM QUEUE WHERE status = 'done';")
