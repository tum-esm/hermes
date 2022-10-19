import enum

import pydantic

########################################################################################
# Constants
########################################################################################


class Length(int, enum.Enum):
    A = 2**5  # 32
    B = 2**31  # max value signed 32-bit integer + 1


class Pattern(str, enum.Enum):
    NODE_IDENTIFIER = r"^(?!-)(?!.*--)[a-z0-9-]{1,32}(?<!-)$"
    VALUE_IDENTIFIER = r"^(?!_)(?!.*__)[a-z0-9_]{1,32}(?<!_)$"


########################################################################################
# Custom types
########################################################################################


NodeIdentifier = pydantic.constr(regex=Pattern.NODE_IDENTIFIER.value)
ValueIdentifier = pydantic.constr(regex=Pattern.VALUE_IDENTIFIER.value)
Timestamp = pydantic.conint(ge=0, lt=Length.B)


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
    skip: pydantic.conint(ge=0, lt=Length.B) = None
    limit: pydantic.conint(ge=0, lt=Length.B) = None

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
