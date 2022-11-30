import attrs

import app.validation.constants as constants
from app.validation.core import _Request, _RequestBody, _RequestPath, _RequestQuery
from app.validation.fields import (
    JSON_FIELD,
    POSITIVE_FLOAT_QUERY_FIELD,
    POSITIVE_FLOAT_VALIDATOR,
    POSITIVE_INTEGER_VALIDATOR,
    SENSOR_NAME_FIELD,
    SENSOR_NAME_VALIDATOR,
    VALUE_IDENTIFIER_VALIDATOR,
    _convert_query_string_to_list,
    _validate_end_greater_equal_start,
)


# Guidelines for syntactically correct, but otherwise somehow invalid values:
# - When lists of values are passed, ignore any invalid ones
# - When a single value is passed, raise an error


@attrs.frozen
class _PostSensorsRequestPath(_RequestPath):
    pass


@attrs.frozen
class _PutSensorsRequestPath(_RequestPath):
    sensor_name: str = SENSOR_NAME_FIELD


@attrs.frozen
class _GetSensorsRequestPath(_RequestPath):
    pass


@attrs.frozen
class _GetMeasurementsRequestPath(_RequestPath):
    pass


@attrs.frozen
class _PostSensorsRequestQuery(_RequestQuery):
    pass


@attrs.frozen
class _PutSensorsRequestQuery(_RequestQuery):
    pass


@attrs.frozen
class _GetSensorsRequestQuery(_RequestQuery):
    sensors: list[str] = attrs.field(
        default="",
        converter=_convert_query_string_to_list,
        validator=attrs.validators.deep_iterable(
            iterable_validator=attrs.validators.instance_of(list),
            member_validator=SENSOR_NAME_VALIDATOR,
        ),
    )


@attrs.frozen
class _GetMeasurementsRequestQuery(_RequestQuery):
    sensors: list[str] = attrs.field(
        default="",
        converter=_convert_query_string_to_list,
        validator=attrs.validators.deep_iterable(
            iterable_validator=attrs.validators.instance_of(list),
            member_validator=SENSOR_NAME_VALIDATOR,
        ),
    )
    values: list[str] = attrs.field(
        default="",
        converter=_convert_query_string_to_list,
        validator=attrs.validators.deep_iterable(
            iterable_validator=attrs.validators.instance_of(list),
            member_validator=VALUE_IDENTIFIER_VALIDATOR,
        ),
    )
    start: int = POSITIVE_FLOAT_QUERY_FIELD
    end: int = attrs.field(
        default=None,
        converter=attrs.converters.optional(int),
        validator=attrs.validators.optional(
            attrs.validators.and_(
                POSITIVE_FLOAT_VALIDATOR,
                _validate_end_greater_equal_start,
            )
        ),
    )
    skip: int = attrs.field(
        default=0,
        converter=int,
        validator=POSITIVE_INTEGER_VALIDATOR,
    )
    limit: int = attrs.field(
        default=constants.Limit.MEDIUM,
        converter=int,
        validator=attrs.validators.and_(
            POSITIVE_INTEGER_VALIDATOR,
            attrs.validators.le(constants.Limit.LARGE),
        ),
    )


@attrs.frozen
class _PostSensorsRequestBody(_RequestBody):
    sensor_name: str = SENSOR_NAME_FIELD
    configuration: dict[str, int | float | str | bool | None] = JSON_FIELD


@attrs.frozen
class _PutSensorsRequestBody(_RequestBody):
    sensor_name: str = SENSOR_NAME_FIELD
    configuration: dict[str, int | float | str | bool | None] = JSON_FIELD


@attrs.frozen
class _GetSensorsRequestBody(_RequestBody):
    pass


@attrs.frozen
class _GetMeasurementsRequestBody(_RequestBody):
    pass


# TODO Can we generate these automatically?
@attrs.frozen
class PostSensorsRequest(_Request):
    path: _PostSensorsRequestPath = attrs.field(
        converter=lambda x: _PostSensorsRequestPath(**x),
    )
    query: _PostSensorsRequestQuery = attrs.field(
        converter=lambda x: _PostSensorsRequestQuery(**x),
    )
    body: _PostSensorsRequestBody = attrs.field(
        converter=lambda x: _PostSensorsRequestBody(**x),
    )


@attrs.frozen
class PutSensorsRequest(_Request):
    path: _PutSensorsRequestPath = attrs.field(
        converter=lambda x: _PutSensorsRequestPath(**x),
    )
    query: _PutSensorsRequestQuery = attrs.field(
        converter=lambda x: _PutSensorsRequestQuery(**x),
    )
    body: _PutSensorsRequestBody = attrs.field(
        converter=lambda x: _PutSensorsRequestBody(**x),
    )


@attrs.frozen
class GetSensorsRequest(_Request):
    path: _GetSensorsRequestPath = attrs.field(
        converter=lambda x: _GetSensorsRequestPath(**x),
    )
    query: _GetSensorsRequestQuery = attrs.field(
        converter=lambda x: _GetSensorsRequestQuery(**x),
    )
    body: _GetSensorsRequestBody = attrs.field(
        converter=lambda x: _GetSensorsRequestBody(**x),
    )


@attrs.frozen
class GetMeasurementsRequest(_Request):
    path: _GetMeasurementsRequestPath = attrs.field(
        converter=lambda x: _GetMeasurementsRequestPath(**x),
    )
    query: _GetMeasurementsRequestQuery = attrs.field(
        converter=lambda x: _GetMeasurementsRequestQuery(**x),
    )
    body: _GetMeasurementsRequestBody = attrs.field(
        converter=lambda x: _GetMeasurementsRequestBody(**x),
    )
