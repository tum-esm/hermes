import attrs

import app.validation.constants as constants
from app.validation.core import _RequestQuery


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
