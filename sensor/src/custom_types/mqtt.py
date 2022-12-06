from typing import Literal
from pydantic import BaseModel, validator

from .validators import validate_int, validate_str, validate_float
from .sensor_answers import CO2SensorData

# meta data to deal with message queue
class MQTTMessageHeader(BaseModel):
    identifier: int
    status: Literal["pending", "sent", "failed", "successful"]
    revision: int
    issue_timestamp: float  # 01.01.2022 - 19.01.2038 allowed (4 byte integer)
    success_timestamp: float  # 01.01.2022 - 19.01.2038 allowed (4 byte integer)

    # validators
    _val_identifier = validator("identifier", pre=True, allow_reuse=True)(
        validate_int(minimum=0),
    )
    _val_status = validator("status", pre=True, allow_reuse=True)(
        validate_str(allowed=["pending", "sent", "failed", "successful"]),
    )
    _val_revision = validator("revision", pre=True, allow_reuse=True)(
        validate_int(minimum=0, maximum=2_147_483_648),
    )
    _val_issue_timestamp = validator("issue_timestamp", pre=True, allow_reuse=True)(
        validate_float(minimum=1_640_991_600, maximum=2_147_483_648),
    )
    _val_success_timestamp = validator("success_timestamp", pre=True, allow_reuse=True)(
        validate_float(minimum=1_640_991_600, maximum=2_147_483_648),
    )


# message sent to server
class MQTTStatusMessageBody(BaseModel):
    severity: Literal["info", "warning", "error"]
    subject: str
    details: str

    # validators
    _val_severity = validator("severity", pre=True, allow_reuse=True)(
        validate_str(allowed=["info", "warning", "error"]),
    )
    _val_subject = validator("subject", pre=True, allow_reuse=True)(
        validate_str(min_len=1, max_len=1024),
    )
    _val_details = validator("details", pre=True, allow_reuse=True)(
        validate_str(min_len=1, max_len=1024),
    )


# message sent to server
class MQTTMeasurementMessageBody(BaseModel):
    value: CO2SensorData


# elements in message queue
class MQTTStatusMessage(BaseModel):
    header: MQTTMessageHeader
    body: MQTTStatusMessageBody


# elements in message queue
class MQTTMeasurementMessage(BaseModel):
    header: MQTTMessageHeader
    body: MQTTMeasurementMessageBody


# TODO: implement bundled sending of message
