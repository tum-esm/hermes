import pydantic

import app.validation.constants as constants


########################################################################################
# Base model
########################################################################################


class Model(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(strict=True, frozen=True, extra="forbid")


class Configuration(Model, extra="allow"):
    # TODO Validate the values more thoroughly for min and max limits/lengths
    # number of JSON fields or nesting depth could be interesting as well
    # Or, check the actual size of the JSON / length of the JSON string
    pass


########################################################################################
# Types
########################################################################################

Name = pydantic.constr(pattern=constants.Pattern.NAME.value)
Identifier = pydantic.constr(pattern=constants.Pattern.IDENTIFIER.value)
Password = pydantic.constr(min_length=8, max_length=constants.Limit.MEDIUM)

# TODO what are the real min/max values here? How do we handle overflow?
# During validation somehow, or by handling the database error?
Revision = pydantic.conint(ge=0, lt=constants.Limit.MAXINT4)
Timestamp = pydantic.confloat(ge=0, lt=constants.Limit.MAXINT4)

Key = pydantic.constr(pattern=constants.Pattern.KEY.value)
# TODO Validate the values more thoroughly for min and max limits/lengths
# number of JSON fields or nesting depth could be interesting as well
# Or, check the actual size of the JSON / length of the JSON string
Value = (
    None
    | pydantic.StrictBool
    | pydantic.StrictInt
    | pydantic.StrictFloat
    | pydantic.StrictStr
    | list
    | dict
)
Measurement = dict[Key, Value]
