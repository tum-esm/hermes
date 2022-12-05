import typing

import pydantic

import app.validation.constants as constants
from app.validation.fields import JSONValues


ValueIdentifier = pydantic.constr(
    strict=True,
    regex=constants.Pattern.VALUE_IDENTIFIER.value,
)
Revision = pydantic.conint(strict=True, ge=0, lt=constants.Limit.MAXINT4)
# TODO what are the real min/max values here? How do we handle overflow?
# During validation somehow, or by handling the database error?
Timestamp = pydantic.confloat(strict=True, ge=0, lt=constants.Limit.MAXINT4)


class _BaseModel(pydantic.BaseModel):
    class Config:
        max_anystr_length = constants.Limit.LARGE
        extra = pydantic.Extra["forbid"]
        frozen = True


class Heartbeat(_BaseModel):
    revision: Revision
    timestamp: Timestamp
    success: bool  # Did the sensor successfully process the configuration?


class HeartbeatsMessage(_BaseModel):
    heartbeats: pydantic.conlist(
        item_type=Heartbeat, min_items=1, max_items=constants.Limit.MEDIUM - 1
    )


class Status(_BaseModel):
    severity: typing.Literal["info", "warning", "error"]
    revision: Revision
    timestamp: Timestamp
    subject: pydantic.constr(
        strict=True, min_length=1, max_length=constants.Limit.LARGE - 1
    )
    details: pydantic.constr(
        strict=True, min_length=1, max_length=constants.Limit.LARGE - 1
    ) | None = None


class StatusesMessage(_BaseModel):
    statuses: pydantic.conlist(
        item_type=Status, min_items=1, max_items=constants.Limit.MEDIUM - 1
    )


class Measurement(_BaseModel):
    revision: Revision
    timestamp: Timestamp
    # TODO Validate the values more thoroughly for min and max limits/lengths
    value: dict[ValueIdentifier, JSONValues]


class MeasurementsMessage(_BaseModel):
    measurements: pydantic.conlist(
        item_type=Measurement, min_items=1, max_items=constants.Limit.MEDIUM - 1
    )
