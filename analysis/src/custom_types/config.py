from pydantic import BaseModel, validator
from .validators import validate_int, validate_str


class DatabaseConfig(BaseModel):
    """content of field `config.sensors` in file `config.json`"""

    host: str
    port: int
    user: str
    password: str
    database: str

    # validators
    _val_host = validator("host", pre=True, allow_reuse=True)(
        validate_str(),
    )
    _val_port = validator("port", pre=True, allow_reuse=True)(
        validate_int(minimum=0),
    )
    _val_user = validator("user", pre=True, allow_reuse=True)(
        validate_str(),
    )
    _val_password = validator("password", pre=True, allow_reuse=True)(
        validate_str(),
    )
    _val_database = validator("database", pre=True, allow_reuse=True)(
        validate_str(),
    )

    class Config:
        extra = "forbid"


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

    database: DatabaseConfig
    sensors: list[SensorConfig]

    class Config:
        extra = "forbid"
