from pydantic import BaseModel, validator
from .validators import validate_int, validate_str


class DatabaseConfig(BaseModel):
    """content of field `config.sensors` in file `config.json`"""

    host: str
    port: int
    user: str
    password: str
    db_name: str

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
    _val_db_name = validator("db_name", pre=True, allow_reuse=True)(
        validate_str(),
    )

    class Config:
        extra = "forbid"


class Config(BaseModel):
    """content of file `config.json`"""

    database: DatabaseConfig

    class Config:
        extra = "forbid"
