import pydantic

import app.validation.constants as constants
from app.validation.fields import JSONValues


SensorIdentifier = pydantic.constr(
    strict=True,
    regex=constants.Pattern.SENSOR_IDENTIFIER.value,
)
ValueIdentifier = pydantic.constr(
    strict=True,
    regex=constants.Pattern.VALUE_IDENTIFIER.value,
)
# TODO what's the real max value here?
Timestamp = pydantic.confloat(strict=True, ge=0, lt=constants.Limit.MAXINT4)


class _BaseModel(pydantic.BaseModel):
    class Config:
        max_anystr_length = constants.Limit.LARGE
        extra = pydantic.Extra["forbid"]
        frozen = True


class Measurement(_BaseModel):
    timestamp: Timestamp
    # TODO Validate the values more thoroughly for min and max limits/lengths
    values: dict[ValueIdentifier, JSONValues]


class MeasurementsMessage(_BaseModel):
    sensor_identifier: SensorIdentifier
    measurements: pydantic.conlist(
        item_type=Measurement,
        min_items=1,
        max_items=constants.Limit.MEDIUM - 1,
    )
