import os
from os.path import dirname
from typing import Any, Literal
import psycopg
from src import custom_types

PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))


class SQLQueries:
    @staticmethod
    def _run_sql_query(
        config: custom_types.Config,
        filename: Literal[
            "used_sensor_software",
            "select_all_sensors",
            "select_sensor_measurements",
        ],
        replacements: dict[str, str] = {},
    ) -> list[Any]:
        with open(os.path.join(PROJECT_DIR, "src", "queries", f"{filename}.sql")) as f:
            sql_string = f.read()

        # replace things like %SENSOR_ID% in the sql string
        for k, v in replacements.items():
            sql_string = sql_string.replace(f"%{k}%", v)

        with psycopg.connect(
            "postgresql://"
            + f"{config.database.user}:{config.database.password}"
            + f"@{config.database.host}:{config.database.port}/"
            + f"{config.database.db_name}"
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_string)
                return cursor.fetchall()

    @staticmethod
    def fetch_sensor(config: custom_types.Config) -> list[custom_types.Sensor]:
        return [
            custom_types.Sensor(sensor_name=r[0], sensor_identifier=str(r[1]))
            for r in SQLQueries._run_sql_query(config, "select_all_sensors")
        ]

    @staticmethod
    def fetch_sensor_code_version_activity(
        config: custom_types.Config,
    ) -> list[custom_types.SensorCodeVersionActivity]:
        return [
            custom_types.SensorCodeVersionActivity(
                sensor_name=r[0],
                code_version=r[1],
                first_measurement_timestamp=r[2],
                last_measurement_timestamp=r[3],
            )
            for r in SQLQueries._run_sql_query(config, "used_sensor_software")
        ]

    @staticmethod
    def fetch_sensor_measurements(
        config: custom_types.Config,
        sensor_id: str,
    ) -> list[Any]:
        return SQLQueries._run_sql_query(
            config,
            "select_sensor_measurements",
            replacements={"SENSOR_ID": sensor_id},
        )
