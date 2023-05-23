from typing import Optional
import pydantic


class State(pydantic.BaseModel):
    last_upgrade_time: Optional[float]
    last_calibration_time: Optional[float]
