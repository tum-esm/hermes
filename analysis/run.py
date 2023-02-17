from datetime import datetime
import os
from os.path import dirname
from typing import Any, Literal
import psycopg
from pydantic import BaseModel
from src import custom_types, utils

PROJECT_DIR = dirname(os.path.abspath(__file__))


def run_query(
    config: custom_types.Config,
    filename: Literal["used_sensor_software.sql", "select_all_sensors.sql"],
) -> list[Any]:
    with open(os.path.join(PROJECT_DIR, "src", "queries", filename)) as f:
        sql_string = f.read()

    print(sql_string)

    with psycopg.connect(
        "postgresql://"
        + f"{config.database.user}:{config.database.password}"
        + f"@{config.database.host}:{config.database.port}/"
        + f"{config.database.db_name}"
    ) as connection:
        print("connection established")
        with connection.cursor() as cursor:
            cursor.execute(sql_string)
            return cursor.fetchall()


class Sensor(BaseModel):
    """content of field `config.sensors` in file `config.json`"""

    sensor_name: str
    sensor_identifier: str


def fetch_sensor(config: custom_types.Config) -> list[Sensor]:
    return [
        Sensor(sensor_name=r[0], sensor_identifier=str(r[1]))
        for r in run_query(config, "select_all_sensors.sql")
    ]


class SensorCodeVersionActivity(BaseModel):
    """content of field `config.sensors` in file `config.json`"""

    sensor_name: str
    code_version: str
    first_measurement_timestamp: datetime
    last_measurement_timestamp: datetime


def fetch_sensor_code_version_activity(
    config: custom_types.Config,
) -> list[SensorCodeVersionActivity]:
    return [
        SensorCodeVersionActivity(
            sensor_name=r[0],
            code_version=r[1],
            first_measurement_timestamp=r[2],
            last_measurement_timestamp=r[3],
        )
        for r in run_query(config, "used_sensor_software.sql")
    ]


if __name__ == "__main__":
    config = utils.ConfigInterface.read()
    print(fetch_sensor(config))
    print(fetch_sensor_code_version_activity(config))
