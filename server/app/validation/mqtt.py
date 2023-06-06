import typing

import pydantic

import app.validation.constants as constants
import app.validation.types as types


class Acknowledgement(types._BaseModel):
    revision: types.Revision
    timestamp: types.Timestamp
    success: pydantic.StrictBool  # Was the configuration processed successfully?


class AcknowledgementsMessage(types._BaseModel):
    # TODO: Rename to acknowledgements on refactor
    heartbeats: pydantic.conlist(item_type=Acknowledgement, min_items=1)


class Log(types._BaseModel):
    severity: typing.Literal["info", "warning", "error"]
    subject: pydantic.StrictStr
    revision: types.Revision
    timestamp: types.Timestamp
    details: pydantic.StrictStr | None = None

    @pydantic.validator("subject")
    def trim_subject(cls, v):
        if len(v) >= constants.Limit.MEDIUM:
            return v[: constants.Limit.MEDIUM - 1]
        return v

    @pydantic.validator("details")
    def trim_details(cls, v):
        if len(v) >= constants.Limit.LARGE:
            return v[: constants.Limit.LARGE - 1]
        return v


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
