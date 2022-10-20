import pydantic
from typing import Any, Literal, TypedDict


class ConfigDict(TypedDict):
    """The config.json for each sensor"""

    version: Literal["0.1.0"]


class _ValidationModel(pydantic.BaseModel):
    config: ConfigDict

    class Config:
        extra = "forbid"


class ConfigValidationError(Exception):
    """
    Will be raised in any custom checks on config dicts
    have failed: file-existence, ip-format, min/max-range
    """


def validate_config_dict(config: Any) -> None:
    """
    Check, whether a given object is a correct ConfigDict
    Raises a ConfigValidationError if the object is invalid.
    This should always be used when loading the object from a
    JSON file!
    """
    try:
        _ValidationModel(config=config)
    except pydantic.ValidationError as e:
        pretty_error_messages = []
        for error in e.errors():
            fields = [str(f) for f in error["loc"][1:] if f not in ["__root__"]]
            pretty_error_messages.append(f"{'.'.join(fields)} ({error['msg']})")
        raise ConfigValidationError(
            f"config is invalid: {', '.join(pretty_error_messages)}"
        )
