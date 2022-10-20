import pydantic
from typing import Any, Callable, Literal, TypedDict


class ConfigDict(TypedDict):
    """The config.json for each sensor"""

    version: Literal["0.1.0"]
    node_id: str


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

    validated_config: ConfigDict = config

    def get_nested_dict_property(property_path: str) -> Any:
        prop = validated_config
        for key in property_path.split("."):
            prop = prop[key]  # type: ignore
        return prop

    def assert_str_len(property_path: str, min_len: int, max_len: int) -> None:
        prop: str = get_nested_dict_property(property_path)
        error_message = (
            f"length of config.{property_path} must be in range [{min_len}, {max_len}]"
        )
        assert len(prop) >= min_len, error_message
        assert len(prop) <= max_len, error_message

    assertions: list[Callable[[], None]] = [
        lambda: assert_str_len("node_id", 3, 128),
    ]

    pretty_error_messages = []

    for assertion in assertions:
        try:
            assertion()
        except AssertionError as a:
            pretty_error_messages.append(a.args[0])
        except (TypeError, KeyError):
            # Will be ignored because the structure is already
            # validated. Occurs when property is missing
            pass

    if len(pretty_error_messages) > 0:
        raise ConfigValidationError(
            f"config is invalid: {', '.join(pretty_error_messages)}"
        )
