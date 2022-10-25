from typing import Any, Literal, TypedDict

from .typing_utils import TypingUtils


class _ConfigDictGeneral(TypedDict):
    node_id: str


class ConfigDict(TypedDict):
    """The config.json for each sensor"""

    version: Literal["0.1.0"]
    general: _ConfigDictGeneral


def validate_config_dict(config: Any) -> None:
    """
    Check, whether a given object is a correct ConfigDict
    Raises a ConfigValidationError if the object is invalid.
    This should always be used when loading the object from a
    JSON file!
    """
    TypingUtils.validate_typed_dict(config, "config")
    TypingUtils.parse_assertions(
        [
            lambda: TypingUtils.assert_str_len(config, "general.node_id", 3, 128),
        ],
        "config",
    )
