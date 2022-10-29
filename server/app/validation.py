import enum

import abc
import attrs
import pydantic

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
# Custom types
########################################################################################


SensorIdentifier = pydantic.constr(regex=Pattern.SENSOR_IDENTIFIER.value)
ValueIdentifier = pydantic.constr(regex=Pattern.VALUE_IDENTIFIER.value)
Timestamp = pydantic.conint(ge=0, lt=Limit.MAXINT4)


########################################################################################
# Base model
########################################################################################


class BaseModel(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra["forbid"]


########################################################################################
# Validation models
########################################################################################


class GetMeasurementsRequest(BaseModel):
    sensors: pydantic.conlist(item_type=SensorIdentifier, unique_items=True) = None
    values: pydantic.conlist(item_type=ValueIdentifier, unique_items=True) = None
    start_timestamp: Timestamp = None
    end_timestamp: Timestamp = None
    skip: pydantic.conint(ge=0, lt=Limit.MAXINT4) = None
    limit: pydantic.conint(ge=0, lt=Limit.MAXINT4) = None

    @pydantic.validator("sensors", "values", pre=True)
    def transform_string_to_list(cls, v, values):
        if isinstance(v, str):
            return v.split(",")
        return v

    @pydantic.validator("end_timestamp")
    def validate_end_timestamp(cls, v, values):
        if "start_timestamp" in values and v < values["start_timestamp"]:
            raise ValueError("end_timestamp must be >= start_timestamp")
        return v


def convert_query_string_to_list(string: str) -> list[str]:
    return string.split(",")


TIMESTAMP_VALIDATOR = attrs.validators.and_(
    attrs.validators.instance_of(int),
    attrs.validators.ge(0),
    attrs.validators.lt(Limit.MAXINT4),
)
SENSOR_IDENTIFIER_VALIDATOR = attrs.validators.and_(
    attrs.validators.instance_of(str),
    attrs.validators.matches_re(Pattern.SENSOR_IDENTIFIER),
)
VALUE_IDENTIFIER_VALIDATOR = attrs.validators.and_(
    attrs.validators.instance_of(str),
    attrs.validators.matches_re(Pattern.VALUE_IDENTIFIER),
)


@attrs.frozen
class Measurement:
    sensor_identifier: str = attrs.field(validator=SENSOR_IDENTIFIER_VALIDATOR)
    timestamp: int = attrs.field(validator=TIMESTAMP_VALIDATOR)
    values: dict[str, int | float] = attrs.field(
        validator=attrs.validators.deep_mapping(
            mapping_validator=attrs.validators.instance_of(dict),
            key_validator=VALUE_IDENTIFIER_VALIDATOR,
            # TODO validate the values more thoroughly for min and max limits
            value_validator=attrs.validators.instance_of(int | float),
        )
    )


class _RequestBody:
    pass


class _RequestQuery:
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


@attrs.frozen
class GetSensorsRequestQuery(_RequestQuery):

    # TODO make sensors query parameter optional

    sensors: list[str] = attrs.field(
        converter=convert_query_string_to_list,
        validator=attrs.validators.deep_iterable(
            iterable_validator=attrs.validators.instance_of(list),
            member_validator=SENSOR_IDENTIFIER_VALIDATOR,
        ),
    )


@attrs.frozen
class GetSensorsRequestBody(_RequestBody):
    pass


@attrs.frozen
class GetSensorsRequest(_Request):
    query: GetSensorsRequestQuery = attrs.field(
        converter=lambda x: GetSensorsRequestQuery(**x),
    )
    body: GetSensorsRequestBody = attrs.field(
        converter=lambda x: GetSensorsRequestBody(**x),
    )
