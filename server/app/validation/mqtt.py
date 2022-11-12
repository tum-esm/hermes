import pydantic

import app.validation.constants as constants


SensorIdentifier = pydantic.constr(
    strict=True, regex=constants.Pattern.SENSOR_IDENTIFIER
)
ValueIdentifier = pydantic.constr(strict=True, regex=constants.Pattern.VALUE_IDENTIFIER)
Timestamp = pydantic.confloat(strict=True, ge=0, lt=constants.Length.MAXINT4)


class _BaseModel(pydantic.BaseModel):
    class Config:
        max_anystr_length = constants.Length.LARGE
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
        max_items=constants.Length.MEDIUM - 1,
    )
