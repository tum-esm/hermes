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
            "used_sensor_software_measurements",
            "used_sensor_software_logs",
            "select_all_sensors",
            "select_sensor_measurements",
            "select_sensor_logs",
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
            + f"{config.database.db_name}",
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
        output = [
            custom_types.SensorCodeVersionActivity(
                sensor_name=r[0],
                code_version=r[1],
                first_timestamp=r[2],
                last_timestamp=r[3],
            )
            for r in [
                *SQLQueries._run_sql_query(config, "used_sensor_software_measurements"),
                *SQLQueries._run_sql_query(config, "used_sensor_software_logs"),
            ]
        ]

        output.sort(key=lambda a: a.sensor_name + a.code_version)

        merged_outputs: list[custom_types.SensorCodeVersionActivity] = []
        for a, b in zip(output[:-1], output[1:]):
            if (a.code_version != b.code_version) or (a.sensor_name != b.sensor_name):
                merged_outputs.append(a)
            else:
                merged_outputs.append(
                    custom_types.SensorCodeVersionActivity(
                        sensor_name=a.sensor_name,
                        code_version=a.code_version,
                        first_timestamp=min(a.first_timestamp, b.first_timestamp),
                        last_timestamp=max(a.last_timestamp, b.last_timestamp),
                    )
                )

        return merged_outputs

    @staticmethod
    def fetch_sensor_measurements(
        config: custom_types.Config,
        sensor_name: str,
    ) -> list[custom_types.SensorMeasurement]:
        return [
            custom_types.SensorMeasurement(
                timestamp=r[0],
                value=r[1],
            )
            for r in SQLQueries._run_sql_query(
                config,
                "select_sensor_measurements",
                replacements={"SENSOR_NAME": sensor_name},
            )
        ]

    @staticmethod
    def fetch_sensor_logs(
        config: custom_types.Config,
        sensor_name: str,
    ) -> list[custom_types.SensorLog]:
        return [
            custom_types.SensorLog(
                timestamp=r[0],
                severity=r[1],
                subject=r[2],
            )
            for r in SQLQueries._run_sql_query(
                config,
                "select_sensor_logs",
                replacements={"SENSOR_NAME": sensor_name},
            )
        ]
