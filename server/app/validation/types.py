import pydantic

import app.validation.constants as constants


########################################################################################
# Base model
########################################################################################


class _BaseModel(pydantic.BaseModel):
    class Config:
        extra = pydantic.Extra.forbid
        frozen = True


class _Configuration(pydantic.BaseModel):
    # TODO Validate the values more thoroughly for min and max limits/lengths
    # number of JSON fields or nesting depth could be interesting as well
    # Or, check the actual size of the JSON / length of the JSON string
    class Config:
        frozen = True


########################################################################################
# Types
########################################################################################

Name = pydantic.constr(strict=True, regex=constants.Pattern.NAME.value)
Identifier = pydantic.constr(strict=True, regex=constants.Pattern.IDENTIFIER.value)
Password = pydantic.constr(strict=True, min_length=8, max_length=constants.Limit.MEDIUM)
Revision = pydantic.conint(ge=0, lt=constants.Limit.MAXINT4)

Key = pydantic.constr(strict=True, regex=constants.Pattern.KEY.value)
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

# TODO what are the real min/max values here? How do we handle overflow?
# During validation somehow, or by handling the database error?
# TODO Make strict when pydantic v2 is released
Timestamp = pydantic.confloat(ge=0, lt=constants.Limit.MAXINT4)
