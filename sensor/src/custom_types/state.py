from typing import Optional

import pydantic


class State(pydantic.BaseModel):
    last_upgrade_time: Optional[float]
    last_calibration_time: Optional[float]
    current_config_revision: int
    offline_since: Optional[float]
    next_calibration_cylinder: int = pydantic.Field(..., ge=0, le=3)
