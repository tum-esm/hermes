from pydantic import BaseModel, validator
from .validators import validate_float


class State(BaseModel):
    last_upgrade_time: float
    last_calibration_time: float

    # validators
    _val_float = validator("*", pre=True, allow_reuse=True)(
        validate_float(),
    )
