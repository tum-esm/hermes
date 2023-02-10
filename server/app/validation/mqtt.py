import typing

import pydantic

import app.validation.types as types


class Heartbeat(types._BaseModel):
    revision: types.Revision
    timestamp: types.Timestamp
    # Did the sensor successfully process the configuration?
    success: pydantic.StrictBool


class HeartbeatsMessage(types._BaseModel):
    heartbeats: pydantic.conlist(item_type=Heartbeat, min_items=1)


class Log(types._BaseModel):
    severity: typing.Literal["debug", "info", "warning", "error"]
    revision: types.Revision
    timestamp: types.Timestamp
    subject: pydantic.StrictStr
    details: pydantic.StrictStr | None = None


class LogsMessage(types._BaseModel):
    logs: pydantic.conlist(item_type=Log, min_items=1) = pydantic.Field(
        ..., alias="log_messages"
    )


class Measurement(types._BaseModel):
    revision: types.Revision
    timestamp: types.Timestamp
    value: types.Json


class MeasurementsMessage(types._BaseModel):
    measurements: pydantic.conlist(item_type=Measurement, min_items=1)
