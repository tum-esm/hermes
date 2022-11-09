import attrs

from app.validation.fields import (
    JSON_FIELD,
    POSITIVE_INTEGER_VALIDATOR,
    SENSOR_IDENTIFIER_VALIDATOR,
)


@attrs.frozen
class MeasurementMessage:
    sensor_identifier: str = attrs.field(validator=SENSOR_IDENTIFIER_VALIDATOR)
    timestamp: int = attrs.field(validator=POSITIVE_INTEGER_VALIDATOR)
    # TODO Allow for list of values, to concatenate multiple measurements in one request
    measurement: dict[str, int | float | str | bool | None] = JSON_FIELD
