from typing import Literal, Optional, Union
import pydantic

from .sensor_answers import (
    MeasurementProcedureData,
    CO2SensorData,
    AirSensorData,
    CalibrationProcedureData,
    SystemData,
    WindSensorData,
    HeatedEnclosureData,
)

# -----------------------------------------------------------------------------
# MQTT Config (read from env variables)


class MQTTConfig(pydantic.BaseModel):
    """fixed params loaded from the environment"""

    station_identifier: str = pydantic.Field(..., min_length=3, max_length=256)
    mqtt_url: str = pydantic.Field(..., min_length=3, max_length=256)
    mqtt_port: int = pydantic.Field(..., ge=1, le=65535)
    mqtt_username: str = pydantic.Field(..., min_length=4, max_length=256)
    mqtt_password: str = pydantic.Field(..., min_length=4, max_length=256)
    mqtt_base_topic: str = pydantic.Field(..., max_length=256, regex=r"^([a-z0-9_-]+\/)*$")

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------
# MQTT Log Message


class MQTTLogMessageBody(pydantic.BaseModel):
    """message body which is sent to server"""

    severity: Literal["info", "warning", "error"]
    revision: int = pydantic.Field(..., ge=0)
    timestamp: float = pydantic.Field(..., ge=1_640_991_600)
    subject: str = pydantic.Field(..., min_length=1, max_length=256)
    details: str = pydantic.Field(..., min_length=0, max_length=16_384)

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------
# MQTT Data Message

# TODO: remove MQTTCO2Data and MQTTAirData


class MQTTMeasurementData(pydantic.BaseModel):
    variant: Literal["measurement"]
    data: MeasurementProcedureData


class MQTTCalibrationData(pydantic.BaseModel):
    variant: Literal["calibration"]
    data: CalibrationProcedureData


class MQTTCO2Data(pydantic.BaseModel):
    variant: Literal["co2"]
    data: CO2SensorData


class MQTTAirData(pydantic.BaseModel):
    variant: Literal["air"]
    data: AirSensorData


class MQTTSystemData(pydantic.BaseModel):
    variant: Literal["system"]
    data: SystemData


class MQTTWindData(pydantic.BaseModel):
    variant: Literal["wind"]
    data: WindSensorData


class MQTTEnclosureData(pydantic.BaseModel):
    variant: Literal["enclosure"]
    data: HeatedEnclosureData


class MQTTDataMessageBody(pydantic.BaseModel):
    """message body which is sent to server"""

    revision: int = pydantic.Field(..., ge=0)
    timestamp: float = pydantic.Field(..., ge=1_640_991_600)
    value: Union[
        MQTTMeasurementData,
        MQTTCO2Data,
        MQTTCalibrationData,
        MQTTAirData,
        MQTTSystemData,
        MQTTWindData,
        MQTTEnclosureData,
    ]

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------
# MQTT Heartbeat Message


class MQTTHeartbeatMessageBody(pydantic.BaseModel):
    """message body which is sent to server"""

    revision: int = pydantic.Field(..., ge=0)
    timestamp: float = pydantic.Field(..., ge=1_640_991_600)
    success: bool

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------
# MQTT Message Types: Status + Data


class MQTTMessageHeader(pydantic.BaseModel):
    mqtt_topic: Optional[str]
    sending_skipped: bool

    class Config:
        extra = "forbid"


class MQTTLogMessage(pydantic.BaseModel):
    """element in local message queue"""

    variant: Literal["logs"]
    header: MQTTMessageHeader
    body: MQTTLogMessageBody

    class Config:
        extra = "forbid"


class MQTTDataMessage(pydantic.BaseModel):
    """element in local message queue"""

    variant: Literal["data"]
    header: MQTTMessageHeader
    body: MQTTDataMessageBody

    class Config:
        extra = "forbid"


class MQTTHeartbeatMessage(pydantic.BaseModel):
    """element in local message queue"""

    variant: Literal["heartbeat"]
    header: MQTTMessageHeader
    body: MQTTHeartbeatMessageBody

    class Config:
        extra = "forbid"


MQTTMessageBody = Union[MQTTLogMessageBody, MQTTDataMessageBody, MQTTHeartbeatMessageBody]
MQTTMessage = Union[MQTTLogMessage, MQTTDataMessage, MQTTHeartbeatMessage]

# -----------------------------------------------------------------------------
# SQL


class SQLMQTTRecord(pydantic.BaseModel):
    internal_id: int
    status: Literal["pending", "in-progress"]
    content: MQTTMessage

    class Config:
        extra = "forbid"
