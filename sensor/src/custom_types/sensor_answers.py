from typing import Literal, Optional
from pydantic import BaseModel, validator
from pydantic import BaseModel, validator
from .validators import (
    validate_int,
    validate_str,
    validate_float,
    validate_bool,
    validate_list,
)

# validation is only necessary for external sources
# internal source will be covered by mypy


class CO2SensorData(BaseModel):
    raw: float
    compensated: float
    filtered: float


class MainboardSensorData(BaseModel):
    """units: °C for temperature, rH for humidity, hPa for pressure"""

    mainboard_temperature: Optional[float]
    cpu_temperature: Optional[float]
    enclosure_humidity: Optional[float]
    enclosure_pressure: Optional[float]


class WindSensorData(BaseModel):
    direction_min: float
    direction_avg: float
    direction_max: float
    speed_min: float
    speed_avg: float
    speed_max: float
    last_update_time: float


class WindSensorStatus(BaseModel):
    temperature: float
    heating_voltage: float
    supply_voltage: float
    reference_voltage: float
    sensor_id: str
    last_update_time: float


class HeatedEnclosureData(BaseModel):
    target: float
    allowed_deviation: float
    measured: Optional[float]
    heater_is_on: bool
    fan_is_on: bool
    last_update_time: float


class RawHeatedEnclosureData(BaseModel):
    version: str
    target: float
    allowed_deviation: float
    measured: Optional[float]
    heater: Literal["on", "off"]
    fan: Literal["on", "off"]

    # validators
    _val_version = validator("version", pre=True, allow_reuse=True)(
        validate_str(regex=r"^\d+\.\d+\.\d+$"),
    )
    _val_target = validator("target", pre=True, allow_reuse=True)(
        validate_float(),
    )
    _val_allowed_deviation = validator("allowed_deviation", pre=True, allow_reuse=True)(
        validate_float(),
    )
    _val_measured = validator("measured", pre=True, allow_reuse=True)(
        validate_float(nullable=True),
    )
    _val_heater = validator("heater", pre=True, allow_reuse=True)(
        validate_str(allowed=["on", "off"]),
    )
    _val_fan = validator("fan", pre=True, allow_reuse=True)(
        validate_str(allowed=["on", "off"]),
    )

    class Config:
        extra = "forbid"
