from typing import Literal, Union
from pydantic import BaseModel, validator

from .validators import validate_bool, validate_int, validate_str, validate_float
from .sensor_answers import (
    CO2SensorData,
    AirSensorData,
    CalibrationProcedureData,
    SystemData,
    WindSensorData,
    HeatedEnclosureData,
)

# -----------------------------------------------------------------------------
# MQTT Log Message


class MQTTLogMessageBody(BaseModel):
    """message body which is sent to server"""

    severity: Literal["info", "warning", "error"]
    revision: int
    timestamp: float
    subject: str
    details: str = ""

    # validators
    _val_severity = validator("severity", pre=True, allow_reuse=True)(
        validate_str(allowed=["info", "warning", "error"]),
    )
    _val_revision = validator("revision", pre=True, allow_reuse=True)(
        validate_int(minimum=0, maximum=2_147_483_648),
    )
    _val_timestamp = validator("timestamp", pre=True, allow_reuse=True)(
        validate_float(minimum=1_640_991_600, maximum=2_147_483_648),
    )
    _val_subject = validator("subject", pre=True, allow_reuse=True)(
        validate_str(min_len=1, max_len=1024),
    )
    _val_details = validator("details", pre=True, allow_reuse=True)(
        validate_str(min_len=0, max_len=1024),
    )

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------
# MQTT Data Message


class MQTTCO2Data(BaseModel):
    variant: Literal["co2"]
    data: CO2SensorData


class MQTTCalibrationData(BaseModel):
    variant: Literal["calibration"]
    data: CalibrationProcedureData


class MQTTAirData(BaseModel):
    variant: Literal["air"]
    data: AirSensorData


class MQTTSystemData(BaseModel):
    variant: Literal["system"]
    data: SystemData


class MQTTWindData(BaseModel):
    variant: Literal["wind"]
    data: WindSensorData


class MQTTEnclosureData(BaseModel):
    variant: Literal["enclosure"]
    data: HeatedEnclosureData


class MQTTDataMessageBody(BaseModel):
    """message body which is sent to server"""

    revision: int
    timestamp: float
    value: Union[
        MQTTCO2Data,
        MQTTCalibrationData,
        MQTTAirData,
        MQTTSystemData,
        MQTTWindData,
        MQTTEnclosureData,
    ]

    # validators
    _val_revision = validator("revision", pre=True, allow_reuse=True)(
        validate_int(minimum=0, maximum=2_147_483_648),
    )
    _val_timestamp = validator("timestamp", pre=True, allow_reuse=True)(
        validate_float(minimum=1_640_991_600, maximum=2_147_483_648),
    )

    class Config:
        extra = "forbid"

