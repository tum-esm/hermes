import abc
import enum
import json

import attrs
import starlette

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
# Constants
########################################################################################


class Limit(int, enum.Enum):
    MEDIUM = 2**6  # 64
    MAXINT4 = 2**31  # Maximum value signed 32-bit integer + 1


class Pattern(str, enum.Enum):
    SENSOR_IDENTIFIER = r"^(?!-)(?!.*--)[a-z0-9-]{1,64}(?<!-)$"
    VALUE_IDENTIFIER = r"^(?!_)(?!.*__)[a-z0-9_]{1,64}(?<!_)$"


########################################################################################
# Attrs converters
########################################################################################


def _convert_query_string_to_list(string: str) -> list[str]:
    # split(",") returns [""] if string is empty, and we don't want that
    return string.split(",") if string else []


########################################################################################
# Attrs validators
########################################################################################


def _validate_end_timestamp_greater_equal_start_timestamp(
    instance: _RequestQuery,
    attribute: attrs.Attribute,
    value: int,
) -> None:
    if instance.start_timestamp > value:
        raise ValueError("end_timestamp must be >= start_timestamp")


SENSOR_IDENTIFIER_VALIDATOR = attrs.validators.and_(
    attrs.validators.instance_of(str),
    attrs.validators.matches_re(Pattern.SENSOR_IDENTIFIER),
)
VALUE_IDENTIFIER_VALIDATOR = attrs.validators.and_(
    attrs.validators.instance_of(str),
    attrs.validators.matches_re(Pattern.VALUE_IDENTIFIER),
)
POSITIVE_INTEGER_VALIDATOR = attrs.validators.and_(
    attrs.validators.instance_of(int),
    attrs.validators.ge(0),
    attrs.validators.lt(Limit.MAXINT4),
)


########################################################################################
# Attrs fields
########################################################################################

# We could define these with default converters and validators, and optionally
# pass additional converters and validators than run after the default ones.

POSITIVE_INTEGER_QUERY_FIELD = attrs.field(
    default=None,
    converter=attrs.converters.optional(int),
    validator=attrs.validators.optional(
        attrs.validators.and_(POSITIVE_INTEGER_VALIDATOR)
    ),
)


########################################################################################
# Route validation
########################################################################################


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
    start_timestamp: int = POSITIVE_INTEGER_QUERY_FIELD
    end_timestamp: int = attrs.field(
        default=None,
        converter=attrs.converters.optional(int),
        validator=attrs.validators.optional(
            attrs.validators.and_(
                POSITIVE_INTEGER_VALIDATOR,
                _validate_end_timestamp_greater_equal_start_timestamp,
            )
        ),
    )
    skip: int = POSITIVE_INTEGER_QUERY_FIELD
    limit: int = POSITIVE_INTEGER_QUERY_FIELD


@attrs.frozen
class GetSensorsRequestBody(_RequestBody):
    pass


@attrs.frozen
class GetMeasurementsRequestBody(_RequestBody):
    pass


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
    values: dict[str, int | float] = attrs.field(
        validator=attrs.validators.deep_mapping(
            mapping_validator=attrs.validators.instance_of(dict),
            key_validator=VALUE_IDENTIFIER_VALIDATOR,
            # TODO validate the values more thoroughly for min and max limits
            value_validator=attrs.validators.instance_of(int | float),
        )
    )
