from typing import Literal
from pydantic import BaseModel
from .sensor_answers import CO2SensorData


class MQTTMessageHeader(BaseModel):
    identifier: int
    status: Literal["pending", "sent", "failed", "successful"]
    revision: int
    issue_timestamp: float
    success_timestamp: float

    # TODO: Add validation


class MQTTStatusMessageBody(BaseModel):
    severity: Literal["info", "warning", "error"]
    subject: str
    details: str

    # TODO: Add validation


class MQTTStatusMessage(BaseModel):
    header: MQTTMessageHeader
    body: MQTTStatusMessageBody


class MQTTMeasurementMessageBody(BaseModel):
    value: CO2SensorData

    # TODO: Add validation


class MQTTMeasurementMessage(BaseModel):
    header: MQTTMessageHeader
    body: MQTTMeasurementMessageBody
