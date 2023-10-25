from typing import Optional
from datetime import datetime
import pydantic


class State(pydantic.BaseModel):
    last_upgrade_time: Optional[float]
    last_calibration_time: Optional[float]
    current_config_revision: int
    offline_since: Optional[float]
