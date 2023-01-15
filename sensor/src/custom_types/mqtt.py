from typing import Any, Literal, Optional, Union
from pydantic import BaseModel, validator

from .validators import validate_int, validate_str, validate_float
from .sensor_answers import CO2SensorData


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
        validate_str(min_len=8, max_len=256),
    )
    _val_mqtt_password = validator("mqtt_password", pre=True, allow_reuse=True)(
        validate_str(min_len=8, max_len=256),
    )
    _val_mqtt_base_topic = validator("mqtt_base_topic", pre=True, allow_reuse=True)(
        validate_str(min_len=1, max_len=256, regex=r"^([a-z0-9_-]+\/)*$"),
    )

    class Config:
        extra = "forbid"


class MQTTMessageHeader(BaseModel):
    """meta data for managing message queue"""

    identifier: int
    mqtt_topic: Optional[str]
    status: Literal["pending", "sent", "delivered"]
    delivery_timestamp: Optional[float]

    # validators
    _val_identifier = validator("identifier", pre=True, allow_reuse=True)(
        validate_int(minimum=0),
    )
    _val_mqtt_topic = validator("mqtt_topic", pre=True, allow_reuse=True)(
        validate_str(nullable=True),
    )
    _val_status = validator("status", pre=True, allow_reuse=True)(
        validate_str(allowed=["pending", "sent", "delivered"]),
    )
    _val_delivery_timestamp = validator(
        "delivery_timestamp", pre=True, allow_reuse=True
    )(
        validate_float(minimum=1_640_991_600, maximum=2_147_483_648, nullable=True),
    )

    class Config:
        extra = "forbid"


class MQTTStatusMessageBody(BaseModel):
    """message body which is sent to server"""

    severity: Literal["info", "warning", "error"]
    revision: int
    timestamp: float
    subject: str
    details: str

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


class MQTTMeasurementMessageBody(BaseModel):
    """message body which is sent to server"""

    revision: int
    timestamp: float
    value: CO2SensorData

    # validators
    _val_revision = validator("revision", pre=True, allow_reuse=True)(
        validate_int(minimum=0, maximum=2_147_483_648),
    )
    _val_timestamp = validator("timestamp", pre=True, allow_reuse=True)(
        validate_float(minimum=1_640_991_600, maximum=2_147_483_648),
    )

    class Config:
        extra = "forbid"


class MQTTStatusMessage(BaseModel):
    """element in local message queue"""

    variant: Literal["status"]
    header: MQTTMessageHeader
    body: MQTTStatusMessageBody


class MQTTMeasurementMessage(BaseModel):
    """element in local message queue"""

    variant: Literal["measurement"]
    header: MQTTMessageHeader
    body: MQTTMeasurementMessageBody


class ActiveMQTTMessageQueue(BaseModel):
    max_identifier: int
    messages: list[Union[MQTTStatusMessage, MQTTMeasurementMessage]]

    # validators
    _val_max_identifier = validator("max_identifier", pre=True, allow_reuse=True)(
        validate_int(minimum=0),
    )

    class Config:
        extra = "forbid"


class ArchivedMQTTMessageQueue(BaseModel):
    messages: list[Union[MQTTStatusMessage, MQTTMeasurementMessage]]

    class Config:
        extra = "forbid"


MQTTMessageBody = Union[MQTTStatusMessageBody, MQTTMeasurementMessageBody]
MQTTMessage = Union[MQTTStatusMessage, MQTTMeasurementMessage]


class MQTTConfigurationRequestConfig(BaseModel):
    version: str

    # validators
    _val_version = validator("version", pre=True, allow_reuse=True)(
        validate_str(min_len=5),
    )


class MQTTConfigurationRequest(BaseModel):
    """A message sent by the server requesting a station to
    update its configuration. Extra items in this mode are
    allowed for future additions."""

    revision: int
    configuration: MQTTConfigurationRequestConfig

    # validators
    _val_revision = validator("revision", pre=True, allow_reuse=True)(
        validate_int(minimum=0),
    )
