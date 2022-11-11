import attrs

import app.validation.constants as constants
from app.validation.fields import (
    JSON_FIELD_VALIDATOR,
    POSITIVE_INTEGER_VALIDATOR,
    SENSOR_IDENTIFIER_VALIDATOR,
    JSONValues,
    _validate_contains_timestamp,
)


@attrs.frozen
class MeasurementsMessage:
    sensor_identifier: str = attrs.field(validator=SENSOR_IDENTIFIER_VALIDATOR)
    measurements: list[dict[str, JSONValues]] = attrs.field(
        validator=attrs.validators.deep_iterable(
            iterable_validator=attrs.validators.and_(
                attrs.validators.instance_of(list),
                attrs.validators.min_length(1),
                attrs.validators.max_length(constants.Limit.MEDIUM - 1),
            ),
            member_validator=attrs.validators.and_(
                JSON_FIELD_VALIDATOR,
                validate_contains_timestamp,
            ),
        )
    )
