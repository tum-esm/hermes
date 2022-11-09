import abc
import json

import attrs
import starlette

import app.constants as constants
import app.errors as errors
from app.logs import logger


########################################################################################
# Route validation base classes and functions
########################################################################################


class _RequestQuery:
    pass


class _RequestBody:
    pass


class _Request(abc.ABC):
    """Abstract class for request validation models."""

    @property
    @abc.abstractmethod
    def query(self) -> _RequestQuery:
        pass

    @property
    @abc.abstractmethod
    def body(self) -> _RequestBody:
        pass


async def validate(
    request: starlette.requests.Request,
    schema: type[_Request],
) -> _Request:
    """Validate a starlette request against the given attrs schema."""
    try:
        body = await request.body()
        body = {} if len(body) == 0 else json.loads(body.decode())
        return schema(request.query_params, body)
    except (TypeError, ValueError) as e:
        # TODO Improve log message somehow
        logger.warning(f"[HTTP] InvalidSyntaxError: {e}")
        raise errors.InvalidSyntaxError()


########################################################################################
# Attrs converters
########################################################################################


def _convert_query_string_to_list(string: str) -> list[str]:
    """Convert a comma-separated string to a list of strings."""
    # split(",") returns [""] if string is empty, and we don't want that
    return string.split(",") if string else []


########################################################################################
# Attrs validators
########################################################################################


def _validate_end_greater_equal_start(
    instance: _RequestQuery,
    attribute: attrs.Attribute,
    value: int,
) -> None:
    if instance.start > value:
        raise ValueError("end must be >= start")


SENSOR_IDENTIFIER_VALIDATOR = attrs.validators.and_(
    attrs.validators.instance_of(str),
    attrs.validators.matches_re(constants.Pattern.SENSOR_IDENTIFIER),
)
VALUE_IDENTIFIER_VALIDATOR = attrs.validators.and_(
    attrs.validators.instance_of(str),
    attrs.validators.matches_re(constants.Pattern.VALUE_IDENTIFIER),
)
POSITIVE_INTEGER_VALIDATOR = attrs.validators.and_(
    attrs.validators.instance_of(int),
    attrs.validators.ge(0),
    attrs.validators.lt(constants.Limit.MAXINT4),
)
JSON_VALIDATOR = attrs.validators.and_(
    attrs.validators.instance_of(dict),
    attrs.validators.deep_mapping(
        # TODO Enforce some max number of keys
        mapping_validator=attrs.validators.instance_of(dict),
        # Note that this validator disallows nested JSON
        key_validator=VALUE_IDENTIFIER_VALIDATOR,
        # TODO Validate the values more thoroughly for min and max limits/lengths
        value_validator=attrs.validators.instance_of(int | float | str | bool | None),
    ),
)


########################################################################################
# Attrs fields
########################################################################################

# Maybe we can define these with default converters and validators, and optionally:
# - pass additional converters and validators than run after the default ones
# - pass different default values
# - automatically set converters and validators optional if default=None is set

# Query fields are parsed from strings and are always optional
POSITIVE_INTEGER_QUERY_FIELD = attrs.field(
    default=None,
    converter=attrs.converters.optional(int),
    validator=attrs.validators.optional(POSITIVE_INTEGER_VALIDATOR),
)

# Standard fields are taken as is and are by default required
JSON_FIELD = attrs.field(
    validator=JSON_VALIDATOR,
)


########################################################################################
# Route validation
#
# Guidelines for syntactically correct, but otherwise somehow invalid values:
# - When lists of values are passed, ignore any invalid ones
# - When a single value is passed, raise an error
########################################################################################


@attrs.frozen
class PostSensorsRequestQuery(_RequestQuery):
    pass


@attrs.frozen
class GetSensorsRequestQuery(_RequestQuery):
    sensors: list[str] = attrs.field(
        default="",
        converter=_convert_query_string_to_list,
        validator=attrs.validators.deep_iterable(
            iterable_validator=attrs.validators.instance_of(list),
            member_validator=SENSOR_IDENTIFIER_VALIDATOR,
        ),
    )


@attrs.frozen
class GetMeasurementsRequestQuery(_RequestQuery):
    sensors: list[str] = attrs.field(
        default="",
        converter=_convert_query_string_to_list,
        validator=attrs.validators.deep_iterable(
            iterable_validator=attrs.validators.instance_of(list),
            member_validator=SENSOR_IDENTIFIER_VALIDATOR,
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
    start: int = POSITIVE_INTEGER_QUERY_FIELD
    end: int = attrs.field(
        default=None,
        converter=attrs.converters.optional(int),
        validator=attrs.validators.optional(
            attrs.validators.and_(
                POSITIVE_INTEGER_VALIDATOR,
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
class PostSensorsRequestBody(_RequestBody):
    configuration: dict[str, int | float | str | bool | None] = JSON_FIELD


@attrs.frozen
class GetSensorsRequestBody(_RequestBody):
    pass


@attrs.frozen
class GetMeasurementsRequestBody(_RequestBody):
    pass


# TODO Can we automatically generate these?
@attrs.frozen
class PostSensorsRequest(_Request):
    query: PostSensorsRequestQuery = attrs.field(
        converter=lambda x: PostSensorsRequestQuery(**x),
    )
    body: PostSensorsRequestBody = attrs.field(
        converter=lambda x: PostSensorsRequestBody(**x),
    )


@attrs.frozen
class GetSensorsRequest(_Request):
    query: GetSensorsRequestQuery = attrs.field(
        converter=lambda x: GetSensorsRequestQuery(**x),
    )
    body: GetSensorsRequestBody = attrs.field(
        converter=lambda x: GetSensorsRequestBody(**x),
    )


@attrs.frozen
class GetMeasurementsRequest(_Request):
    query: GetMeasurementsRequestQuery = attrs.field(
        converter=lambda x: GetMeasurementsRequestQuery(**x),
    )
    body: GetMeasurementsRequestBody = attrs.field(
        converter=lambda x: GetMeasurementsRequestBody(**x),
    )


########################################################################################
# MQTT validation
########################################################################################


@attrs.frozen
class Measurement:
    sensor_identifier: str = attrs.field(validator=SENSOR_IDENTIFIER_VALIDATOR)
    timestamp: int = attrs.field(validator=POSITIVE_INTEGER_VALIDATOR)
    values: dict[str, int | float | str | bool | None] = JSON_FIELD
