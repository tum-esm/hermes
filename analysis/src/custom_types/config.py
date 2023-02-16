from pydantic import BaseModel, validator
from .validators import validate_str


class SensorConfig(BaseModel):
    """content of field `config.sensors` in file `config.json`"""

    sensor_name: str
    sensor_identifier: str

    # validators
    _val_sensor_name = validator("sensor_name", pre=True, allow_reuse=True)(
        validate_str(),
    )
    _val_sensor_identifier = validator("sensor_identifier", pre=True, allow_reuse=True)(
        validate_str(),
    )

    class Config:
        extra = "forbid"


class Config(BaseModel):
    """content of file `config.json`"""

    sensors: list[SensorConfig]

    class Config:
        extra = "forbid"
