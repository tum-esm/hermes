from datetime import datetime
from typing import Literal, Optional, Union
from pydantic import BaseModel

from .mqtt import (
    MQTTCO2Data,
    MQTTCalibrationData,
    MQTTAirData,
    MQTTSystemData,
    MQTTWindData,
    MQTTEnclosureData,
)


class Sensor(BaseModel):
    sensor_name: str
    sensor_identifier: str


class SensorCodeVersionActivity(BaseModel):
    sensor_name: str
    code_version: str
    first_timestamp: datetime
    last_timestamp: datetime


class SensorMeasurement(BaseModel):
    timestamp: datetime
    value: Union[
        MQTTCO2Data,
        MQTTCalibrationData,
        MQTTAirData,
        MQTTSystemData,
        MQTTWindData,
        MQTTEnclosureData,
    ]


class SensorLog(BaseModel):
    severity: Literal["info", "warning", "error"]
    timestamp: datetime
    subject: str
