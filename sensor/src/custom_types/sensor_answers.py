from typing import Literal, Optional
import pydantic
from .config import CalibrationGasConfig

# validation is only necessary for external sources
# internal source will be covered by mypy


class AirSensorData(pydantic.BaseModel):
    bme280_temperature: Optional[float]
    bme280_humidity: Optional[float]
    bme280_pressure: Optional[float]
    sht45_temperature: Optional[float]
    sht45_humidity: Optional[float]
    chamber_temperature: Optional[float]


class CO2SensorData(pydantic.BaseModel):
    raw: float
    compensated: float
    filtered: float


class CalibrationProcedureData(pydantic.BaseModel):
    gases: list[CalibrationGasConfig]
    readings: list[list[CO2SensorData]]
    timestamps: list[list[float]]


class BME280SensorData(pydantic.BaseModel):
    """units: °C for temperature, rH for humidity, hPa for pressure"""

    temperature: Optional[float]
    humidity: Optional[float]
    pressure: Optional[float]


class SHT45SensorData(pydantic.BaseModel):
    """units: °C for temperature, rH for humidity"""

    temperature: Optional[float]
    humidity: Optional[float]


class SystemData(pydantic.BaseModel):
    """fractional values from 0 to 1"""

    mainboard_temperature: Optional[float]
    cpu_temperature: Optional[float]
    enclosure_humidity: Optional[float]
    enclosure_pressure: Optional[float]
    disk_usage: float
    cpu_usage: float
    memory_usage: float


class WindSensorData(pydantic.BaseModel):
    direction_min: float
    direction_avg: float
    direction_max: float
    speed_min: float
    speed_avg: float
    speed_max: float
    last_update_time: float


class WindSensorStatus(pydantic.BaseModel):
    temperature: float
    heating_voltage: float
    supply_voltage: float
    reference_voltage: float
    sensor_id: str
    last_update_time: float


class HeatedEnclosureData(pydantic.BaseModel):
    target: float
    allowed_deviation: float
    measured: Optional[float]
    heater_is_on: bool
    fan_is_on: bool
    last_update_time: float


class RawHeatedEnclosureData(pydantic.BaseModel):
    version: str = pydantic.Field(..., regex=r"^\d+\.\d+\.\d+(-(alpha|beta|rc)\.\d+)?$")
    target: float
    allowed_deviation: float
    measured: Optional[float]
    heater: Literal["on", "off"]
    fan: Literal["on", "off"]

    class Config:
        extra = "forbid"
