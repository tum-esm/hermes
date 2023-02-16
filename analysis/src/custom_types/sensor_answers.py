from typing import Literal, Optional
from pydantic import BaseModel, validator
from .validators import validate_int, validate_float

# validation is only necessary for external sources
# internal source will be covered by mypy


class CalibrationGasConfig(BaseModel):
    valve_number: Literal[1, 2, 3, 4]
    concentration: float

    # validators
    _val_valve_number = validator("valve_number", pre=True, allow_reuse=True)(
        validate_int(allowed=[1, 2, 3, 4]),
    )
    _val_concentration = validator("concentration", pre=True, allow_reuse=True)(
        validate_float(minimum=0, maximum=10000),
    )

    class Config:
        extra = "forbid"


class AirSensorData(BaseModel):
    inlet_temperature: Optional[float]
    inlet_humidity: Optional[float]
    chamber_temperature: Optional[float]


class CO2SensorData(BaseModel):
    raw: float
    compensated: float
    filtered: float


class CalibrationProcedureData(BaseModel):
    gases: list[CalibrationGasConfig]
    readings: list[list[CO2SensorData]]


class MainboardSensorData(BaseModel):
    """units: °C for temperature, rH for humidity, hPa for pressure"""

    mainboard_temperature: Optional[float]
    cpu_temperature: Optional[float]
    enclosure_humidity: Optional[float]
    enclosure_pressure: Optional[float]


class SystemData(BaseModel):
    """fractional values from 0 to 1"""

    mainboard_temperature: Optional[float]
    cpu_temperature: Optional[float]
    enclosure_humidity: Optional[float]
    enclosure_pressure: Optional[float]
    disk_usage: float
    cpu_usage: float


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
