from typing import Literal, TypedDict


class ConfigDict(TypedDict):
    """The config.json for each sensor"""

    version: Literal["0.1.0"]


# TODO: add function to validate a config dict
