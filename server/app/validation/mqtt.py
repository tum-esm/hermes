import enum

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


class Severity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class _BaseModel(pydantic.BaseModel):
    class Config:
        max_anystr_length = constants.Limit.LARGE
        extra = pydantic.Extra["forbid"]
        frozen = True


class Status(_BaseModel):
    revision: Revision
    timestamp: Timestamp
    severity: Severity
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
    values: dict[ValueIdentifier, JSONValues]


class MeasurementsMessage(_BaseModel):
    measurements: pydantic.conlist(
        item_type=Measurement, min_items=1, max_items=constants.Limit.MEDIUM - 1
    )
