from typing import Literal, Optional, Union
import pydantic

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

class MQTTMeasurementData(pydantic.BaseModel):
    raw: float
    compensated: float
    filtered: float
    bme280_temperature: Optional[float]
    bme280_humidity: Optional[float]
    bme280_pressure: Optional[float]
    sht45_temperature: Optional[float]
    sht45_humidity: Optional[float]
    chamber_temperature: Optional[float]


class MQTTCalibrationData(pydantic.BaseModel):
    gas_bottle_id: float
    raw: float
    compensated: float
    filtered: float
    bme280_temperature: Optional[float]
    bme280_humidity: Optional[float]
    bme280_pressure: Optional[float]
    sht45_temperature: Optional[float]
    sht45_humidity: Optional[float]
    chamber_temperature: Optional[float]


class MQTTSystemData(pydantic.BaseModel):
    mainboard_temperature: Optional[float]
    cpu_temperature: Optional[float]
    enclosure_humidity: Optional[float]
    enclosure_pressure: Optional[float]
    disk_usage: float
    cpu_usage: float
    memory_usage: float


class MQTTWindData(pydantic.BaseModel):
    direction_min: float
    direction_avg: float
    direction_max: float
    speed_min: float
    speed_avg: float
    speed_max: float
    last_update_time: float


class MQTTMeasurementMessageBody(pydantic.BaseModel):
    """message body which is sent to server"""

    revision: int = pydantic.Field(..., ge=0)
    timestamp: float = pydantic.Field(..., ge=1_640_991_600)
    value: Union[
        MQTTMeasurementData,
        MQTTCalibrationData,
        MQTTSystemData,
        MQTTWindData,
    ]

    class Config:
        extra = "forbid"


# -----------------------------------------------------------------------------
# MQTT Heartbeat Message


class MQTTAcknowledgmentMessageBody(pydantic.BaseModel):
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
    body: MQTTMeasurementMessageBody

    class Config:
        extra = "forbid"


class MQTTHeartbeatMessage(pydantic.BaseModel):
    """element in local message queue"""

    variant: Literal["heartbeat"]
    header: MQTTMessageHeader
    body: MQTTAcknowledgmentMessageBody

    class Config:
        extra = "forbid"


MQTTMessageBody = Union[MQTTLogMessageBody, MQTTMeasurementMessageBody, MQTTAcknowledgmentMessageBody]
MQTTMessage = Union[MQTTLogMessage, MQTTDataMessage, MQTTHeartbeatMessage]

# -----------------------------------------------------------------------------
# SQL


class SQLMQTTRecord(pydantic.BaseModel):
    internal_id: int
    status: Literal["pending", "in-progress"]
    content: MQTTMessage

    class Config:
        extra = "forbid"
