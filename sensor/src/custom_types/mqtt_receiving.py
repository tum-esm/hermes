from pydantic import BaseModel, validator
from .validators import validate_int, validate_str


class MQTTConfigurationRequestConfig(BaseModel):
    version: str

    # validators
    _val_version = validator("version", pre=True, allow_reuse=True)(
        validate_str(min_len=5),
    )

    class Config:
        extra = "allow"


class MQTTConfigurationRequest(BaseModel):
    """A message sent by the server requesting a station to
    update its configuration. Extra items in this mode are
    allowed for future additions."""

    revision: int
    configuration: MQTTConfigurationRequestConfig

    # validators
    _val_revision = validator("revision", pre=True, allow_reuse=True)(
        validate_int(minimum=0),
    )
