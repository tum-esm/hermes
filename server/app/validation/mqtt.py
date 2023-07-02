import typing

import pydantic

import app.validation.constants as constants
import app.validation.types as types


class Acknowledgement(types.Model):
    timestamp: types.Timestamp
    revision: types.Revision
    success: bool  # Records if the configuration was processed successfully


class AcknowledgementsMessage(types.Model):
    values: pydantic.conlist(item_type=Acknowledgement, min_length=1) = pydantic.Field(
        ..., alias="heartbeats"
    )


class Log(types.Model):
    timestamp: types.Timestamp
    revision: types.Revision | None = None
    severity: typing.Literal["info", "warning", "error"]
    subject: str
    details: str | None = None

    @pydantic.validator("subject")
    def trim_subject(cls, v):
        return v[: constants.Limit.MEDIUM]

    @pydantic.validator("details")
    def trim_details(cls, v):
        return v[: constants.Limit.LARGE]


class LogsMessage(types.Model):
    values: pydantic.conlist(item_type=Log, min_length=1) = pydantic.Field(
        ..., alias="log_messages"
    )


class Measurement(types.Model):
    timestamp: types.Timestamp
    revision: types.Revision | None = None
    value: types.Measurement


class MeasurementsMessage(types.Model):
    values: pydantic.conlist(item_type=Measurement, min_length=1) = pydantic.Field(
        ..., alias="measurements"
    )
