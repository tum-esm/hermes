import enum

import attrs
import pydantic

########################################################################################
# Constants
########################################################################################


class Limit(int, enum.Enum):
    MEDIUM = 2**6  # 64
    MAXINT4 = 2**31  # Maximum value signed 32-bit integer + 1


class Pattern(str, enum.Enum):
    NODE_IDENTIFIER = r"^(?!-)(?!.*--)[a-z0-9-]{1,64}(?<!-)$"
    VALUE_IDENTIFIER = r"^(?!_)(?!.*__)[a-z0-9_]{1,64}(?<!_)$"


########################################################################################
# Custom types
########################################################################################


NodeIdentifier = pydantic.constr(regex=Pattern.NODE_IDENTIFIER.value)
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
    nodes: pydantic.conlist(item_type=NodeIdentifier, unique_items=True) = None
    values: pydantic.conlist(item_type=ValueIdentifier, unique_items=True) = None
    start_timestamp: Timestamp = None
    end_timestamp: Timestamp = None
    skip: pydantic.conint(ge=0, lt=Limit.MAXINT4) = None
    limit: pydantic.conint(ge=0, lt=Limit.MAXINT4) = None

    @pydantic.validator("nodes", "values", pre=True)
    def transform_string_to_list(cls, v, values):
        if isinstance(v, str):
            return v.split(",")
        return v

    @pydantic.validator("end_timestamp")
    def validate_end_timestamp(cls, v, values):
        if "start_timestamp" in values and v < values["start_timestamp"]:
            raise ValueError("end_timestamp must be >= start_timestamp")
        return v


TIMESTAMP_VALIDATOR = [
    attrs.validators.instance_of(int),
    attrs.validators.ge(0),
    attrs.validators.lt(Limit.MAXINT4),
]
NODE_IDENTIFIER_VALIDATOR = [
    attrs.validators.instance_of(str),
    attrs.validators.matches_re(Pattern.NODE_IDENTIFIER),
]
VALUE_IDENTIFIER_VALIDATOR = [
    attrs.validators.instance_of(str),
    attrs.validators.matches_re(Pattern.VALUE_IDENTIFIER),
]


@attrs.frozen
class Measurement:
    node_identifier: str = attrs.field(validator=NODE_IDENTIFIER_VALIDATOR)
    timestamp: int = attrs.field(validator=TIMESTAMP_VALIDATOR)
    values: dict[str, int | float] = attrs.field(
        validator=attrs.validators.deep_mapping(
            mapping_validator=attrs.validators.instance_of(dict),
            key_validator=attrs.validators.and_(*VALUE_IDENTIFIER_VALIDATOR),
            value_validator=attrs.validators.instance_of(int | float),
        )
    )
