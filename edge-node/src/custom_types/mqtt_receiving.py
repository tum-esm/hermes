import pydantic


class MQTTConfigurationRequestConfig(pydantic.BaseModel):
    version: str = pydantic.Field(..., min_length=5)

    class Config:
        extra = "allow"


class MQTTConfigurationRequest(pydantic.BaseModel):
    """A message sent by the server requesting a station to
    update its configuration. Extra items in this mode are
    allowed for future additions."""

    revision: int = pydantic.Field(..., ge=0)
    configuration: MQTTConfigurationRequestConfig
