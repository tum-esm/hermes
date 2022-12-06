from typing import Literal
from pydantic import BaseModel, validator
from .validators import (
    validate_int,
    validate_str,
)


class GeneralConfig(BaseModel):
    station_name: str

    # validators
    _val_station_name = validator("station_name", pre=True, allow_reuse=True)(
        validate_str(min_len=3, max_len=64),
    )


class MQTTConfig(BaseModel):
    url: str
    port: int
    identifier: str
    password: str
    base_topic: str

    # validators
    _val_url = validator("url", pre=True, allow_reuse=True)(
        validate_str(min_len=3, max_len=256),
    )
    _val_port = validator("port", pre=True, allow_reuse=True)(
        validate_int(minimum=0),
    )
    _val_identifier = validator("identifier", pre=True, allow_reuse=True)(
        validate_str(min_len=3, max_len=256),
    )
    _val_password = validator("password", pre=True, allow_reuse=True)(
        validate_str(min_len=8, max_len=256),
    )
    _val_base_topic = validator("base_topic", pre=True, allow_reuse=True)(
        validate_str(min_len=1, max_len=256, regex=r"^(\/[a-z0-9_-]+)*$"),
    )


class AirInletConfig(BaseModel):
    number: Literal[1, 2, 3, 4]
    direction: int

    # validators
    _val_number = validator("number", pre=True, allow_reuse=True)(
        validate_int(allowed=[1, 2, 3, 4])
    )
    _val_direction = validator("direction", pre=True, allow_reuse=True)(
        validate_int(minimum=0, maximum=359)
    )


class ValveConfig(BaseModel):
    air_inlets: list[AirInletConfig]


class Config(BaseModel):
    """The config.json for each sensor"""

    version: Literal["0.1.0"]
    revision: int
    general: GeneralConfig
    mqtt: MQTTConfig
    valves: ValveConfig

    # validators
    _val_version = validator("version", pre=True, allow_reuse=True)(
        validate_str(allowed=["0.1.0"]),
    )
    _val_revision = validator("revision", pre=True, allow_reuse=True)(
        validate_int(minimum=0, maximum=2_147_483_648),
    )
