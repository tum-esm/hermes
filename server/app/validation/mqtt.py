import typing

import pydantic

import app.validation.constants as constants
import app.validation.types as types


class Heartbeat(types._BaseModel):
    revision: types.Revision
    timestamp: types.Timestamp
    success: bool  # Did the sensor successfully process the configuration?


class HeartbeatsMessage(types._BaseModel):
    heartbeats: pydantic.conlist(
        item_type=Heartbeat, min_items=1, max_items=constants.Limit.MEDIUM - 1
    )


class LogMessage(types._BaseModel):
    severity: typing.Literal["info", "warning", "error"]
    revision: types.Revision
    timestamp: types.Timestamp
    # TODO Cut off the string at max length instead of rejecting it
    subject: pydantic.constr(
        strict=True, min_length=1, max_length=constants.Limit.LARGE - 1
    )
    # TODO Cut off the string at max length instead of rejecting it
    details: pydantic.constr(
        strict=True, min_length=1, max_length=constants.Limit.LARGE - 1
    ) | None = None


class LogMessagesMessage(types._BaseModel):
    log_messages: pydantic.conlist(
        item_type=LogMessage, min_items=1, max_items=constants.Limit.MEDIUM - 1
    )


class Measurement(types._BaseModel):
    revision: types.Revision
    timestamp: types.Timestamp
    value: types.Json


class MeasurementsMessage(types._BaseModel):
    measurements: pydantic.conlist(
        item_type=Measurement, min_items=1, max_items=constants.Limit.MEDIUM - 1
    )
