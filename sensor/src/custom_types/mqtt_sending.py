from typing import Literal, Optional, Union
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
# MQTT Config (read from env variables)


class MQTTConfig(BaseModel):
    """fixed params loaded from the environment"""

    station_identifier: str
    mqtt_url: str
    mqtt_port: str
    mqtt_username: str
    mqtt_password: str
    mqtt_base_topic: str

    # validators
    _val_station_identifier = validator(
        "station_identifier", pre=True, allow_reuse=True
    )(
        validate_str(min_len=3, max_len=256),
    )
    _val_mqtt_url = validator("mqtt_url", pre=True, allow_reuse=True)(
        validate_str(min_len=3, max_len=256),
    )
    _val_mqtt_port = validator("mqtt_port", pre=True, allow_reuse=True)(
        validate_str(is_numeric=True),
    )
    _val_mqtt_username = validator("mqtt_username", pre=True, allow_reuse=True)(
        validate_str(min_len=4, max_len=256),
    )
    _val_mqtt_password = validator("mqtt_password", pre=True, allow_reuse=True)(
        validate_str(min_len=4, max_len=256),
    )
    _val_mqtt_base_topic = validator("mqtt_base_topic", pre=True, allow_reuse=True)(
        validate_str(max_len=256, regex=r"^([a-z0-9_-]+\/)*$"),
    )

    class Config:
        extra = "forbid"


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


# -----------------------------------------------------------------------------
# MQTT Message Types: Status + Data


class MQTTMessageHeader(BaseModel):
    mqtt_topic: Optional[str]
    sending_skipped: bool

    _val_mqtt_topic = validator("mqtt_topic", pre=True, allow_reuse=True)(
        validate_str(nullable=True),
    )
    _val_sending_skipped = validator("sending_skipped", pre=True, allow_reuse=True)(
        validate_bool(),
    )

    class Config:
        extra = "forbid"


class MQTTLogMessage(BaseModel):
    """element in local message queue"""

    variant: Literal["logs"]
    header: MQTTMessageHeader
    body: MQTTLogMessageBody

    # validators
    _val_variant = validator("variant", pre=True, allow_reuse=True)(
        validate_str(allowed=["logs"]),
    )

    class Config:
        extra = "forbid"


class MQTTDataMessage(BaseModel):
    """element in local message queue"""

    variant: Literal["data"]
    header: MQTTMessageHeader
    body: MQTTDataMessageBody

    # validators
    _val_variant = validator("variant", pre=True, allow_reuse=True)(
        validate_str(allowed=["data"]),
    )

    class Config:
        extra = "forbid"


MQTTMessageBody = Union[MQTTLogMessageBody, MQTTDataMessageBody]
MQTTMessage = Union[MQTTLogMessage, MQTTDataMessage]

# -----------------------------------------------------------------------------
# SQL


class SQLMQTTRecord(BaseModel):
    internal_id: int
    status: Literal["pending", "in-progress", "done"]
    content: MQTTMessage

    _val_internal_id = validator("internal_id", pre=True, allow_reuse=True)(
        validate_int(),
    )
    _val_status = validator("status", pre=True, allow_reuse=True)(
        validate_str(allowed=["pending", "in-progress", "done"]),
    )

    class Config:
        extra = "forbid"
