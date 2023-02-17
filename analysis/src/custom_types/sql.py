from datetime import datetime
from pydantic import BaseModel


class Sensor(BaseModel):
    """content of field `config.sensors` in file `config.json`"""

    sensor_name: str
    sensor_identifier: str


class SensorCodeVersionActivity(BaseModel):
    """content of field `config.sensors` in file `config.json`"""

    sensor_name: str
    code_version: str
    first_measurement_timestamp: datetime
    last_measurement_timestamp: datetime
